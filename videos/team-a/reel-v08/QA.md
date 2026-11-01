# WARD TEN — delivery and QA

## Deliverables

| | Vertical master | Landscape reframe |
|---|---:|---:|
| File | `video.mp4` | `video-landscape.mp4` |
| Duration / decoded frames | 60.000 s / 1,800 | 60.000 s / 1,800 |
| Dimensions / display aspect | 1080×1920 / 9:16 | 1920×1080 / 16:9 |
| Frame rate / pixels | 30/1 fps, yuv420p, square pixels | 30/1 fps, yuv420p, square pixels |
| Video | H.264 High, **894,222 bit/s** | H.264 High, **688,250 bit/s** |
| Audio | AAC LC, 48 kHz stereo, **192,827 bit/s** | AAC LC, 48 kHz stereo, **192,827 bit/s** |
| Overall container bitrate | 1,096,056 bit/s | 890,116 bit/s |
| Integrated loudness | **−16.06 LUFS** | **−16.06 LUFS** |
| True peak | **−1.87 dBTP** | **−1.87 dBTP** |
| Size | 8,220,423 bytes | 6,675,877 bytes |
| SHA-256 | `dc76f5fb7204316f2d920831b938dc896631da50970f08e3a35b2143f351c70b` | `b15e0135bc07246ee2d2ded2a94e4a43b842884cd2e0cf7bf5b3da10aedff4df` |

Both together are 14,896,300 bytes. Their H.264 and AAC streams begin at 0.000 s and each lasts 60.000 s. `moov` precedes `mdat` in each MP4 (faststart). Landscape is a real crop/reframe of the central 1080-square story area, not a shrunken portrait: it adds original sidebars, recreates the 02:17 time marker, and burns the same caption schedule in landscape-safe positioning. After the working checkpoint, its aspect metadata was explicitly set to square pixels/16:9 via lossless stream copy; the extracted H.264 video packet hash was unchanged. The two final AAC packet streams are byte-identical when demuxed to ADTS: `d30614744b2a680a88a8c38d49119747dd2513e01299d7df9b5918c5ea8d935a`.

## Evidence and checks

- `qa/*.full-ffprobe.txt` and `*.frames.txt` are actual probes and decoded-frame counts. Files are 30 fps, 1,800 frames, with the codec/pixel/audio details above. Aspect ratio is explicit in both final exports.
- `qa/*.loudnorm-json.txt` records the **input** measurements, not the filter's predicted output: −16.06 LUFS and −1.87 dBTP for each finished AAC soundtrack. The `-v error` specification command produces empty `*.spec-loudnorm.txt` because FFmpeg suppresses its info-level summary; the separate info-level JSON is the meaningful result.
- Each complete file was scanned with `blackdetect` at pixel thresholds 0.10 and 0.02, picture threshold 0.98, and duration 0.5 s; `freezedetect` at −60 dB for 0.5 s; and `silencedetect` at −50 dB for 0.5 s. **No events** were reported. Decode-to-null produced zero error bytes. This does not mean the narration contains no pauses: a continuous drone fills the intentional voice gap.
- Thirty planned shots repeat 54/60/66 frames ten times: **1.8 / 2.0 / 2.2 s**, **2.0 s average**. `qa/timing.json` checks all 29 expected boundaries in the decoded portrait: the numbered header patch's strongest adjacent-frame change in a local window lands on each expected frame. This is a structural indicator, not a judgment that every transition feels distinct.
- The committed 48 kHz stereo 16-bit FLAC narration is **59.222208 s**, 1,789,587 bytes; first timed word starts 0.257 s, last ends 58.229 s. The script and all **130** word-event tokens match. In the original synthesis, 20 sentence-gap centers trimmed to fit were verified near digital silence, with loudest RMS −90.4 dBFS; speech was not time-stretched. The gap between the last pre-reveal and first post-reveal word boundaries is **3.100 s**; “discharging” begins at 46.859 s, about 78.1% of the film.
- `captions.srt` has **44** cues, all **2–5 words**; start 0.257 s, end 59.840 s. Durations range 0.719–2.776 s, mean 1.271 s. All 130 words are accounted for; the maximum SRT-to-word boundary overhang is 0.006 s, under one 30 fps frame. Nominal caption font is 72–94 px and max measured line width is 866.41 px, within the 875 px design width. Portrait and landscape ASS are produced from the same cue/word list; progressive word highlighting and their separately positioned burns are visible in extracted frames.
- Separate pre-mix loudness measurements: narration −19.40 LUFS, raw drone −28.86 LUFS, raw Foley −40.71 LUFS. Drone gain −0.54 dB sets it **10.0 LU below narration** before global normalization; Foley gain is +6.31 dB. Full pass and AAC remeasurement data are in `qa/audio-metrics.json`. The final mix is subsequently normalized as a whole; these are stem measurements, not a perceptual intelligibility test.
- Independent committed-stem-to-final-mix analysis is reproducible with `./audit_narration.py --out /tmp/ward-ten-voice-audit.json`. Decoding both to 16 kHz mono and searching ±0.5 s, the **zero-lag Pearson correlation is 0.869829**, and the peak occurs at **0 samples / 0.000 s**. A least-squares fit of the narration to the complete mix leaves an aggregate residual **4.926 dB below the fitted voice** (5.685 dB below across timed word spans). The residual includes music, effects, AAC error and nonlinear gain; this is an estimate, not isolated-stem or perceptual proof. Both MP4s have identical demuxed AAC.
- Caption highlighting is **measured per word**, not apportioned by word length: `captions.py` creates ASS `\\k` intervals from adjacent committed Edge word starts, quantized to centiseconds; the final word extends to the cue end. Regenerated portrait and landscape dialogue entries match. All **130/130** word spans fit their 44 ASS cues within one frame (worst overhang 10.542 ms); all **130/130** logical karaoke starts are within one frame of the telemetry (worst 14.458 ms). When the first eligible 30 fps frame is *calculated* from the ASS start, **128/130** are within one frame; the two others are 38.667 ms and 34.542 ms late. Those frame timings are calculations, not observed pixel changes, and the telemetry is not a human phonetic alignment. Per-word values and SHA-256 hashes for the actual FLAC, telemetry, captions, script and outputs are in `qa/voice-mix-audit.json`.
- Seven stills are actual decoded frames, losslessly PNG-optimized after extraction: `01-board.png` at 2.8 s, `02-observations.png` at 8.6 s, `03-call-log.png` at 12.8 s, `04-corridor.png` at 26.6 s, `05-doorway-bed.png` at 31.0 s, `06-discharge.png` at 47.3 s, and `07-landscape-call-log.png` at 12.8 s. They show the 10/10/11 discrepancy, perspective corridor and doorway bed, discharge, and landscape caption. `qa/SHA256SUMS` covers both masters, the stem and all seven.

