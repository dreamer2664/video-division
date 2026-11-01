# PERFECT TIME — reel v09

An original 60-second fictional call-centre system-horror film. `video.mp4` is the 1080×1920 vertical master; `video-landscape.mp4` is the 1920×1080 reframe, with original sidebars and matching independently burned captions. The landscape shows the central 1080×1080 picture area of the master at native size instead of shrinking the portrait frame; it recreates the time marker in the sidebar. `captions.srt`, extracted stills, screenplay, source and numeric QA accompany the films.

## Offline rendering and verification

Requirements: Python 3.11+, NumPy and Pillow for rendering, SciPy for the independent narration audit (`python3 -m pip install -r requirements.txt`), and FFmpeg/ffprobe with libx264, libass, drawtext/FreeType, AAC and FLAC. From this directory:

```bash
./render.sh
./verify.sh
./check_timing.py
./audit_narration.py
```

The renderer constructs original screen layouts and a one-point-perspective call-centre floor, aligns 2–5-word captions to the committed narration word telemetry, synthesizes the drone and call/relay sounds from oscillators and seeded noise, normalizes the mix, and encodes both MP4s. It uses the committed offline narration FLAC and bundled typeface; no reference media or network is needed. Intermediates go to `/tmp` and are cleaned afterward; `KEEP_TEMP=1 ./render.sh` retains the temporary mix analysis. Outputs overwrite the two MP4s and regenerate `captions.srt`. Python/Pillow/FFmpeg/encoder versions can change bytes.

Optional voice-stem regeneration requires internet and `edge-tts==7.3.1`: `python3 make_narration.py`. This is unnecessary for offline rendering. The independently selected voice is `en-US-ChristopherNeural` at −12% rate and −4 Hz pitch; near-digital-silent sentence gaps are shortened, not time-stretched, and the longer dramatic pause is retained. No real person is impersonated.

All screen layouts, perspective artwork, screenplay, drone and Foley are original. Anton by Vernon Adams, under the SIL Open Font License 1.1, is bundled in `assets/`. See `QA.md` for measured results and limitations. This is fiction; no public video publishing is authorized.
