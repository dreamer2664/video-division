#!/usr/bin/env bash
# render.sh — v07 "IT ANSWERED — NIGHT TWO"
#   ./render.sh            full render: narration -> frames -> vertical master -> landscape -> stills
#   ./render.sh frames     frames only (assumes narration already built)
#   ./render.sh mux        re-encode from existing frames
#
# Toolchain is pinned: FFmpeg 7.0.2 static (sha256 abda8d77…) built by hand into ~/bin.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/bin:$PATH"

mkdir -p assets/work/frames stills

mode="${1:-all}"

if [ "$mode" = "all" ]; then
  ( cd assets && python3 voice.py )
  ( cd assets && python3 generate.py )
fi

if [ "$mode" = "frames" ]; then
  ( cd assets && python3 generate.py )
fi

# ---- loudness: measured static gain + peak limiter, verified on the ENCODED file ----
# v06 taught this the hard way: two-pass loudnorm fell back to dynamic mode and missed by 0.69 dB.
# Whatever gain the loop lands on is written to assets/work/gain.txt and reported in QA.md.
python3 assets/loudness.py assets/work/mix.wav assets/work/mix_mastered.m4a | tee assets/work/loudness.txt

ffmpeg -y -v error -framerate 30 -i assets/work/frames/f%04d.png \
  -i assets/work/mix_mastered.m4a \
  -map 0:v -map 1:a -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -profile:v high \
  -c:a copy -t 60 -movflags +faststart \
  -metadata title="IT ANSWERED — NIGHT TWO (pixel v07)" \
  video.mp4

# landscape derivative (same audio, letterboxed with a blurred bed)
ffmpeg -y -v error -i video.mp4 -filter_complex \
"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,gblur=sigma=28,eq=brightness=-0.12[bg];[0:v]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]" \
  -map "[v]" -map 0:a -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p -r 30 -c:a copy -t 60 \
  -movflags +faststart \
  -metadata title="IT ANSWERED — NIGHT TWO (pixel v07) — landscape derivative" \
  video-landscape.mp4

# stills for the PR / QA
for spec in "01:2.0" "02:31.0" "03:56.0"; do
  n="${spec%%:*}"; t="${spec##*:}"
  ffmpeg -y -v error -ss "$t" -i video.mp4 -frames:v 1 "stills/${n}.png"
done

echo "---- delivered ----"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels \
  -of default=noprint_wrappers=1 video.mp4
printf 'sha256  %s\n' "$(sha256sum video.mp4 | cut -d' ' -f1)"
