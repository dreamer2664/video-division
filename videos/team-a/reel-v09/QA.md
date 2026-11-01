# PERFECT TIME — v09 quality and provenance record

## Review status

The two deliverables are 60-second fiction films, not recordings of an actual service. Automated/structural checks and four extracted frames were reviewed as described below. **No one listened to the audio or continuously watched either film during this production.** These checks do not establish acting quality, intelligibility, subjective visual rhythm, full-frame safety on every device, or phonetic alignment. The landscape caption in the inspected 24.7 s still sits close to the timeline marker; this is a visual crowding risk, not a claim that every frame was reviewed.

## Masters

| File | Dimensions / duration | Video / audio | Bytes | SHA-256 |
|---|---|---|---:|---|
| `video.mp4` | 1080×1920, 9:16, 60.000 s, 1,800 frames, 30 fps | H.264 High yuv420p, 781,973 bit/s; AAC-LC 48 kHz stereo, 192,969 bit/s | 7,379,848 | `efba316fb9d0dd315aa21b0bc8e42bcf765a423c3fc1c4d88c6713757c80fb29` |
| `video-landscape.mp4` | 1920×1080, square pixels / 16:9, 60.000 s, 1,800 frames, 30 fps | H.264 High yuv420p, 523,274 bit/s; AAC-LC 48 kHz stereo, 192,969 bit/s | 5,439,647 | `9205e6e3d6c49fa0320cdc07b8176d8500096cce9f60fbe6fedd85a11bba2f41` |

Both have faststart (`moov` before `mdat`) and identical demuxed AAC bitstreams: ADTS SHA-256 `fedf1be3b62c16b089de1c5fdd14a0421f1da026dc41823950f98fed2cc8e644`. `SHA256SUMS` covers the masters, narration, telemetry, production scripts, QA summaries and evidence stills.

## Audio and independent narration audit

- The original committed narration is `assets/narration.flac`, 58.040417 s; SHA-256 `d69977bd0d8d2f82b537c191da719fda0e568dbb3754ca4dbf034a6b88b2cb21`. Its 125 service-provided word events are in `assets/word_timings.json`, SHA-256 `530a6afec82962c26d789481bb51cb01ed6f598d2f9504c6183fe56948c39f47`. The speech is generated with `en-US-ChristopherNeural`, rate −12%, pitch −4 Hz. Measured speech after “calls” pauses 3.097 s before the next speech begins.
- `qa/audio-metrics.json` records isolated-stem LUFS and mixing. Before the global mix normalization the voice is **10.00 LU above the synthesized music**, using the measured integrated stem values and applied gain. The finished AAC measures **−16.10 LUFS integrated and −1.92 dBTP**; the original drone and relay/queue Foley are synthesized, not taken from references.
- Re-run `python3 audit_narration.py --out qa/voice-mix-audit.json`. It decodes the committed voice and the delivered mix to aligned mono 16 kHz PCM. Pearson correlation is **0.877453 at zero lag**; the strongest normalized correlation in the ±0.5 s search occurs at **0 samples**. A least-squares scaled source estimate exceeds the residual by **5.246 dB over 60 s** and **6.386 dB within timed word spans**. This residual contains music, Foley, AAC error and any nonlinear gain: it is **not** an isolated accompaniment stem, a perceptual intelligibility test, or proof that each syllable is audible. The full method, inputs, hashes and measurements are committed in `qa/voice-mix-audit.json`.

## Captions, cuts and timing

- `captions.srt` and the burned ASS captions are generated from the committed word telemetry, not character-count or evenly distributed timing. There are **42 cues**, each **2–5 words**, covering 125 words that match the script. Portrait and landscape ASS dialogue is identical, with different positioning.
- For each cue the ASS instant-karaoke tag lengths run from each service-measured word start to the next, rounded to centiseconds; the final tag extends to cue end. All **125/125 word spans** fit the ASS cue intervals within one 30 fps frame (largest overhang **9.583 ms**); **125/125 logical highlight starts** are within one frame of service word starts (maximum **9.917 ms**); and **125/125 calculated first eligible 30 fps frame times** are within one frame (maximum **29.000 ms**). These frame times are **calculated from ASS timestamps**, not established by pixel-difference measurement or human phonetic listening. The full per-word audit is in `qa/voice-mix-audit.json`.
- The 30-shot plan repeats 54/60/66 frames (1.8/2.0/2.2 s), with a 2.0 s mean. `qa/timing.json` records **29/29** scheduled portrait cut boundaries matched against peaks in the decoded header region; it also records the SRT cue check and the identical AAC and faststart checks. This is a cut-timing test, not a subjective pacing review.

## Detection and still inspection

`./verify.sh <output-directory>` decoded both complete masters and saved raw FFprobe, FFmpeg and hash logs under `qa/`. No decode errors or events were reported by the configured detectors: two `blackdetect` passes (minimum 0.5 s, picture fraction 0.98, pixel thresholds 0.10 and 0.02), `freezedetect` (−60 dB, minimum 0.5 s) and `silencedetect` (−50 dB, minimum 0.5 s). Absence of events depends on these settings and does not rule out other visual/audio defects. The spec-style `ffmpeg -v error ... loudnorm=print_format=summary` suppresses informational output; the useful loudness JSON was captured separately at info level in `qa/*.loudnorm-json.txt`.

The following losslessly optimized PNGs were extracted from the final delivered MP4s and visually inspected, not recreated from source artwork:

- `stills/01-call-centre-depth.png`: portrait, 0.8 s; perspective floor and desks.
- `stills/02-queue-one.png`: portrait, 3.0 s; waiting-one queue and caption.
- `stills/03-measuring-callers.png`: portrait, 43.6 s; the AHT reveal.
- `stills/04-landscape-record.png`: landscape, 24.7 s; FINISHED/LIVE record and caption/timeline spacing.

## Source order and rebuild

The original v09 study and script/shot plan were pushed at `32c0ba48bda7e02934d64203baefcdd279106687`, **before any candidate v09 production imagery**. The reference notes explicitly adapt the earlier v07 study rather than claiming a new watch/listen. The committed narration, telemetry and font followed at `92e5316fade0c2738aef8d319a482dd94b4ff09e`; production source was pushed before visual tests. Original picture/source refinements and output checkpoints followed. No reference audio or reference frames are used in or committed with this production.

From an isolated copy containing the source files and `assets/` but no masters, `./render.sh` rebuilt both files **byte-identically** to the hashes above, without network access. Test environment: FFmpeg/ffprobe `7.1.5-0+deb13u1` with libx264/libass/drawtext, Python 3.13.16, NumPy 2.3.5, Pillow 12.3.0 and SciPy 1.17.1. `requirements.txt` and `README.md` contain setup and verification commands. Different encoder/library versions may produce different bytes.

## Local workspace housekeeping

To stay below the workspace size cap while retaining prior films and source, duplicate immutable files in the old v02 scratch copies were replaced with workspace-internal links after byte comparison. Nine local v07 reference downloads/derived audio/contact sheets were removed from that checkout only after verifying their Git blob IDs against `main` and checking that the blobs exist locally. The v07 study notes, masters, source, branch and commit remain intact; those reference blobs are still in Git and on `main`. In that checkout, the omitted paths were marked `skip-worktree`; to restore them when capacity permits, run `git update-index --no-skip-worktree -- <paths>` followed by `git checkout -- <paths>`. The omitted paths are the three `references/*.mp4`, three `references/audio/*.m4a` and three `references/sheets/*.png` files listed in the repository. Restoring them will increase workspace usage by about 9.7 MB.
