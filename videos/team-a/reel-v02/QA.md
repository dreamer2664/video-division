# QA — Waiting has a curve, revised after fresh audit

## Bottom line: why the original was small

The fresh checkout of `reel/v02` at `19f85f965fab756a7bee39fa65d2f32099b8599a` contained the **7,524,354-byte** original. Its video stream was **787,644 bit/s** and the whole MP4 averaged **1,003,247 bit/s**. The explanation is **both** efficient compression of flat, low-motion graphics **and a picture that was too thin**: long comparison and graph holds were largely static apart from decorative movement.

Against the original program-drawn frames at 2, 9, 16, 24, 34, 44, 52 and 58 seconds, eight sampled decoded frames averaged **38.08 dB RGB PSNR** and **0.99927 luma SSIM** at half resolution. That limited test does not prove good visual quality, but it does not suggest that heavy compression damage was the main problem. File size is not a quality score. The actual weakness was the sparse staging and pacing.

I revised the picture, not just the encode: staggered kinetic type, moving orders through a service gate, even-versus-bunched arrival lanes, a wait ruler that fills over several seconds, a progressively drawn curve, and a capacity buffer that opens over time. The revised shot plan was committed in `script.md` before the replacement render. The same model, copy, score and 60-second structure are retained.

The replacement targets **4 Mb/s ABR**, with a 6 Mb/s maximum and no filler added just to inflate the file. It actually averages **2,542,766 bit/s video** because the mostly flat vector imagery remains easy to encode; its **20,687,910-byte** file is still smaller than the other samples mentioned in the brief. That is not by itself a fault or proof of professional polish. The new stream is about 3.23 times the original video bitrate and the motion is more explanatory, but the piece is still deliberately simple.

## Current committed video: measured facts

| Property | Result |
|---|---|
| Duration | **60.000000 s** |
| Picture | **1920×1080**, 30/1 fps, 1,800 decoded frames, H.264 High, yuv420p, libx264 |
| Bitrate | **2,542,766 bit/s video**; 207,114 bit/s AAC; 2,758,388 bit/s container |
| Audio | AAC, 48 kHz, stereo, **−16.0 LUFS** integrated and **−4.4 dBTP** true peak (`loudnorm` input measurement) |
| File | **20,687,910 bytes** (about 20.69 MB), below 90 MB; `moov` precedes `mdat` |
| Captions | Burned in; the eight matching caption cues also ship as `captions.srt`. There is no spoken narration. |
| Typography | Rendered type uses font size ≥54 px at 1080p; captions and selected palette pairs are high contrast. |
| SHA-256 | `03aa0efa0c8a649c3871bed05935486478babdef0e6865b072964bb4455b1802` |

## Spec commands, run on the committed replacement

The Git-object hash and working-file hash matched before the checks. The required `ffprobe` command returned this **verbatim**:

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
size=20687910
```

The spec's loudness command was run **exactly** as written:

```text
$ ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12
```

It produced **zero bytes**: this FFmpeg's `-v error` suppresses the filter's info-level summary. That blank output is not a loudness measurement. With normal verbosity, the actual output was:

```text
$ ffmpeg -hide_banner -nostats -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -16
        encoder         : Lavc61.19.101 pcm_s16le
