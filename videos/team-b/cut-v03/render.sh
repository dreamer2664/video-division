#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo 'Install FFmpeg with libx264 support first.' >&2; exit 1; }
python3 -c 'import cv2,numpy,PIL' || { echo 'Install Python packages: opencv-python-headless numpy Pillow' >&2; exit 1; }
cd project
python3 sound.py
python3 render.py "$(command -v ffmpeg)"
cd ..
ffmpeg -hide_banner -y -i project/picture.mp4 -i assets/original-score.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -af 'volume=9.1dB' -movflags +faststart -shortest video.mp4
mkdir -p stills
ffmpeg -hide_banner -y -loglevel error -ss 2.3 -i video.mp4 -frames:v 1 stills/01.png
ffmpeg -hide_banner -y -loglevel error -ss 25.3 -i video.mp4 -frames:v 1 stills/02.png
ffmpeg -hide_banner -y -loglevel error -ss 45.3 -i video.mp4 -frames:v 1 stills/03.png
