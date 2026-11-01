#!/usr/bin/env bash
# Reproduce the 15 s counter proof from the repo alone.
#
# Pipeline: voice first, then video.
#   1. make_cue_sheet.py   -> cue_sheet.json (counter per frame + caption beats)
#   2. gen_voice.py        -> voice.mp3 + word_timestamps.json  (requires ELEVENLABS_API_KEY)
#   3. render_counter.py   -> frames + encode -> output/15s_counter.mp4
#
# Steps 2 needs the ElevenLabs key (never committed, read from env). Steps 1 and 3 run offline.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/3] cue sheet"
python3 scripts/make_cue_sheet.py

echo "[2/3] voice (requires ELEVENLABS_API_KEY; skipped offline)"
if [ -n "${ELEVENLABS_API_KEY:-}" ]; then
  python3 scripts/gen_voice.py
else
  echo "  (no key — using existing audio/15s_proof/voice.mp3 + word_timestamps.json)"
fi

echo "[3/3] render 15 s counter sequence"
python3 scripts/render_counter.py \
  cue_sheets/sleep_premise/cue_sheet.json \
  0 15 output/15s_counter.mp4

echo "done: output/15s_counter.mp4"
echo "verify: ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 output/15s_counter.mp4"
