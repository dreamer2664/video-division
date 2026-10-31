# QA — Waiting has a curve

## Result and limitations

The encoded media checks pass. **A subjective, real-time watch/listen did not happen:** this sandbox has no display (`DISPLAY` is unset) or sound device (`/dev/snd` is absent). I tried `ffplay` on the final file: video playback failed with `Could not initialize SDL - x11 not available`; the audio-only attempt reported `cannot find card '0'` / `Unknown PCM default`. A person with a screen and speakers still needs to watch and listen all the way through. This is a review limitation, not a claim that playback was performed.

Instead, I decoded the entire file, visually examined 60 chronological one-per-second frames from the encoded MP4 and four full-resolution boundary frames (frames 0, 15, 1770, 1799), and ran the measurements below. The first and final second show picture and continuing motion; no cropped captions or black end card were apparent in those inspected samples. Full decoding is not a substitute for subjective playback.

| Property | Measured result |
|---|---|
| Container duration | **60.000000 s** |
| Video | 1920×1080, 30/1 fps, 1,800 decoded frames, H.264 High, yuv420p; encoded by libx264 |
| Audio | AAC, 48,000 Hz, two channels / stereo, 60.000000 s |
| Integrated audio | **−16.0 LUFS** (`loudnorm` input measurement); independently **−16.1 LUFS** (`ebur128`, rounding/implementation difference) |
| True peak | **−4.4 dBTP**, no digital clipping indicated |
| Size | **7,524,354 bytes** (about 7.18 MiB), below 90 MB |
| MP4 faststart | `moov` at byte 32, before `mdat` at byte 63,103 |
| Captions | Burned in; also `captions.srt`. Eight cues match the rendered copy and cover 00:00–01:00. No narration. |
| Typography | All rendered text uses font size ≥54 px at 1080p; tested palette pairs have ≥5.45:1 contrast. |
| SHA-256 | `60fef61804c4189f71a047f67abc90a1f2f5a7ef52040d8a43d40dded99050c9` |

## Spec verification commands — actual output

From this directory, the spec's first command returned the following **verbatim**:

```text
$ ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4
codec_name=h264
codec_type=video
width=1920
height=1080
r_frame_rate=30/1
codec_name=aac
codec_type=audio
r_frame_rate=0/0
duration=60.000000
size=7524354
```

The spec's second command was also run **exactly**:

```text
$ ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12
```

It returned **zero bytes**. On the tested FFmpeg, `-v error` suppresses the info-level `loudnorm` summary; the blank output is not a loudness measurement. Repeating with normal verbosity produced the following actual output. The **Input** values describe the delivered file. The Output values describe a temporary, un-saved normalization to the filter's default −24 LUFS and are not the file's levels.

```text
$ ffmpeg -hide_banner -nostats -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -16
        encoder         : Lavc61.19.101 pcm_s16le
[Parsed_loudnorm_0 @ 0x7f5bb8001b80]
Input Integrated:    -16.0 LUFS
Input True Peak:      -4.4 dBTP
Input LRA:             1.8 LU
Input Threshold:     -26.1 LUFS

Output Integrated:   -23.7 LUFS
Output True Peak:    -11.9 dBTP
Output LRA:            1.1 LU
Output Threshold:    -33.7 LUFS

Normalization Type:   Dynamic
Target Offset:        -0.3 LU
[out#0/null @ 0x559bcf0e3940] video:773KiB audio:45008KiB subtitle:0KiB other streams:0KiB global headers:0KiB muxing overhead: unknown
frame= 1800 fps=238 q=-0.0 Lsize=N/A time=00:01:00.00 bitrate=N/A speed=7.94x
```

An independent `ebur128=peak=true` run reported `I: -16.1 LUFS`, `LRA: 1.5 LU`, and `Peak: -4.4 dBFS` in its true-peak summary.

## Other measured checks

`./verify.sh` runs the spec commands, measures the audio, checks the file's atom order, fully decodes the video for black/freeze analysis, counts decoded frames, and asserts the numeric format requirements. Selected actual output:

