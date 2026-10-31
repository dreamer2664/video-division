#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${FFMPEG:=ffmpeg}"
export FFMPEG
export PYTHONPATH="$PWD/.deps${PYTHONPATH:+:$PYTHONPATH}"
python3 project/voice.py
python3 project/sound.py
python3 project/render.py
