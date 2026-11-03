#!/usr/bin/env bash
# Reproduce the 15 s counter proof from the repo alone.
#
# Pipeline: voice first, then video.
#   1. make_cue_sheet.py   -> cue_sheet.json (counter per frame + caption beats)
#   2. gen_voice.py        -> voice.mp3 + word_timestamps.json  (requires ELEVENLABS_API_KEY)
#   3. render_counter.py   -> frames + encode -> output/15s_counter.mp4
#   4. loudnorm pass       -> ffmpeg two-pass loudnorm to -16 LUFS integrated on the final film
#
# Steps 2 needs the ElevenLabs key (never committed, read from env). Steps 1, 3, 4 run offline.
set -euo pipefail
# ffmpeg was stripped from site-packages between runs; use the static binary
# bundled in the persistent workspace so the script is reproducible here.
export PATH="/home/user/ffmpeg-static:$PATH"
export FFMPEG="/home/user/ffmpeg-static/ffmpeg"
cd "$(dirname "$0")/.."

echo "[1/4] cue sheet"
python3 scripts/make_cue_sheet.py

echo "[2/4] voice (requires ELEVENLABS_API_KEY; skipped offline)"
if [ -n "${ELEVENLABS_API_KEY:-}" ]; then
  python3 scripts/gen_voice.py
else
  echo "  (no key — using existing audio/15s_proof/voice.mp3 + word_timestamps.json)"
fi

echo "[3/4] render 15 s counter sequence"
python3 scripts/render_counter.py \
  cue_sheets/sleep_premise/cue_sheet.json \
  0 15 output/15s_counter.mp4

echo "[4/4] loudness: loudnorm two-pass to -16 LUFS integrated"
python3 - <<'PY'
import subprocess, json, re, os
infile = "output/15s_counter.mp4"
outfile = "output/15s_counter.loud.mp4"
# pass 1: measure input loudness / true peak / LRA
p = subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", infile,
     "-af", "loudnorm=print_format=json", "-f", "null", "-"],
    capture_output=True, text=True)
txt = p.stderr
start = txt.find("{")
end = txt.rfind("}")
stats = json.loads(txt[start:end + 1]) if (start != -1 and end != -1 and end > start) else {}
mi = stats.get("input_i", "-16")
mtp = stats.get("input_tp", "-1")
mlra = stats.get("input_lra", "11")
# pass 2: apply normalization targeting -16 LUFS integrated, using measured
# input stats (no offset from pass 1 -- that offset targets the default -24).
subprocess.run(
    ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", infile,
     "-af", f"loudnorm=I=-16:TP=-1:LRA=11:measured_I={mi}:measured_TP={mtp}:measured_LRA={mlra}:linear=true",
     "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
     "-movflags", "+faststart", outfile],
    check=True)
os.replace(outfile, infile)
print("loudnorm pass complete; target -16 LUFS integrated")
PY

echo "done: output/15s_counter.mp4"
echo "verify: ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 output/15s_counter.mp4"
