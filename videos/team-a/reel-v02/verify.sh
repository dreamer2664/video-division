#!/usr/bin/env bash
# Inspect the delivered MP4. Usage: ./verify.sh [path-to-video.mp4]
set -euo pipefail
cd "$(dirname "$0")"
FILE="${1:-video.mp4}"
test -r "$FILE" || { echo "Cannot read: $FILE" >&2; exit 1; }
for cmd in ffmpeg ffprobe python3 sha256sum; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 1; }; done
export LC_ALL=C
printf '\n=== SPEC ffprobe (verbatim command) ===\n'
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 "$FILE"
printf '\n=== SPEC loudnorm (verbatim command) ===\n'
# Note: this exact command suppresses the summary on stock FFmpeg, because -v error
# hides loudnorm's info-level printout. The corrected measurement follows it.
TMP="$(mktemp -d "${TMPDIR:-/tmp}/reel-verify.XXXXXXXX")"
trap 'rm -f "$TMP/spec.log" "$TMP/detect.log"; rmdir "$TMP" 2>/dev/null || true' EXIT
ffmpeg -v error -i "$FILE" -af loudnorm=print_format=summary -f null - 2>"$TMP/spec.log"
tail -12 "$TMP/spec.log"
if test ! -s "$TMP/spec.log"; then echo '(no output; -v error suppresses the summary)'; fi
printf '\n=== AUDIO measurement (corrected verbosity) ===\n'
ffmpeg -hide_banner -nostats -i "$FILE" -af loudnorm=print_format=summary -f null - 2>&1 | tail -16
printf '\n=== Video stream detail and decoded frame count ===\n'
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=profile,pix_fmt,r_frame_rate,avg_frame_rate,nb_read_frames,duration -of default=noprint_wrappers=1 "$FILE"
printf '\n=== Audio stream detail ===\n'
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels,channel_layout,duration -of default=noprint_wrappers=1 "$FILE"
printf '\n=== MP4 top-level atoms (moov must precede mdat) ===\n'
python3 - "$FILE" <<'PY'
import struct, sys
p=sys.argv[1]
with open(p,'rb') as f:
    f.seek(0,2); end=f.tell(); f.seek(0); atoms=[]
    while f.tell()+8<=end:
        offset=f.tell(); size,name=struct.unpack('>I4s',f.read(8)); header=8
        if size==1:
            size=struct.unpack('>Q',f.read(8))[0]; header=16
        elif size==0: size=end-offset
        if size<header or offset+size>end: raise SystemExit('Invalid MP4 atom size')
        name=name.decode('ascii','replace'); atoms.append((name,offset,size))
        print(f'{name}: offset={offset}, size={size}')
        f.seek(offset+size)
    names=[x[0] for x in atoms]
    if 'moov' not in names or 'mdat' not in names or names.index('moov') > names.index('mdat'):
        raise SystemExit('FAIL: moov does not precede mdat')
    print('faststart: PASS')
PY
printf '\n=== Full decode, black/freeze detection (0.5 seconds) ===\n'
ffmpeg -hide_banner -nostats -i "$FILE" -vf 'blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=0.5' -an -f null - 2>"$TMP/detect.log"
if grep -E 'black_start|freeze_start|freeze_end|freeze_duration' "$TMP/detect.log"; then
  echo 'Review events above; this is a diagnostic, not a pass.'
else
  echo 'No blackdetect or freezedetect events at the stated thresholds.'
fi
printf '\n=== SHA-256 ===\n'
sha256sum "$FILE"
