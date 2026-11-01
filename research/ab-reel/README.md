# Ten-second voice check and image pairs

## Voices: one sentence, five sources

Play `five-voices-under-10s.mp3` (9.216 seconds); the same sentence is **“The ledger has four names.”** Or play `voice-A.mp3` through `voice-E.mp3` separately. Each excerpt is cut from the longer measured passage, and each was level-matched to −21 dBFS RMS before MP3 encoding; decoded sample RMS is −21.445 to −21.446 dBFS. No music or special EQ. There is 0.10 s between samples. Piper's endpoint is an energy-valley estimate, whereas Edge/Eleven use boundary telemetry. A single sentence and fixed playback order are **not** a statistically valid preference test.

| Slot | Approximate reel time | Voice/settings |
|---|---:|---|
| A | 0.00–1.97 | Edge Christopher, −12% / −4 Hz (the v10 baseline) |
| B | 2.07–3.65 | Edge Andrew Multilingual, +0% / +0 Hz (provisional default) |
| C | 3.75–5.49 | Edge Brian Multilingual, +0% / +0 Hz (provisional runner-up) |
| D | 5.59–7.37 | Piper Joe, length scale 1.12 (offline) |
| E | 7.47–9.19 | ElevenLabs Roger, multilingual v2 (reference) |

`voice-samples.json` records precise cuts and pre-encode RMS/peaks. Full benchmark audio and word/character events live under `../voice-matrix/`. See `../voices-reel.md` for the matrix, limitations and a blinded-panel protocol. **No human listening scores exist yet.**

## Images: three pairs

The following 1920×1080 JPEGs are matched before/after pairs, not different generated scenes:

- `image-01-awning-before.jpg` / `image-01-awning-after.jpg`
- `image-02-ledger-before.jpg` / `image-02-ledger-after.jpg`
- `image-03-reception-before.jpg` / `image-03-reception-after.jpg`

Inputs are the exact 1376×768 source JPEGs in `inputs/`. “Before” is Lanczos-only; “after” adds selective unsharp, a feathered depth mask, cool far haze and two masked rain sheets. The numerical ROI definitions, cautions and commands are in `../imaging-reel.md` and `../image-metrics.json`.
