#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
FFMPEG="${FFMPEG:-$(command -v ffmpeg || true)}"
if [[ -z "$FFMPEG" || ! -x "$FFMPEG" ]]; then echo 'FFmpeg executable required; set FFMPEG=/path/to/ffmpeg.' >&2; exit 1; fi
PYTHON="${PYTHON:-python3}"
WORK="${WORKDIR:-/tmp/cut-v08-build}"
mkdir -p "$WORK"
if [[ ! -s assets/narration.wav ]]; then
  "$PYTHON" project/voice.py --ffmpeg "$FFMPEG" --work "$WORK/voice-clips" --out assets/narration.wav --csv project/voice_cues.csv
fi
"$PYTHON" project/sound.py --out "$WORK/score.wav"
"$PYTHON" project/render.py --ffmpeg "$FFMPEG" --out "$WORK/picture.mp4" --cues project/voice_cues.csv
"$FFMPEG" -hide_banner -y -i "$WORK/picture.mp4" -i assets/narration.wav -i "$WORK/score.wav" \
  -filter_complex '[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[voice];[2:a]volume=1.5[bed];[voice][bed]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=7:linear=true,volume=-0.45dB[mix]' \
  -map 0:v:0 -map '[mix]' -t 60 -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart video.mp4
"$FFMPEG" -hide_banner -y -i video.mp4 \
  -filter_complex '[0:v]split=2[fg][bg];[bg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=36:12,eq=brightness=-0.18:saturation=0.72[background];[fg]scale=608:1080:flags=lanczos[portrait];[background][portrait]overlay=(W-w)/2:0:shortest=1[outv]' \
  -map '[outv]' -map 0:a:0 -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30 -c:a copy -movflags +faststart video-landscape.mp4
mkdir -p stills
for entry in '2.4 01' '21.6 02' '45.6 03'; do
  read -r time name <<<"$entry"
  "$FFMPEG" -hide_banner -y -loglevel error -ss "$time" -i video.mp4 -frames:v 1 "stills/$name.png"
done
