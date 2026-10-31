#!/usr/bin/env bash
# Rebuild video.mp4 from only the bundled assets. Output path can be overridden
# with OUTPUT=/path/to/file.mp4 to test reproducibility without clobbering.
set -euo pipefail
cd "$(dirname "$0")"
for cmd in python3 ffmpeg; do command -v "$cmd" >/dev/null || { echo "Missing required program: $cmd" >&2; exit 1; }; done
python3 -c 'import PIL, numpy' || { echo 'Install dependencies in requirements.txt first.' >&2; exit 1; }
ffmpeg -hide_banner -encoders 2>/dev/null | grep 'libx264' >/dev/null || { echo 'FFmpeg requires libx264.' >&2; exit 1; }
OUT="${OUTPUT:-video.mp4}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$(dirname "$OUT")"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/reel-v02.XXXXXXXX")"
trap 'rm -f "$TMP/score.wav" "$TMP/loudnorm.log"; rmdir "$TMP" 2>/dev/null || true' EXIT
export LC_ALL=C PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1
printf '%s\n' '1/3 Synthesizing original stereo soundtrack...'
python3 assets/score.py "$TMP/score.wav"
printf '%s\n' '2/3 Measuring soundtrack for two-pass loudness normalization...'
ffmpeg -hide_banner -nostats -i "$TMP/score.wav" -af 'loudnorm=I=-16:TP=-2:LRA=11:print_format=json' -f null - 2>"$TMP/loudnorm.log"
FILTER="$(python3 - "$TMP/loudnorm.log" <<'PY'
import json,re,sys
s=open(sys.argv[1], encoding='utf8').read()
obj=json.loads(re.findall(r'\{\s*"input_i".*?\}',s,re.S)[-1])
print('loudnorm=I=-16:TP=-2:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true,aresample=48000'.format(**obj))
PY
)"
printf '%s\n' '3/3 Drawing 1800 frames and encoding H.264/AAC...'
python3 assets/visuals.py | ffmpeg -hide_banner -loglevel warning -y \
  -f rawvideo -pixel_format rgb24 -video_size 1920x1080 -framerate 30 -i pipe:0 \
  -i "$TMP/score.wav" -map 0:v:0 -map 1:a:0 -af "$FILTER" \
  -frames:v 1800 -c:v libx264 -preset veryfast -b:v 4M -maxrate 6M -bufsize 8M -pix_fmt yuv420p \
  -x264-params 'threads=2:lookahead_threads=1' -g 60 -r 30 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart \
  -map_metadata -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact \
  -video_track_timescale 30000 "$OUT"
printf 'Rendered: %s\n' "$OUT"
