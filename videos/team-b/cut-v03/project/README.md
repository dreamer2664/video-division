# Project / reproducibility notes

This is a generated motion-design edit (no footage); the timeline and shot durations are in `../script.md`. Run `../render.sh` from any directory. Prerequisites: FFmpeg with libx264 + AAC support; Python 3 with opencv-python-headless, numpy, Pillow; DejaVu Sans at `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` and `DejaVuSans-Bold.ttf`. The project makes a 60-second 1920×1080 30 fps animated H.264 intermediate, synthesizes the original stereo score, then muxes it with AAC at 48 kHz and applies 9.1 dB gain to reach the -16 LUFS target. It regenerates the three QA stills.

`render.py` emits 1,800 procedurally drawn frames through FFmpeg stdin; `sound.py` generates the score sample-by-sample using sine oscillators and a shaped pulse. Both are source, not opaque project files. Intermediate `picture.mp4` is intentionally not committed; render.sh regenerates it.

## Sandbox capability map (observed)
- Kdenlive, Shotcut, Xvfb, x11vnc, Chromium/Chrome: not installed (`command -v` returned no paths). There was no `DISPLAY`/Wayland session, so launching these in a virtual display was not possible; no claim of an editor crash is made.
- Browser editors: network HEAD checks only (not a real browser/editor session): Kapwing returned HTTP 200, Clipchamp redirected (302) to `/en/`, Canva returned HTTP 403. No browser executable or desktop session exists to test editing or export; browser-editor usability remains unverified.
- System FFmpeg/ffprobe: initially absent. A standalone FFmpeg 7.0.2 static binary was downloaded outside the repository and successfully encoded the 1080p H.264 output with AAC muxing. Python/OpenCV/Pillow compositing worked and completed a 60-second render in about 94 seconds, around 0.64× real time. This is the only working pipeline tested.
- Memory snapshot before production: 1.9 GiB total, 488 MiB used, 1.3 GiB free, 1.5 GiB available, no swap. Peak per-process render memory was not measured; the machine remained operational. Do not interpret the baseline as a peak measurement.
