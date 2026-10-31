#!/usr/bin/env bash
# Offline, deterministic illustration/caption/mix pipeline. All intermediates live in /tmp.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/reel-v07-build.XXXXXX")"
cleanup(){ if [[ "${KEEP_TEMP:-0}" != 1 ]]; then rm -rf "$BUILD"; else echo "Build evidence kept at $BUILD"; fi; }
trap cleanup EXIT
printf 'Build intermediates: %s\n' "$BUILD"
python3 make_art.py --out "$BUILD"
python3 captions.py --ass "$BUILD/captions.ass"
python3 make_sound.py --out "$BUILD"
python3 mix_audio.py --out "$BUILD"
mkdir -p "$BUILD/fonts"
cp assets/Anton-Regular.ttf "$BUILD/fonts/"

# Each still is exactly 72 output frames. Ease 1.00 -> 1.06 over the 72 frames,
# reset at the hard cut. A single live-camera cursor moves independently. drawtext
# avoids a framesync queue of full-size images in the memory-constrained sandbox.
FILTER="[0:v]fps=30,zoompan=z='1+0.06*(3*pow(mod(on,72)/71,2)-2*pow(mod(on,72)/71,3))':x='iw/2-iw/(2*zoom)':y='ih/2-ih/(2*zoom)':d=1:s=1080x1920:fps=30,setsar=1,drawtext=fontfile='$HERE/assets/Anton-Regular.ttf':text='•':fontcolor=0xF5C542:fontsize=54:x='920+12*sin(2*PI*t/2.4)':y=162,ass=filename='$BUILD/captions.ass':fontsdir='$BUILD/fonts',format=yuv420p[v]"
ffmpeg -hide_banner -loglevel warning -y -threads 2 -filter_complex_threads 2 \
  -f concat -safe 0 -i "$BUILD/shots.ffconcat" -i "$BUILD/mix.m4a" \
  -filter_complex "$FILTER" -map '[v]' -map 1:a:0 -frames:v 1800 -t 60 \
  -c:v libx264 -preset veryfast -crf 19 -threads 2 -pix_fmt yuv420p -r 30 \
  -c:a copy -movflags +faststart -metadata title='Arrival Log' video.mp4

# Keep the entire vertical image; original dark illustrated sidebars make the archive derivative.
ffmpeg -hide_banner -loglevel warning -y -threads 2 -filter_complex_threads 2 \
  -loop 1 -framerate 30 -i "$BUILD/landscape-bg.png" -i video.mp4 \
  -filter_complex '[0:v]format=yuv420p[bg];[1:v]scale=608:1080:flags=lanczos,setsar=1[fg];[bg][fg]overlay=(W-w)/2:0:shortest=1,format=yuv420p[v]' \
  -map '[v]' -map 1:a:0 -frames:v 1800 -t 60 -c:v libx264 -preset veryfast -crf 19 -threads 2 \
  -pix_fmt yuv420p -r 30 -c:a copy -movflags +faststart -metadata title='Arrival Log — landscape derivative' video-landscape.mp4
printf 'Rendered video.mp4 and video-landscape.mp4.\n'
