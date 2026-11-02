#!/usr/bin/env bash
# render.sh — v06 "IT ANSWERED". Builds the vertical master (1080x1920) and the landscape
# derivative (1920x1080) from the repo alone.
#
# Requires: python3 + Pillow + numpy, ffmpeg with libx264 + loudnorm, edge-tts (network).
# Intermediates go to assets/work/ (gitignored); final media goes to this folder.
set -euo pipefail
cd "$(dirname "$0")"
DIR="$PWD"
WORK="$DIR/assets/work"
export PATH="$HOME/bin:$PATH"

command -v python3 >/dev/null || { echo "ERROR: python3 missing"; exit 1; }
python3 -c "import PIL, numpy" 2>/dev/null || python3 -m pip install --quiet pillow numpy
command -v edge-tts >/dev/null || python3 -m pip install --quiet edge-tts

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  echo "ffmpeg missing — bootstrapping static build"
  mkdir -p "$WORK/tools" && cd "$WORK/tools"
  curl -sL -o ffmpeg-static.tar.xz https://www.johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
  tar -xf ffmpeg-static.tar.xz
  FFDIR=$(find . -maxdepth 1 -type d -name 'ffmpeg-*-amd64-static' | head -1)
  mkdir -p "$HOME/bin" && cp "$FFDIR/ffmpeg" "$FFDIR/ffprobe" "$HOME/bin/" && chmod +x "$HOME/bin/ffmpeg" "$HOME/bin/ffprobe"
  cd "$DIR"
fi

# Capture first, then test: `ffmpeg ... | grep -q` under `set -e -o pipefail` dies with 141
# (SIGPIPE) the moment grep matches, reporting a missing filter on a build that has it.
ENCODERS=$(ffmpeg -hide_banner -encoders 2>/dev/null)
grep -q libx264 <<<"$ENCODERS" || { echo "ERROR: ffmpeg lacks libx264"; exit 1; }
FILTERS=$(ffmpeg -hide_banner -filters 2>/dev/null)
grep -q loudnorm <<<"$FILTERS" || { echo "ERROR: no loudnorm"; exit 1; }
ffmpeg -version | head -1

mkdir -p "$WORK"

echo "== narration =="
python3 assets/voice.py

echo "== frames + mix =="
python3 assets/generate.py

echo "== loudnorm measure =="
# TP target is -2.5, not -1.5: the two-pass prediction was met exactly and the delivered file
# still measured -0.1 dBTP after AAC encoding. The extra headroom absorbs the codec overshoot;
# the result is re-measured on the delivered file rather than trusted.
MEAS=$(ffmpeg -v info -i "$WORK/mix.wav" -af loudnorm=I=-16:TP=-2.5:LRA=11:print_format=json -f null - 2>&1 \
       | awk '/^\{/{f=1} f{print} /^\}/{if(f) exit}')
echo "$MEAS"
get() { python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d['$1'])" "$MEAS"; }
I=$(get input_i); TP=$(get input_tp); LRA=$(get input_lra); TH=$(get input_thresh); OFF=$(get target_offset)
LIN=$(python3 -c "import json,sys; print('true' if json.loads(sys.argv[1])['normalization_type']=='linear' else 'false')" "$MEAS")
echo "applying: I=-16 TP=-2.5 LRA=11 measured_I=$I measured_TP=$TP measured_LRA=$LRA thresh=$TH offset=$OFF linear=$LIN"

LN="loudnorm=I=-16:TP=-2.5:LRA=11:measured_I=$I:measured_LRA=$LRA:measured_TP=$TP:measured_thresh=$TH:offset=$OFF:linear=$LIN"

echo "== vertical master =="
ffmpeg -y -v error -framerate 30 -i "$WORK/frames/f%04d.png" -i "$WORK/mix.wav" \
  -af "$LN,aresample=48000" \
  -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 -vsync cfr \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -t 60 -movflags +faststart \
  -metadata title="IT ANSWERED — pixel v06 (Team A)" \
  "$DIR/video.mp4"

echo "== landscape derivative =="
ffmpeg -y -v error -i "$DIR/video.mp4" -filter_complex \
"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=28,eq=brightness=-0.12[bg];\
 [0:v]scale=-2:1080[fg];\
 [bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]" \
  -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 \
  -c:a copy -t 60 -movflags +faststart \
  -metadata title="IT ANSWERED — pixel v06 (Team A) — landscape derivative" \
  "$DIR/video-landscape.mp4"

echo "== stills =="
mkdir -p "$DIR/stills"
ffmpeg -y -v error -ss 2.0  -i "$DIR/video.mp4" -frames:v 1 "$DIR/stills/01.png"
ffmpeg -y -v error -ss 11.0 -i "$DIR/video.mp4" -frames:v 1 "$DIR/stills/02.png"
ffmpeg -y -v error -ss 48.0 -i "$DIR/video.mp4" -frames:v 1 "$DIR/stills/03.png"

echo "== done =="
ls -l "$DIR/video.mp4" "$DIR/video-landscape.mp4" "$DIR/captions.srt" "$DIR"/stills/*.png
for f in video.mp4 video-landscape.mp4; do
  echo "--- $f"
  ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels \
    -of default=noprint_wrappers=1 "$DIR/$f"
done
