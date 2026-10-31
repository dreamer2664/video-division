#!/usr/bin/env bash
# pixel v01 — reproduce video.mp4 from this repo alone.
# Needs: python3 + Pillow + numpy, ffmpeg/ffprobe with libx264.
# If ffmpeg is absent, bootstraps the John Van Sickle static release build into work/tools
# (functional check for libx264; reference build used for the shipped file: ffmpeg 7.0.2,
# tarball sha256 abda8d77ce8309141f83ab8edf0596834087c52467f6badf376a6a2a4c87cf67 — see QA.md).
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/bin:$PATH"

command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
python3 -c "import PIL, numpy" 2>/dev/null || python3 -m pip install --user pillow numpy

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo "ffmpeg missing — bootstrapping static build into work/tools ..."
  mkdir -p work/tools && cd work/tools
  curl -sL -o ffmpeg-static.tar.xz https://www.johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  tar -xf ffmpeg-static.tar.xz
  FFDIR=$(find . -maxdepth 1 -type d -name 'ffmpeg-*-amd64-static' | head -1)
  mkdir -p "$HOME/bin" && cp "$FFDIR/ffmpeg" "$FFDIR/ffprobe" "$HOME/bin/" && chmod +x "$HOME/bin/ffmpeg" "$HOME/bin/ffprobe"
  cd ../..
fi
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264 || { echo "ERROR: ffmpeg lacks libx264"; exit 1; }
ffmpeg -version | head -1

# 1. frames + audio + captions (deterministic; asserts every fact on screen at startup)
python3 assets/generate.py

# 2. loudness: measure, then encode with measured two-pass loudnorm (-16 LUFS, TP -1.5)
MEAS=$(ffmpeg -v info -i work/audio.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | awk '/^\{/{f=1} f{print} /^\}/{if(f) exit}')
echo "loudnorm measurement: $MEAS"
LN=$(MEAS="$MEAS" python3 -c "
import json, os
m = json.loads(os.environ['MEAS'])
linear = 'true' if m.get('normalization_type') == 'linear' else 'false'
print(f\"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_LRA={m['input_lra']}:measured_TP={m['input_tp']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear={linear}\")
")
echo "applying: $LN"

# 3. encode: H.264 yuv420p 1080p30 + AAC 48kHz stereo, faststart
ffmpeg -y -v error -framerate 30 -i work/frames/f%04d.png -i work/audio.wav \
  -af "$LN,aresample=48000" -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 30 -vsync cfr \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -t 60 -movflags +faststart \
  -metadata title="A Million Is Not a Billion — pixel v01 (Team A)" video.mp4

# 4. stills: hook / million complete / true-scale bars
mkdir -p stills
ffmpeg -y -v error -ss 4.0  -i video.mp4 -frames:v 1 stills/01.png
ffmpeg -y -v error -ss 20.5 -i video.mp4 -frames:v 1 stills/02.png
ffmpeg -y -v error -ss 49.6 -i video.mp4 -frames:v 1 stills/03.png

echo "=== done ==="
ls -lh video.mp4 captions.srt stills/
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4
