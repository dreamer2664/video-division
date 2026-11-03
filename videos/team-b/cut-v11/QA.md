# QA — CUT V11: TWO LIGHTS (audio-only balance revision)

## Change scope

V11 addresses the single remaining audio-balance rejection from lux on v10. The original delivered cut measured −16.27 LUFS / −1.41 dBTP and passed the loudness/peak gate, but source-based voice-over-bed margin in the opening 0–10 s window was **+5.872 dB** against the house target of +8 to +12 dB. The 30–40 s window was also slightly under the floor at +7.383 dB.

**Correction:** attenuate the bed contribution by **2.3 dB**, preserving the narration stem, timing, and all video frames. This gives the opening window a measured **+8.172 dB** voice/bed margin and places all six 10-second speech windows within the target. The treatment is global to the bed, not a voice regenerate or picture edit. No ElevenLabs request was made.

## Source-based voice/bed margin ledger

Method: direct RMS ratio of committed isolated narration and bed FLAC stems, sampled only over the union of WordBoundary intervals; each telemetry time is shifted +0.300 s to match the placed narration stem. Six adjacent 10-second windows. The v11 bed file itself is re-read after FLAC encoding for the after measurement. This is a source-stem ratio, not a claim of subjective intelligibility or a separated-bed measurement from AAC.

| Speech window | V10 voice/bed margin | V11 voice/bed margin | Target |
|---|---:|---:|---:|
| 0–10 s (opening) | +5.872 dB | **+8.172 dB** | +8 to +12 dB |
| 10–20 s | +8.710 dB | +11.010 dB | +8 to +12 dB |
| 20–30 s | +8.789 dB | +11.089 dB | +8 to +12 dB |
| 30–40 s | +7.383 dB | +9.683 dB | +8 to +12 dB |
| 40–50 s | +9.074 dB | +11.374 dB | +8 to +12 dB |
| 50–60 s | +8.651 dB | +10.951 dB | +8 to +12 dB |
| **All active speech** | +7.814 dB | +10.114 dB | +8 to +12 dB |

All six ten-second bins and the active-speech aggregate now fall inside the requested range. Exact values, stem/source hashes, time-mask definition and applied gain are recorded in `audio/voice_bed_balance_ledger.json`.

## Delivered loudness / true peak

Decoded final AAC measured with FFmpeg `loudnorm` analysis:

- Integrated loudness: **−16.28 LUFS** (target −16.0 ±0.5 LUFS: PASS).
- True peak: **−1.38 dBTP** (ceiling −1.0 dBTP: PASS).
- Stream: 48 kHz, stereo AAC; 60.000000 s.
- Two-pass analysis, gain mapping, final AAC measurement and `ffprobe` output are saved under `audio/`.

## Picture and captions unchanged

- Input v10 MP4 SHA-256: `e093a55f941b72fc694b3f9c50bf3ce559307cc658c0f2161ed2ebfaad589403`.
- Output v11 MP4 SHA-256: `9dca49ae6e16ac17fff242548a79a70a702a506e6174f27d74eb1ce9cb4a76ee`.
- The H.264 video stream is stream-copied; decoded `framemd5` comparison: **1,800 / 1,800 identical frame hashes**. Frame-hash-list SHA-256: recorded in `audio/frame_hashes.json`.
- Captions remain burned into those identical frames. The source `timing/captions_locked.json` hash is recorded unchanged in the ledger. No frame rendering, crop, grade, timing, caption, or video-encode step was run.

## Reproduction and files

Run `python3 videos/team-b/cut-v11/build_audio_v11.py`. The script reads only the committed v10 video/audio stems/pre-master/timing, attenuates the fitted bed contribution by 2.3 dB, performs two-pass `loudnorm=I=-16:TP=-1.5:LRA=11`, encodes AAC, and remuxes with `-c:v copy`. It refuses to replace the output unless audio and structural gates pass and every video-frame hash matches.

Key evidence:
- `audio/voice_bed_balance_ledger.json` — before/after margins, stem/source hashes, chosen gain and unchanged-picture record.
- `audio/gain_mapping.json` — v11 audio input/output mapping and two-pass loudnorm metadata.
- `audio/final_loudnorm_analysis.json` — measured final AAC integrated loudness and true peak.
- `audio/final_ffprobe.json` — delivered stream details.
- `audio/frame_hashes.json` — bit-identical decoded picture evidence.
- `video.mp4` — v11 output.

No human listened; reported acceptance is based on source-stem RMS, loudnorm analysis, ffprobe and decoded video-frame hashes.
