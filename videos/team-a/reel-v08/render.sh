#!/usr/bin/env bash
# Offline WARD TEN production. All intermediate media live in /tmp.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
BUILD="$(mktemp -d "${TMPDIR:-/tmp}/reel-v08-build.XXXXXX")"
cleanup(){ if [[ "${KEEP_TEMP:-0}" != 1 ]]; then rm -rf "$BUILD"; else echo "Build evidence kept at $BUILD"; fi; }
trap cleanup EXIT
printf 'Build intermediates: %s\n' "$BUILD"
python3 make_art.py --out "$BUILD"
python3 captions.py --ass "$BUILD/captions.ass"
python3 captions.py --ass "$BUILD/captions-landscape.ass" --landscape
python3 make_sound.py --out "$BUILD"
python3 mix_audio.py --out "$BUILD"
mkdir -p "$BUILD/fonts"; cp assets/Anton-Regular.ttf "$BUILD/fonts/"

# 30 cuts, repeating 54/60/66 frames. Ease 1.00 -> 1.06 separately per shot.
U="if(lt(mod(on,180),54),mod(on,180)/53,if(lt(mod(on,180),114),(mod(on,180)-54)/59,(mod(on,180)-114)/65))"
Z="st(0,$U);1+0.06*(3*pow(ld(0),2)-2*pow(ld(0),3))"
FILTER="[0:v]fps=30,zoompan=z='$Z':x='iw/2-iw/(2*zoom)':y='ih/2-ih/(2*zoom)':d=1:s=1080x1920:fps=30,setsar=1,drawtext=fontfile='$HERE/assets/Anton-Regular.ttf':text='|':fontcolor=0x70D7B3:fontsize=65:x='140+800*mod(t,2)/2':y=1270,ass=filename='$BUILD/captions.ass':fontsdir='$BUILD/fonts',format=yuv420p[v]"
ffmpeg -hide_banner -loglevel warning -y -threads 2 -filter_complex_threads 2 \
  -f concat -safe 0 -i "$BUILD/shots.ffconcat" -i "$BUILD/mix.m4a" \
  -filter_complex "$FILTER" -map '[v]' -map 1:a:0 -frames:v 1800 -t 60 \
  -c:v libx264 -preset veryfast -crf 23 -threads 2 -pix_fmt yuv420p -r 30 \
  -c:a copy -movflags +faststart -metadata title='Ward Ten' video.mp4

# Landscape is a true reframe: the central 1080-square story picture is preserved
# without scaling tiny UI; the time stamp is recreated on the sidebar and captions
# are independently burned at landscape size from the identical timing data.
LFILTER="[0:v]format=yuv420p[bg];[1:v]crop=1080:1080:0:300,setsar=1[fg];[bg][fg]overlay=(W-w)/2:0:shortest=1,drawtext=fontfile='$HERE/assets/Anton-Regular.ttf':text='•':fontcolor=0xF5D14E:fontsize=48:x='350+10*sin(2*PI*t/2)':y=175,ass=filename='$BUILD/captions-landscape.ass':fontsdir='$BUILD/fonts',format=yuv420p[v]"
ffmpeg -hide_banner -loglevel warning -y -threads 2 -filter_complex_threads 2 \
  -loop 1 -framerate 30 -i "$BUILD/landscape-bg.png" -i video.mp4 \
  -filter_complex "$LFILTER" -map '[v]' -map 1:a:0 -frames:v 1800 -t 60 \
  -c:v libx264 -preset veryfast -crf 23 -threads 2 -pix_fmt yuv420p -r 30 \
  -c:a copy -movflags +faststart -metadata title='Ward Ten — landscape reframe' video-landscape.mp4
printf 'Rendered video.mp4 and video-landscape.mp4.\n'
