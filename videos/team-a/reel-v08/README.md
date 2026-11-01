# WARD TEN — reel v08

An original 60-second fictional hospital handover horror. `video.mp4` is the 1080×1920 vertical master; `video-landscape.mp4` is the 1920×1080 reframe, with original sidebars and independently rendered matching captions. The landscape shows the central 1080×1080 picture area of the master, rather than shrinking the entire portrait frame; the time stamp is recreated on the sidebar. `captions.srt`, seven extracted stills, screenplay and numeric QA accompany the films.

## Render offline

Requirements: Python 3.11+, NumPy and Pillow for rendering, SciPy for the independent narration audit (`python3 -m pip install -r requirements.txt`), and FFmpeg/ffprobe with libx264, libass, drawtext/FreeType, AAC and FLAC. From this directory:

```bash
./render.sh
./verify.sh
./check_timing.py
./audit_narration.py
```

The render builds original vector illustrations and a mathematically receding corridor, aligns subtitles to committed TTS word boundaries, synthesizes all music and effects from oscillators and seeded noise, normalizes the mix, and encodes both MP4s. It uses the committed offline narration FLAC and bundled typeface; no reference media or network is needed. Intermediate files are written to `/tmp` and cleaned afterward; `KEEP_TEMP=1 ./render.sh` retains the temporary mix analysis. Outputs overwrite the two MP4s and regenerate `captions.srt`. Pillow, FFmpeg and encoder version differences can change bytes even with identical source/timings.

Optional voice-stem regeneration requires internet and `edge-tts==7.3.1`: `python3 make_narration.py`. This is unnecessary for the offline render. The single designed voice is `en-US-ChristopherNeural` at −12% rate and −4 Hz pitch; long sentence gaps are shortened by cutting only verified near-digital silence, not speech. No real person is impersonated.

All screen layouts, corridor/bed artwork, screenplay, drone and Foley are original to this production. The sole typeface is Anton by Vernon Adams, distributed under the SIL Open Font License 1.1; the font and license are bundled in `assets/`. See `QA.md` for exact measurements, disclosure and limitations. This is fiction, not medical guidance. No public publishing is authorized.
