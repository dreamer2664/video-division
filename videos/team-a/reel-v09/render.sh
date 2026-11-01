#!/usr/bin/env bash
# Offline PERFECT TIME production; intermediate media live under /tmp.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)";cd "$HERE"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/reel-v09-build.XXXXXX")"
cleanup(){ if [[ "${KEEP_TEMP:-0}" != 1 ]];then rm -rf "$BUILD";else echo "Build evidence kept at $BUILD";fi; }
trap cleanup EXIT
printf 'Build intermediates: %s\n' "$BUILD"
python3 make_art.py --out "$BUILD"
python3 captions.py --ass "$BUILD/captions.ass"
python3 captions.py --ass "$BUILD/captions-landscape.ass" --landscape
python3 make_sound.py --out "$BUILD"
python3 mix_audio.py --out "$BUILD"
mkdir -p "$BUILD/fonts";cp assets/Anton-Regular.ttf "$BUILD/fonts/"
# 30 shots, repeating 54/60/66 frames; smooth 1.00 -> 1.06 push per shot.
U="if(lt(mod(on,180),54),mod(on,180)/53,if(lt(mod(on,180),114),(mod(on,180)-54)/59,(mod(on,180)-114)/65))"
Z="st(0,$U);1+0.06*(3*pow(ld(0),2)-2*pow(ld(0),3))"
V="590*mod(t-30,2)/2"
FILTER="[0:v]fps=30,zoompan=z='$Z':x='iw/2-iw/(2*zoom)':y='ih/2-ih/(2*zoom)':d=1:s=1080x1920:fps=30,setsar=1,drawtext=fontfile='$HERE/assets/Anton-Regular.ttf':text='|':fontcolor=0x5DD6E0:fontsize=65:x='140+800*mod(t,2)/2':y=1222,drawtext=fontfile='$HERE/assets/Anton-Regular.ttf':text='•':fontcolor=0xF7C653:fontsize=38:x='245+$V':y='775+43*sin(($V)*0.04)+18*sin(($V)*0.08)':enable='between(t,30,33.8)',ass=filename='$BUILD/captions.ass':fontsdir='$BUILD/fonts',format=yuv420p[v]"
ffmpeg -hide_banner -loglevel warning -y -threads 2 -filter_complex_threads 2 \
  -f concat -safe 0 -i "$BUILD/shots.ffconcat" -i "$BUILD/mix.m4a" \
  -filter_complex "$FILTER" -map '[v]' -map 1:a:0 -frames:v 1800 -t 60 \
  -c:v libx264 -preset veryfast -crf 23 -threads 2 -pix_fmt yuv420p -r 30 \
  -c:a copy -movflags +faststart -metadata title='Perfect Time' video.mp4

# Retain a native-size 1080-square picture crop, build original sidebars, and
# reburn the same speech-timed captions rather than shrinking the vertical frame.
LFILTER="[0:v]format=yuv420p[bg];[1:v]crop=1080:1080:0:300,setsar=1[fg];[bg][fg]overlay=(W-w)/2:0:shortest=1,drawtext=fontfile='$HERE/assets/Anton-Regular.ttf':text='•':fontcolor=0xF7C653:fontsize=48:x='350+10*sin(2*PI*t/2)':y=175,ass=filename='$BUILD/captions-landscape.ass':fontsdir='$BUILD/fonts',format=yuv420p[v]"
ffmpeg -hide_banner -loglevel warning -y -threads 2 -filter_complex_threads 2 \
  -loop 1 -framerate 30 -i "$BUILD/landscape-bg.png" -i video.mp4 \
  -filter_complex "$LFILTER" -map '[v]' -map 1:a:0 -frames:v 1800 -t 60 \
  -c:v libx264 -preset veryfast -crf 23 -threads 2 -pix_fmt yuv420p -r 30 \
  -c:a copy -movflags +faststart -metadata title='Perfect Time — landscape reframe' "$BUILD/landscape-encoded.mp4"
# Explicit 1:1 pixels / 16:9 display metadata, without video/audio recompression.
ffmpeg -hide_banner -loglevel error -y -i "$BUILD/landscape-encoded.mp4" -map 0 -c copy \
  -aspect 16:9 -movflags +faststart video-landscape.mp4
printf 'Rendered video.mp4 and video-landscape.mp4.\n'
