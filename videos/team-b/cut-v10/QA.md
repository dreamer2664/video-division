# QA — CUT V10: TWO LIGHTS

## Pre-render brief and visual gate

- Deliverable: exactly 60.000 s, 1920×1080 landscape, 30/1 fps CFR, H.264/yuv420p, AAC 48 kHz stereo.
- Story gate: one car enters at Junction 4 and is never shown leaving; eight synchronized camera feeds show the same pair of headlights; the operator's counted result remains **two**.
- Image gate: generated photorealistic motorway/control-room plates; no flat-vector sequence, empty dark-field cutaway, or portrait material. The photographed room, operator, and physical CRTs remain the subject.
- House-look source: the root directive and available grade-v05 `generate_luts.py`, all four 33³ LUTs, `render_v05.py`, plates, `script.md`, and `QA.md` were studied. `look/HOUSE-LOOK.md` was absent from the checked-out `main` tree; QA records that limitation. The available reference implements a 33³ trilinear LUT, filmic S-curve, cold nocturnal shadows / warm practical, photographic plates, parallax rain, halation, grain, and slow camera push.
- **Hero frame named before render:** `HERO-01 — TWO LIGHTS IN THE WINDOW`, 00:56.700 / frame 1701. The real rain-glazed control room and operator stay in focus; the earlier eight-feed anomaly resolves into headlights reflected in the window. Still: `stills/HERO-01-two-lights-in-the-window.png`.
- Voice: `edge-tts en-US-ChristopherNeural --rate=-12% --pitch=-4Hz`. Ominous procedural bed. The narration stem and captured WordBoundary telemetry are committed; 28 captions are boundary-derived and each contains 2–5 words.
- The earlier baby-monitor cut was withdrawn; it is not part of this deliverable.

## Audio-only normalization correction — 2026-11-01

**Scope:** only the audio gain chain changed. `fix_audio_only.py` reran the two-pass EBU R128 `loudnorm` chain and remuxed the new AAC audio with FFmpeg `-c:v copy`. The picture was not rendered or re-encoded. Comparing decoded `framemd5` outputs before and after gives **1800/1800 identical frame hashes**; frame-hash-list SHA-256: `6a5195c0306db2242e1e8f1603da6b1ae0944a9d8487ce6d15743bf64b0dcae0`.

- Original delivered audio measured: **−22.22 LUFS / −5.71 dBTP**.
- Two-pass target: integrated loudness `I=-16.0`, true peak target `TP=-1.5 dBTP` (0.5 dB AAC safety margin under the `≤−1.0 dBTP` ceiling), `LRA=11`, dynamic mode because the available true-peak headroom does not permit a purely linear gain increase.
- Pass 1 measured the locked pre-loudnorm WAV at `−22.18 LUFS / −5.75 dBTP`.
- Pass 2 output JSON reports `−16.07 LUFS / −1.50 dBTP`.
- **Decoded final AAC verification:** `−16.27 LUFS / −1.41 dBTP`, within `−16.0 ±0.5 LUFS` and below the `−1.0 dBTP` ceiling.
- Silence scan on final remux (`silencedetect=n=-40dB:d=1.2`): **0 events**. Black/freeze scan on final remux (`blackdetect` and `freezedetect`, 0.5 s threshold): **0 black events; 0 freeze events**.
- Reproducible audio-only command: `python3 videos/team-b/cut-v10/fix_audio_only.py`. It consumes `audio/master_audio_pre_loudnorm_48k.wav`, runs measured two-pass loudnorm, emits `audio/master_audio_48k.wav`, and remuxes without touching the video stream.
- Original lossless stems and 60-second picture remain in place. The pre-loudnorm source WAV SHA-256 is `257f79de296f9476158ce49a1674dca62a4d506aafb4b76cc29e50feca5ab369`; normalized WAV SHA-256 is `77d668bdc0690a76fc32256e9d95bb35deeac4a24bbb6215cd9285a1267a73aa`.
- Final MP4 SHA-256: `e093a55f941b72fc694b3f9c50bf3ce559307cc658c0f2161ed2ebfaad589403` (`35,395,888` bytes).

### Loudnorm JSON — pass 1 (measurement)

```json
{
  "input_i": "-22.18",
  "input_tp": "-5.75",
  "input_lra": "5.10",
  "input_thresh": "-32.25",
  "output_i": "-16.36",
  "output_tp": "-1.50",
  "output_lra": "2.50",
  "output_thresh": "-26.41",
  "normalization_type": "dynamic",
  "target_offset": "0.36"
}
```

### Loudnorm JSON — pass 2 (normalized PCM master)

```json
{
  "input_i": "-22.18",
  "input_tp": "-5.75",
  "input_lra": "5.10",
  "input_thresh": "-32.25",
  "output_i": "-16.07",
  "output_tp": "-1.50",
  "output_lra": "2.50",
  "output_thresh": "-26.11",
  "normalization_type": "dynamic",
  "target_offset": "0.07"
}
```

### Loudnorm JSON — decoded final MP4 AAC (verification)

`input_i` and `input_tp` below are the measured delivered AAC values.

```json
{
  "input_i": "-16.27",
  "input_tp": "-1.41",
  "input_lra": "4.60",
  "input_thresh": "-26.31",
  "output_i": "-16.15",
  "output_tp": "-1.50",
  "output_lra": "2.50",
  "output_thresh": "-26.24",
  "normalization_type": "dynamic",
  "target_offset": "0.15"
}
```

### Final `ffprobe` summary

Full machine-readable output is committed at `audio/final_ffprobe.json`.

```json
{
  "video": {"codec_name":"h264","width":1920,"height":1080,"r_frame_rate":"30/1","nb_frames":"1800","duration":"60.000000"},
  "audio": {"codec_name":"aac","sample_rate":"48000","channels":2,"duration":"60.000000"},
  "format": {"duration":"60.000000","size":"35395888"}
}
```

Human review disclosure: **no human listened**; verification is numeric and structural only.
