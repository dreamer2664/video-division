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

## Required loudness verification (re-run against fresh remote checkout)
The spec's literal `ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12` emitted **no text**: `-v error` suppresses the summary on this FFmpeg build. I ran the same analysis without `-v error` and captured the filter's measured input and resulting summary. The **Input** lines describe the committed file; the **Output** lines describe what a hypothetical normalization pass would produce, not this file's levels.

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

Additional audio check: `astats=metadata=1:reset=0` measured peak levels of −3.35 / −3.30 dBFS for the channels (consistent with loudnorm true peak −3.3 dBTP). `silencedetect=noise=-50dB:d=0.5` returned no events; the intentional middle dip is not dead air. FFmpeg `blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-50dB:d=0.5` also returned no events.

## Picture / edit checks (fresh remote checkout)
I extracted and inspected frames at 0.2 s and 59.8 s: both show an animated graphic and legible title, not black/frozen frames. The three committed stills at 2.3, 25.3, and 45.3 s show the hook, development, and later progression. Story text is visibly burned in with a dark backing, high contrast, and 40–58 px font sizes (minimum glyph height varies by font; configured sizes are 40 px and up). At 100% in the extracted 1920×1080 stills the copy is readable. There is no voice-over; all spoken-word captions are therefore inapplicable. The displayed story copy is burned in. This check is still a spot-check, not a human real-time watch-through of all 60 seconds.

## Blunt self-review
What works: the pulse-to-network idea reads cleanly; the warm beacon against a restrained midnight palette gives a clear visual anchor; the mid-piece dropout/reconnection creates a legible turn; the ending resolves without going to black. The typography is large and contrast-backed. The motion and score are original and deterministic.

What is weak: this is procedural motion design, not live-action conventional-editor footage. The city is an abstract grid rather than a richly observed place; some shots rely on the same visual grammar, and the synth score is simple and slightly repetitive. The supposed accelerated cutting is mainly animated change and shifting density, not a dense montage of distinct photographed shots. It is a complete short piece, but not a polished agency commercial. No full real-time watch-through or physical laptop legibility test was possible here; stills and automated full-clip checks are evidence, not substitutes for a human screening.

## Toolchain map (observed, not inferred)
- **Kdenlive / Shotcut under Xvfb+VNC:** `command -v kdenlive shotcut Xvfb x11vnc` found none; `$DISPLAY`/Wayland were unset. These apps were **not launched**; there was no crash to report. The stated limitation is unavailable GUI/editor prerequisites, not an editor failure.
- **Browser editors:** no Chromium/Chrome binary or desktop session. Only HTTP HEAD reachability was checked: Kapwing 200, Clipchamp 302 redirect to `/en/`, Canva 403. No browser editor UI, editing, or export was exercised; no claim that any browser editor worked or crashed.
- **CLI compositing:** Python 3 + OpenCV + Pillow generated 1,800 full-HD animated frames piped to a downloaded FFmpeg 7.0.2 static binary; FFmpeg libx264 encoded the picture, then AAC muxed the original synthesized score. This **worked** and `render.sh` exited 0 on reproduction. No 720p fallback.
- **Memory:** the recorded pre-render `free -h` snapshot was 1.9 GiB total, 488 MiB used, 1.3 GiB free, 1.5 GiB available, zero swap. Peak RSS of the renderer/editor processes was **not measured**, so this is a baseline only—not a peak or a claimed memory ceiling.
- **Fresh verification:** this QA revision was made after cloning `cut/v03` fresh from origin at `e20082d3798fe0a2ec7ef5e4f43a3255cc1501f`; ffprobe/loudnorm and picture/audio checks were rerun on that clone. Detailed availability notes and observed network statuses are in `project/README.md`.