## Reproduce the checks

From this directory, with FFmpeg/ffprobe, Python 3, NumPy and Pillow:

```bash
./verify.sh /tmp/ward-ten-qa
./check_timing.py --out /tmp/ward-ten-qa/timing.json
./audit_narration.py --out /tmp/ward-ten-qa/voice-mix-audit.json
sha256sum -c qa/SHA256SUMS
```

`./render.sh` rebuilds from the original picture/audio source and the committed offline narration stem. An independent copy of the source was rendered offline in `/tmp`; **both regenerated MP4s were byte-identical** to the delivered files on this machine (`qa/reproducibility.txt`). Tools used here: FFmpeg 7.1.5, Python 3.13.16, NumPy 2.3.5, Pillow 12.3.0. See `README.md` for setup and possible encoder-version differences. Intermediates were kept under `/tmp`; the two video files together are well below 128 MB.

## Creative provenance and self-review

The fictional narration, screen furniture, corridor/bed drawings, drone, bells and printer effects are original to v08. No reference footage, audio or story was incorporated. The Anton font by Vernon Adams and its SIL Open Font License 1.1 are bundled under `assets/`. The v07 reference study and v08 script were committed before any v08 images; however, the v08-specific design addendum in `reference-notes.md` was written **after candidate PNGs and a six-second picture test**, though before the final exports. This missed the stricter requested ordering for v08-specific notes. The initial working video masters were committed and pushed at `f3a26c0cb85c1b694fafd24be14fd14d62644196` before final verification and the lossless landscape metadata polish.

**No human listened to the narration or mix, and no human continuously watched either completed film. Verification is numeric and structural, plus inspection of the extracted stills; it does not certify intelligibility, performance, subjective loudness, emotional impact, or timing feel.** A human should review both versions on speakers and a phone before publication.

The UI count mismatch and one-point corridor are clearly present in the inspected stills. Weaknesses: several adjacent shots reuse the same central interface, so the landscape reframe sometimes reads as a zoom reset rather than a strongly different composition; the landscape caption sits close to the log footer, and the empty-bed label is near its inset border. The voice delivery, call-bell audibility and small-screen legibility remain unverified by human playback. This is fiction, not clinical guidance; nothing was published to YouTube or another public video platform.
