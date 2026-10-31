#!/usr/bin/env bash
# Reproducible end-to-end build for KELVIN (videos/team-b/grade-v04/video.mp4)
# Runs within <= 700 MiB peak RSS on a 2 GB Debian 13 sandbox.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-/tmp/grade_v04_build}"

echo "=== [grade-v04] Checking system dependencies ==="
MISSING=()
for bin in ffmpeg ffprobe python3; do
  command -v "$bin" >/dev/null 2>&1 || MISSING+=("$bin")
done
if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "Installing required Debian packages..."
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg fonts-ebgaramond fonts-inter python3-numpy python3-pil python3-scipy
fi

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/overlays" "${BUILD_DIR}/shots" "${BUILD_DIR}/reels"

echo "=== [1/6] Generating 33x33x33 .cube 3D colour grading LUTs ==="
python3 "${SCRIPT_DIR}/generate_luts.py"

echo "=== [2/6] Generating 1080p ASS high-contrast typography & captions ==="
python3 "${SCRIPT_DIR}/generate_ass.py"
cp -f "${ROOT_DIR}/assets/captions.srt" "${ROOT_DIR}/captions.srt"

echo "=== [3/6] Exporting companion MLT XML NLE timeline (kelvin-v04.mlt) ==="
python3 "${SCRIPT_DIR}/export_mlt.py"

echo "=== [4/6] Synthesizing slow-motion optical overlays (rain, mist, halation, water shimmer) ==="
python3 "${SCRIPT_DIR}/generate_overlays.py" "${BUILD_DIR}/overlays"

echo "=== [5/6] Synthesizing & two-pass EBU R128 mastering 48kHz stereo sound design ==="
python3 "${SCRIPT_DIR}/build_audio.py" "${BUILD_DIR}/audio_master_48k.wav"

echo "=== [6/6] Grading plates, animating camera & slow-mo layers, burning captions, muxing MP4 ==="
python3 "${SCRIPT_DIR}/grade_and_assemble.py" "${BUILD_DIR}"

echo "=== Extracting verification stills (stills/01.png, 02.png, 03.png) ==="
mkdir -p "${ROOT_DIR}/stills"
ffmpeg -y -hide_banner -loglevel error -ss 00:00:05.50 -i "${ROOT_DIR}/video.mp4" -frames:v 1 "${ROOT_DIR}/stills/01.png"
ffmpeg -y -hide_banner -loglevel error -ss 00:00:15.00 -i "${ROOT_DIR}/video.mp4" -frames:v 1 "${ROOT_DIR}/stills/02.png"
ffmpeg -y -hide_banner -loglevel error -ss 00:00:36.50 -i "${ROOT_DIR}/video.mp4" -frames:v 1 "${ROOT_DIR}/stills/03.png"
ffmpeg -y -hide_banner -loglevel error -ss 00:00:57.50 -i "${ROOT_DIR}/video.mp4" -frames:v 1 "${ROOT_DIR}/stills/04.png"

rm -rf "${BUILD_DIR}"
echo "=== [grade-v04] Render complete: ${ROOT_DIR}/video.mp4 ==="
