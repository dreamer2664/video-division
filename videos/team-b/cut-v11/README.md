# CUT V11 — TWO LIGHTS (audio-only balance revision)

V11 is the v10 picture and caption track with the opening voice-to-bed level corrected. It uses the committed v10 narration stem and word telemetry; it does not synthesize a new voice or render any video frames.

## Reproduce

From the repository root:

```bash
python3 -m pip install -r videos/team-b/cut-v10/requirements.txt
python3 videos/team-b/cut-v11/build_audio_v11.py
```

Requires FFmpeg/ffprobe on `PATH`. The script attenuates only the bed by 2.3 dB, applies the committed two-pass EBU R128 normalization target, and remuxes the resulting AAC to the v10 H.264 video with `-c:v copy`. It verifies all 1,800 decoded video-frame hashes are identical before writing the output.

The v10 source MP4, narration/bed stems, pre-normalized mix, telemetry and locked captions are inputs under `videos/team-b/cut-v10/`. V11's processed bed stem, pre-master, normalized master, measurement ledger, loudnorm analysis, ffprobe output and final `video.mp4` are stored in this directory's `audio/` and root.

See `QA.md` for the before/after voice/bed margins, final loudness/true-peak measurements and picture-preservation checks.
