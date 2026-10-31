#!/usr/bin/env bash
# Numeric/structural QA. Does not pretend to listen or judge acting.
set -euo pipefail
cd "$(dirname "$0")"
Q="${1:-$(mktemp -d "${TMPDIR:-/tmp}/reel-v07-qa.XXXXXX")}"
mkdir -p "$Q"
for f in video.mp4 video-landscape.mp4; do
  echo "Analyzing $f"
  ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type \
    -of default=noprint_wrappers=1 "$f" >"$Q/$f.spec-ffprobe.txt"
  ffprobe -v error -show_streams -show_format "$f" >"$Q/$f.full-ffprobe.txt"
  ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames \
    -of default=noprint_wrappers=1 "$f" >"$Q/$f.frames.txt"
  # The exact spec command uses -v error, which suppresses the info-level summary.
  ffmpeg -v error -i "$f" -af loudnorm=print_format=summary -f null - >"$Q/$f.spec-loudnorm.txt" 2>&1
  ffmpeg -hide_banner -nostats -i "$f" -af 'loudnorm=I=-16:TP=-1:LRA=11:print_format=json' \
    -f null - >"$Q/$f.loudnorm-json.txt" 2>&1
  # blackdetect 0 is the usual dark threshold; 1 tests near-digital black.
  ffmpeg -hide_banner -nostats -i "$f" -filter_complex \
    '[0:v]blackdetect=d=0.5:pix_th=0.10:pic_th=0.98,blackdetect=d=0.5:pix_th=0.02:pic_th=0.98,freezedetect=n=-60dB:d=0.5[v];[0:a]silencedetect=noise=-50dB:d=0.5[a]' \
    -map '[v]' -map '[a]' -f null - >"$Q/$f.scan.txt" 2>&1
  ffmpeg -v error -i "$f" -f null - >"$Q/$f.decode-errors.txt" 2>&1
  sha256sum "$f" >"$Q/$f.sha256.txt"
  grep -E 'black_start|black_end|freeze_start|freeze_end|freeze_duration|silence_start|silence_end|silence_duration|Error|error' "$Q/$f.scan.txt" || true
done
ffprobe -v error -show_streams -show_format assets/narration.flac >"$Q/narration.ffprobe.txt"
echo "Complete; detailed numeric reports: $Q"