```text
=== Video stream detail and decoded frame count ===
profile=High
pix_fmt=yuv420p
r_frame_rate=30/1
avg_frame_rate=30/1
duration=60.000000
nb_read_frames=1800

=== Audio stream detail ===
codec_name=aac
sample_rate=48000
channels=2
channel_layout=stereo
duration=60.000000

=== MP4 top-level atoms (moov must precede mdat) ===
ftyp: offset=0, size=32
moov: offset=32, size=63063
free: offset=63095, size=8
mdat: offset=63103, size=7461251
faststart: PASS

=== Full decode, black/freeze detection (0.5 seconds) ===
No blackdetect or freezedetect events at the stated thresholds.

=== Numeric contract assertions ===
duration, size, 1080p30 H.264 yuv420p, decoded frame count, 48 kHz stereo AAC, -16 LUFS ±0.1, true peak ≤ -1 dBTP: PASS

=== SHA-256 ===
60fef61804c4189f71a047f67abc90a1f2f5a7ef52040d8a43d40dded99050c9  video.mp4
```

The full-file detection was `blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=0.5`. A separate full decode to 320×180 grayscale `framemd5` produced 1,800 hashes; the longest consecutive identical run was **1 frame**, or 0.033333 s. Audio `silencedetect=noise=-50dB:d=0.5` reported no silence of 0.5 s or longer. These are thresholded automated checks, not a guarantee that the piece feels lively or sounds good.

**Failure found and fixed:** the initial render's quiet comparison and graph sections triggered `freezedetect` for intervals up to 3.33 s. I strengthened the moving background, moved the gauge marker outside the numbers to avoid obscuring them, made a targeted test with no freeze events, and rerendered. The final full-file test above has no events at the same threshold.

The three committed stills come from the final encoded video:

- `stills/01.png` — 00:02, hook.
- `stills/02.png` — 00:34, 90% comparison.
- `stills/03.png` — 00:45, waiting-time curve.

## Reproducibility

A fresh single-branch clone from GitHub at checkpoint `0c4630684723be42503f7d430f4153a28b9a762b` was rendered using only its tracked assets, with `OUTPUT=/home/user/reel-v02-clean-reproduction.mp4 ./render.sh`. The original and reproduced MP4s were compared byte-for-byte:

```text
60fef61804c4189f71a047f67abc90a1f2f5a7ef52040d8a43d40dded99050c9  /home/user/video-division/videos/team-a/reel-v02/video.mp4
60fef61804c4189f71a047f67abc90a1f2f5a7ef52040d8a43d40dded99050c9  /home/user/reel-v02-clean-reproduction.mp4
BIT-IDENTICAL CLEAN-CLONE REPRODUCTION: PASS
```

Toolchain: Python 3.13.16, Pillow 12.3.0, NumPy 2.3.5, FFmpeg/ffprobe 7.1.5-0+deb13u1 with libx264 and AAC. `requirements.txt` pins the Python packages. The render does not download anything; installed Python packages and FFmpeg are prerequisites. Byte-identical output is verified with this toolchain; other encoder or library versions may produce different bytes.

## Sources, licences and model

All pictures, diagrams, transitions, music and effects were generated by `assets/visuals.py` and `assets/score.py`; there is no stock footage, sample library, watermark, or real-person voice. The original graphics and synthesized composition are dedicated under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The three bundled, unmodified DejaVu fonts have their own redistribution licence, included as `assets/DejaVu-LICENSE.txt`. No other media was sourced.

The wait numbers are the expected **queue wait before service** in the specified steady-state M/M/1 model, not empirical café measurements. The dots are illustrative. Full assumptions and the formula are in `script.md`.

## Blunt self-review

The causal comparison, labels and graph are readable, and the piece has a hook, development and payoff. The 50% and 90% comparisons hold their layouts for a long time; some motion is decorative rather than explanatory, so the pacing is less polished than a strong commissioned motion-design piece. The word-led, unvoiced treatment may feel clinical, and a real café need not match this simple queue model. The music has only been checked by measurements, not heard on speakers or headphones, so its balance and subjective quality remain unverified. Manager B should review the full video and sound before treating it as presentation-ready.
