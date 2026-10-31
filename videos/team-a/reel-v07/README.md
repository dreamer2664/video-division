# Arrival Log — v07

A self-contained, original 60-second rule-horror short. `video.mp4` is the 1080×1920 master; `video-landscape.mp4` is the 1920×1080 full-portrait archive derivative. `captions.srt` is also supplied. The screenplay and shot plan were committed before picture generation.

## Re-render offline

Requirements: Python 3.10+, NumPy and Pillow (`python3 -m pip install -r requirements.txt`), and FFmpeg/ffprobe with `libx264`, `libass`, `drawtext`/FreeType, AAC and FLAC. From this directory:

```bash
./render.sh
```

The script draws original vector-like compositions, builds the ASS word highlights from `assets/word_timings.json`, synthesizes the drone and dry foley, mixes and two-pass-normalizes audio, then encodes both deliverables. It uses the **committed offline** `assets/narration.flac` and bundled Anton typeface; it needs no network, external references, or additional media. Intermediate files go into a new directory under `/tmp` and are removed afterward. Set `KEEP_TEMP=1 ./render.sh` to preserve that directory and its audio-analysis JSON for inspection. Outputs will overwrite the two MP4s and regenerate `captions.srt`. Pixel and codec bytes can vary with Pillow, FFmpeg and encoder versions; the timings, assets and processing are fixed.

Optional voice-stem regeneration is separate and requires internet plus `edge-tts==7.3.1`: `python3 make_narration.py`. It contacts the Edge TTS service; the already committed FLAC makes this unnecessary for the film render. It does not impersonate a real person. Sentence gaps are shortened only by removing measured near-digital-silence, without time-stretching the speech; a deliberate long pre-reveal pause remains.

## Source and rights

All illustrations, layout, screenplay, music and sound effects were generated for this piece by the scripts in this directory; no reference frames, recordings, stock or photos were used. The sole typeface is Anton by Vernon Adams, distributed under the SIL Open Font License 1.1; the font and its license are bundled in `assets/`. The designed synthetic narration is produced by Microsoft Edge neural TTS (`en-US-ChristopherNeural`), rate −12% and pitch −4 Hz; service terms apply to regeneration. `QA.md` contains measurements, commands, limitations and the full timeline. No publishing is authorized by this package.