[Parsed_loudnorm_0 @ 0x7efd18001b80]
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
[out#0/null @ 0x55ec37afeb40] video:773KiB audio:45008KiB subtitle:0KiB other streams:0KiB global headers:0KiB muxing overhead: unknown
frame= 1800 fps=257 q=-0.0 Lsize=N/A time=00:01:00.00 bitrate=N/A speed=8.58x
```

The **Input** numbers describe the delivered file. The Output numbers are from a temporary null-output normalization to the filter's default −24 LUFS; they do not modify `video.mp4`. An independent `ebur128=peak=true` analysis reported **−16.1 LUFS** and a **−4.4 dB** true peak; the 0.1 LU difference is the meter's reported rounding/implementation.

The separately measured bitrate/stream output was:

```text
$ ffprobe -v error -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,bit_rate,width,height,pix_fmt,r_frame_rate,nb_frames,sample_rate,channels -of default=noprint_wrappers=1 video.mp4
index=0
codec_name=h264
codec_type=video
width=1920
height=1080
pix_fmt=yuv420p
r_frame_rate=30/1
bit_rate=2542766
nb_frames=1800
index=1
codec_name=aac
codec_type=audio
sample_rate=48000
channels=2
r_frame_rate=0/0
bit_rate=207114
nb_frames=2814
duration=60.000000
size=20687910
bit_rate=2758388
```

For completeness, the freshly pulled **original** returned the following actual output from the same spec `ffprobe` command before replacement:

```text
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

Its exact spec loudnorm command also returned zero bytes; the corrected measurement was **−16.0 LUFS / −4.4 dBTP**.

## Playback, frames, text and captions

Direct playback first failed because this sandbox has no physical X display or `/dev/snd` audio device: `ffplay` reported `x11 not available` and ALSA reported `cannot find card '0'`. I then installed a virtual X display and ran the revised file through **ffplay from start to end** with SDL's **dummy audio sink**. It reached EOF successfully. I captured and inspected 60 chronological one-per-second images of that virtual playback, plus full-resolution decoded frames 0, 15, 1770 and 1799 to inspect the first and last seconds. The sampled type and burned captions are legible at 100%, and there was picture and motion at both ends.

**Limitation:** one-per-second visual inspection is not continuous subjective watching, and the dummy sink was not audible. I could not actually listen to the score or judge its balance on speakers/headphones. A person with a screen and sound device must perform that final subjective watch/listen; this is not claimed as completed.

`./verify.sh` decoded the full video and reported:

```text
=== Full decode, black/freeze detection (0.5 seconds) ===
No blackdetect or freezedetect events at the stated thresholds.

=== Numeric contract assertions ===
duration, size, 1080p30 H.264 yuv420p, decoded frame count, 48 kHz stereo AAC, -16 LUFS ±0.1, true peak ≤ -1 dBTP: PASS
```

The detection filters were `blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=0.5`. A second full decode to 320×180 grayscale frame hashes found **1,800 frames**, with the longest consecutive identical run **1 frame (0.033333 s)**. `silencedetect=noise=-50dB:d=0.5` reported no audio silence of 0.5 s or longer. These thresholded checks do not replace perception.

The SRT's eight timestamps and caption text were compared against the renderer: all match and cover 00:00–01:00. The committed stills were extracted from the replacement: `stills/01.png` at 00:02, `stills/02.png` at 00:35, and `stills/03.png` at 00:47.

## Encoding fidelity, faststart and reproduction

The same eight sample times on the replacement averaged **38.76 dB RGB PSNR** and **0.99957 half-resolution luma SSIM** against its own program-rendered source frames. Since the artwork changed, this is a check of sampled encode fidelity, not a controlled artistic-quality comparison. Re-run `python3 assets/audit_fidelity.py video.mp4`; this optional audit used OpenCV 4.11.0 and scikit-image 0.25.2 in addition to the render requirements. It decodes RGB frames with FFmpeg, computes OpenCV RGB PSNR, and compares 960×540 grayscale images with scikit-image SSIM. For the original, run the same method from a checkout of commit `19f85f9`, whose `assets/visuals.py` matches its video.

```text
ftyp: offset=0, size=32
moov: offset=32, size=63206
free: offset=63238, size=8
mdat: offset=63246, size=20624664
faststart: PASS
```

A fresh GitHub clone of `reel/v02` at `a0e0921ee619c2ce9ba738554e8d9bdc95e7d9f0` ran the committed `render.sh` using the bundled source and fonts. The rendered result matched the committed video byte-for-byte:

```text
03aa0efa0c8a649c3871bed05935486478babdef0e6865b072964bb4455b1802  committed video.mp4
03aa0efa0c8a649c3871bed05935486478babdef0e6865b072964bb4455b1802  clean-clone reproduction.mp4
BIT-IDENTICAL CLEAN-CLONE REPRODUCTION: PASS
```

Toolchain: Python 3.13.16, Pillow 12.3.0, NumPy 2.3.5, FFmpeg/ffprobe 7.1.5-0+deb13u1 with libx264 and AAC. `requirements.txt` pins the Python packages. No downloads or outside media are needed during the render; Python packages and FFmpeg must already be installed. Different encoder/library versions may change output bytes.

## Sources and blunt self-review

All visuals, original electronic music and effects are generated by `assets/visuals.py` and `assets/score.py`; original work is dedicated under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The unmodified bundled DejaVu fonts retain their separate licence in `assets/DejaVu-LICENSE.txt`. No unlicensed footage, samples, watermark or real-person voice is used.

The explanation is a simplified M/M/1 model; the dots are illustrative, not a measured café or simulation. The revision adds meaningful visual development, but the design remains minimalist, word-led and somewhat clinical; some compositions still hold for several seconds. The score has passed loudness/peak checks but has **not been heard**, so its mix and artistic quality remain an open review item. Manager B should evaluate the complete picture and sound on real playback equipment before calling it presentation-ready.
