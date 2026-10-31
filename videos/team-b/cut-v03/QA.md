# QA — Cut v03: The Quiet Signal

## Measured result
- Duration: **60.000000 s** (inside 58–62 s).
- Picture: 1920×1080, 30/1 fps, H.264, yuv420p. MP4 faststart confirmed by atom order `ftyp @ 0`, `moov @ 32`, then `mdat @ 53176`.
- Sound: AAC, 48 kHz, stereo. Integrated loudness **−16.0 LUFS**; true peak **−3.3 dBTP**; LRA 4.6 LU. No clipping indicated; true peak is below the −1 dBTP ceiling.
- Size: 29,557,390 bytes (~28.2 MiB), below 90 MB.
- Captions: no spoken narration; all original story copy is burned into the motion graphics in a high-contrast dark-backed 40–58 px type treatment. No separate SRT is required for this non-narrated piece.
- Music/SFX source and licence: entirely synthesized by `project/sound.py` from generated sine oscillators, pulse envelopes, and fades; no recordings, samples, stock, or third-party music. Original work, no external licence required.
- Black/frozen frame scan: FFmpeg `blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-50dB:d=0.5` returned no black or freeze events.
- First/middle/end stills extracted and spot-checked: `stills/01.png` at 2.3 s, `02.png` at 25.3 s, `03.png` at 45.3 s. First second (0.2 s) and final second (59.8 s) were spot-checked for visible image and title; the automated scan covers the full clip. This was not a human real-time watch-through of every second.
- Reproducibility: `PATH=/path/to/ffmpeg-7.0.2-static:$PATH ./render.sh` exited 0, regenerated the MP4 and stills. Render took 93.7 seconds in this sandbox. Run `./render.sh` with FFmpeg and the Python dependencies documented in `project/README.md` to reproduce from the repo.

## Required ffprobe output (verbatim)
Command: `ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4`

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
size=29557390
```

## Required loudness verification
The spec's literal `ffmpeg -v error ... loudnorm=print_format=summary ...` command emits no text because `-v error` suppresses the summary. Re-ran without that suppression; the reported **Input** values below are the file's measured levels (the `Output` lines are what a hypothetical normalization pass would produce, not this file's levels):

```text
Input Integrated:    -16.0 LUFS
Input True Peak:      -3.3 dBTP
Input LRA:             4.6 LU
Input Threshold:     -26.3 LUFS

Output Integrated:   -24.2 LUFS
Output True Peak:    -11.5 dBTP
Output LRA:            4.5 LU
Output Threshold:    -34.5 LUFS

Normalization Type:   Dynamic
Target Offset:        +0.2 LU
```

## Blunt self-review
What works: the pulse-to-network idea reads cleanly; the warm beacon against a restrained midnight palette gives a clear visual anchor; the mid-piece dropout/reconnection creates a legible turn; the ending resolves without going to black. The typography is large and contrast-backed. The motion and score are original and deterministic.

What is weak: this is procedural motion design, not live-action conventional-editor footage. The city is an abstract grid rather than a richly observed place; some shots rely on the same visual grammar, and the synth score is simple and slightly repetitive. The supposed accelerated cutting is mainly animated change and shifting density, not a dense montage of distinct photographed shots. It is a complete short piece, but not a polished agency commercial. No full real-time watch-through or physical laptop legibility test was possible here; stills and automated full-clip checks are evidence, not substitutes for a human screening.

## Tool/environment map
See `project/README.md` for exact editor/browser checks, observed availability, limits, baseline memory, and render time. No Kdenlive/Shotcut/Xvfb/browser editing test could be run because the executables/display were absent. System FFmpeg was absent; the static binary workflow did successfully render at full required resolution. No 720p fallback was needed.
