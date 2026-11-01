# CUT V10 — TWO LIGHTS

Photographic 60-second short, rendered 1920×1080 at 30 fps.

## Reproduction

The final narration source MP3, captured Edge-TTS WordBoundary telemetry, photographic plates, grade-v05 33³ LUTs, and deterministic rain/drone recipe are kept in this directory.

```bash
python3 -m pip install -r videos/team-b/cut-v10/requirements.txt
python3 videos/team-b/cut-v10/render_v10.py
```

The full render is offline once the committed source assets exist; it requires FFmpeg and ffprobe on `PATH`. To intentionally obtain a new online voice take (which will change its hash/timing), run `python3 videos/team-b/cut-v10/synthesize_voiceover.py` first, then render again.

## Audio-only normalization fix

To update the existing MP4 audio without re-rendering or re-encoding a single video frame, run:

```bash
python3 videos/team-b/cut-v10/fix_audio_only.py
```

It runs measured two-pass loudnorm from the committed pre-normalization WAV, writes the normalized 48 kHz master and remuxes with `-c:v copy`; it verifies all 1,800 decoded video-frame hashes remain identical.
