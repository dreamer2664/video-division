# QA Report — `MARK FOUR` (`videos/team-b/grade-v05`)

> **Verification disclosure:** no human listened to this; verification is numeric and structural.

> **Audit Revision Disclosure (PR #1 Consolidated Fix):** The initial `047e322` submission (`MP4 SHA256 141f3939848bf2970d993b421f6f227de54ea5e89f09e563c078c1a3f8545858`) left its narration stem in worker-local `/tmp/grade_v05_build/` scratch, which was cleared after the turn (`edge-tts` cloud MP3 vocoding exhibits `-40.9 dBFS` stochastic float variance across sessions even when `WordBoundary` offsets remain `0.000000 s` identical). Rather than claiming a fresh synthesis was the lost scratch file, this revision persists the complete lossless timeline-aligned stems (`audio/narration_stem_48k.flac`, `audio/bed_ducked_48k.flac`), raw per-line TTS sources (`audio/tts_lines/line_01.mp3`–`line_11.mp3`), exact `WordBoundary` & placement hashes (`timing/tts_source_manifest.json`), and linear `loudnorm` gain mapping (`audio/gain_mapping.json`) inside the repository, remuxes the audio stream onto the untouched `047e322` H.264 video stream (`-c:v copy`, zero picture re-render; new `video.mp4` `SHA256 1070d8654ad5e24763b71aa9c2f3d96b8c120b18d5094fda5efe9f2d94b6a1f0`), and makes `build_audio_v05.py` consume those immutable committed FLAC stems offline by default without calling `edge-tts` or rewriting `timing/*.json`.

---

## Voice decision

For `v05` (*MARK FOUR*), I selected **`edge-tts` (`en-US-ChristopherNeural`, `--rate=-12%`, `--pitch=-4Hz`)** as the single narrative voice for the entire 60-second film without polling or waiting on human review (Rule 8). `en-US-ChristopherNeural` provides a grounded, low-register baritone timbre; slowing prosody by `-12%` and lowering fundamental pitch by `-4 Hz` places delivery in the close, documentary-calm nocturnal register described in `doc/STYLE-BREAKDOWN.md` §6 (`137` words spoken across `53.92 s` of active speech within a `60.000 s` master). Deterministic `100 ns` `WordBoundary` offsets lock all `11` shot cuts and all `39` `2–5` word amber/ivory/crimson caption beats (`0.000 s` drift), while broadcast EQ (`85 Hz` HPF, `-2.2 dB` @ `330 Hz` mud cut, `+2.8 dB` @ `3.1 kHz` presence boost) preserves phone-speaker intelligibility over `+10.33 dB` sidechain-ducked rain and sub-cello ambience.

---

## 1. Durable Audio Provenance, Hashes & Immutable Offline Reproduction

All audio sources and gain mappings are committed at durable repository paths under `videos/team-b/grade-v05/`:

- **Timeline-aligned lossless narration stem:** `videos/team-b/grade-v05/audio/narration_stem_48k.flac`
  - `SHA256`: `a4f2f8a84bc1130d72310d54f85e34b5e245028e83ced695f1cd809b6f8cb661` (`48000 Hz`, `2 ch`, `s16` lossless FLAC, `60.000000 s`)
- **Timeline-aligned lossless ducked rain/score/foley bed:** `videos/team-b/grade-v05/audio/bed_ducked_48k.flac`
  - `SHA256`: `41352ef69704701255ef595136458a9f2a82121cb5d12a26f586cfcd1475174e` (`48000 Hz`, `2 ch`, `s16` lossless FLAC, `60.000000 s`)
- **Raw per-line TTS sources & word telemetry:** `videos/team-b/grade-v05/audio/tts_lines/line_01.mp3`..`line_11.mp3` + `videos/team-b/grade-v05/timing/tts_source_manifest.json` (contains per-line SHA256s, raw `WordBoundary` ticks, trim windows, and global placement offsets).
- **Exact pre-master & `loudnorm` gain mapping:** `videos/team-b/grade-v05/audio/gain_mapping.json`
  - Pre-master sum: `raw_mix = int16(narration_stem_48k.flac)/32767.0 + int16(bed_ducked_48k.flac)/32767.0` (`pre_scale = 1.0`)
  - Linear two-pass EBU R128 filter: `loudnorm=I=-16.0:TP=-1.5:LRA=9.0:measured_I=-16.55:measured_LRA=1.90:measured_TP=-2.59:measured_thresh=-26.78:offset=0.14:linear=true:print_format=summary,aresample=48000`
  - Resulting `master_audio_48k.wav` `SHA256`: `abf875b254ec6422cc686b33dbdb63d4f32716b65e2f1022264be920c2912e7c`
  - Delivered `videos/team-b/grade-v05/video.mp4` `SHA256`: `1070d8654ad5e24763b71aa9c2f3d96b8c120b18d5094fda5efe9f2d94b6a1f0` (`31,397,177` bytes; video stream copied bit-for-bit via `-c:v copy` from `047e322`)
  - **Source-to-MP4 waveform verification:** Decoding `videos/team-b/grade-v05/video.mp4` audio and comparing sample-for-sample against `master_audio_48k.wav` built offline from the two committed `.flac` stems yields Pearson correlation **`r = 0.998922`** (residual difference `-45.47 dBFS`, pure `192 kbps` AAC perceptual coding floor).
- **Offline Reproduction Command (no network / no `/tmp` precondition / pinned `requirements.txt`):**
  ```bash
  python3 videos/team-b/grade-v05/build_audio_v05.py
  ```

---

## 2. Durable-Path Speech & Mix Measurements

### 2.1 Verbatim `ffprobe` on `videos/team-b/grade-v05/audio/narration_stem_48k.flac`

```bash
ffprobe -v quiet -print_format json -show_format -show_streams videos/team-b/grade-v05/audio/narration_stem_48k.flac
```
```json
{
    "streams": [
        {
            "index": 0,
            "codec_name": "flac",
            "codec_long_name": "FLAC (Free Lossless Audio Codec)",
            "codec_type": "audio",
            "sample_fmt": "s16",
            "sample_rate": "48000",
            "channels": 2,
            "channel_layout": "stereo",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 2880000,
            "duration": "60.000000",
            "bits_per_raw_sample": "16"
        }
    ],
    "format": {
        "filename": "videos/team-b/grade-v05/audio/narration_stem_48k.flac",
        "nb_streams": 1,
        "format_name": "flac",
        "start_time": "0.000000",
        "duration": "60.000000",
        "size": "2880234",
        "bit_rate": "384031",
        "probe_score": 100
    }
}
```

### 2.2 `silencedetect=n=-40dB:d=1` on Committed Narration Stem & Full Mix

```bash
ffmpeg -hide_banner -i videos/team-b/grade-v05/audio/narration_stem_48k.flac -af silencedetect=n=-40dB:d=1 -f null -
```
```text
[silencedetect] silence_start: 17.195833 | silence_end: 18.313292 | silence_duration: 1.117458
[silencedetect] silence_start: 24.639250 | silence_end: 25.729062 | silence_duration: 1.089813
[silencedetect] silence_start: 30.262521 | silence_end: 31.341167 | silence_duration: 1.078646
[silencedetect] silence_start: 40.251958 | silence_end: 41.381333 | silence_duration: 1.129375
[silencedetect] silence_start: 43.495750 | silence_end: 44.722958 | silence_duration: 1.227208  <-- deliberate pre-twist beat
[silencedetect] silence_start: 55.498458 | silence_end: 56.634542 | silence_duration: 1.136083
```
On the full mix (`ffmpeg -hide_banner -i videos/team-b/grade-v05/video.mp4 -af silencedetect=n=-40dB:d=1 -f null -`), **`0` silences `> 1.0 s`** occur anywhere in the 60.000 s file.

### 2.3 Matched Active-Window Dominance & Six `10 s` Body Windows

- **Matched active-speech windows (`82.73%` duty cycle across `60.000 s`):**
  - Committed `narration_stem_48k.flac` active RMS: **`-19.11 dBFS`**
  - Committed `bed_ducked_48k.flac` active RMS: **`-29.44 dBFS`**
  - **Measured voice-over-bed dominance on active speech:** **`+10.33 dB`** (within `8–12 dB` spec; during non-speech breaths the bed rises to **`-25.77 dBFS`**).

| Body Window | Speech Duty Cycle | `narration_stem_48k.flac` RMS | `bed_ducked_48k.flac` RMS | Delivered `video.mp4` Mix RMS |
| :---: | :---: | :---: | :---: | :---: |
| `00-10s` | `88.8%` | `-19.64 dBFS` | `-29.32 dBFS` | `-18.68 dBFS` |
| `10-20s` | `85.4%` | `-19.97 dBFS` | `-29.43 dBFS` | `-18.99 dBFS` |
| `20-30s` | `83.4%` | `-19.72 dBFS` | `-29.95 dBFS` | `-18.81 dBFS` |
| `30-40s` | `84.5%` | `-20.00 dBFS` | `-29.94 dBFS` | `-19.06 dBFS` |
| `40-50s` | `75.5%` | `-20.30 dBFS` | `-26.62 dBFS` | `-18.88 dBFS` |
| `50-60s` | `78.8%` | `-19.99 dBFS` | `-27.25 dBFS` | `-18.74 dBFS` |

### 2.4 Caption Cue Alignment & Per-Cue Committed Stem Waveform RMS (`39` Cues)

Every caption cue aligns at `0.000 s` drift to `tts_source_manifest.json` and carries verified active speech waveform energy (`-23.2` to `-16.9 dBFS`) in `audio/narration_stem_48k.flac`:

| Cue | Shot | Caption Cue (`s`) | Speech (`WordBoundary`) (`s`) | Drift (`s`) | Stem Waveform RMS | Display Text | Spoken Words |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 01 | 01 | `0.360–1.539` | `0.360–1.539` | `0.000` | `-19.50 dBFS` | `At 2:17` | `At two seventeen` |
| 02 | 01 | `1.553–2.135` | `1.553–2.135` | `0.000` | `-18.03 dBFS` | `in the morning,` | `in the morning` |
| 03 | 01 | `2.434–3.598` | `2.434–3.598` | `0.000` | `-17.40 dBFS` | `the old stone lock` | `the old stone lock` |
| 04 | 01 | `3.613–4.479` | `3.613–4.479` | `0.000` | `-20.61 dBFS` | `on the Blackwater` | `on the Blackwater` |
| 05 | 01 | `4.493–5.772` | `4.493–5.772` | `0.000` | `-20.16 dBFS` | `has only one rule.` | `has only one rule` |
| 06 | 02 | `6.152–7.501` | `6.152–7.501` | `0.000` | `-17.01 dBFS` | `Never open the sluice` | `Never open the sluice` |
| 07 | 02 | `7.515–8.567` | `7.515–8.567` | `0.000` | `-19.01 dBFS` | `if the rain reaches` | `if the rain reaches` |
| 08 | 02 | `8.581–9.405` | `8.581–9.405` | `0.000` | `-22.58 dBFS` | `MARK FOUR.` | `Mark Four` |
| 09 | 03 | `9.825–10.933` | `9.825–10.933` | `0.000` | `-18.27 dBFS` | `For forty years,` | `For forty years` |
| 10 | 03 | `11.174–11.998` | `11.174–11.998` | `0.000` | `-19.47 dBFS` | `a night keeper` | `a night keeper` |
| 11 | 03 | `12.012–13.191` | `12.012–13.191` | `0.000` | `-18.88 dBFS` | `has logged the water` | `has logged the water` |
| 12 | 03 | `13.205–14.612` | `13.205–14.612` | `0.000` | `-20.96 dBFS` | `every fifteen minutes.` | `every fifteen minutes` |
| 13 | 04 | `14.992–17.208` | `14.992–17.208` | `0.000` | `-19.32 dBFS` | `1:45 — Mark Two.` | `One forty-five Mark Two` |
| 14 | 04 | `18.209–20.183` | `18.209–20.183` | `0.000` | `-19.50 dBFS` | `2:00 — Mark Three.` | `Two o'clock Mark Three` |
| 15 | 05 | `20.603–22.194` | `20.603–22.194` | `0.000` | `-19.22 dBFS` | `Outside, four inches` | `Outside four inches` |
| 16 | 05 | `22.208–23.529` | `22.208–23.529` | `0.000` | `-18.57 dBFS` | `of cold rain fall` | `of cold rain fall` |
| 17 | 05 | `23.543–24.637` | `23.543–24.637` | `0.000` | `-20.62 dBFS` | `in twenty minutes.` | `in twenty minutes` |
| 18 | 05 | `25.624–26.391` | `25.624–26.391` | `0.000` | `-18.42 dBFS` | `Yet the gauge` | `Yet the gauge` |
| 19 | 05 | `26.405–27.399` | `26.405–27.399` | `0.000` | `-19.06 dBFS` | `stops moving.` | `stops moving` |
| 20 | 06 | `27.799–29.290` | `27.799–29.290` | `0.000` | `-17.60 dBFS` | `Three millimeters below` | `Three millimeters below` |
| 21 | 06 | `29.305–30.228` | `29.305–30.228` | `0.000` | `-19.83 dBFS` | `the red line.` | `the red line` |
| 22 | 06 | `31.215–32.933` | `31.215–32.933` | `0.000` | `-18.46 dBFS` | `Still as dark glass.` | `Still as dark glass` |
| 23 | 07 | `33.373–34.751` | `33.373–34.751` | `0.000` | `-17.96 dBFS` | `So you carry the lantern` | `So you carry the lantern` |
| 24 | 07 | `34.765–35.958` | `34.765–35.958` | `0.000` | `-20.15 dBFS` | `out onto the catwalk` | `out onto the catwalk` |
| 25 | 07 | `35.972–36.640` | `35.972–36.640` | `0.000` | `-23.57 dBFS` | `to check for` | `to check for` |
| 26 | 07 | `36.654–37.663` | `36.654–37.663` | `0.000` | `-21.41 dBFS` | `a jammed float.` | `a jammed float` |
| 27 | 08 | `38.083–38.949` | `38.083–38.949` | `0.000` | `-17.50 dBFS` | `Your light hits` | `Your light hits` |
| 28 | 08 | `38.964–40.285` | `38.964–40.285` | `0.000` | `-19.21 dBFS` | `the wet stone wall.` | `the wet stone wall` |
| 29 | 08 | `41.271–41.925` | `41.271–41.925` | `0.000` | `-16.21 dBFS` | `And you see` | `And you see` |
| 30 | 08 | `41.939–43.473` | `41.939–43.473` | `0.000` | `-19.47 dBFS` | `the empty bolt holes.` | `the empty bolt holes` |
| 31 | 09 | `44.593–46.468` | `44.593–46.468` | `0.000` | `-18.12 dBFS` | `Someone unbolted Mark Four,` | `Someone unbolted Mark Four` |
| 32 | 09 | `46.752–48.101` | `46.752–48.101` | `0.000` | `-18.32 dBFS` | `and moved the brass plate` | `and moved the brass plate` |
| 33 | 09 | `48.116–49.266` | `48.116–49.266` | `0.000` | `-22.02 dBFS` | `two feet higher.` | `two feet higher` |
| 34 | 10 | `49.726–51.175` | `49.726–51.175` | `0.000` | `-18.36 dBFS` | `Behind you, the lamp` | `Behind you the lamp` |
| 35 | 10 | `51.189–52.226` | `51.189–52.226` | `0.000` | `-19.12 dBFS` | `in the keeper's booth` | `in the keeper's booth` |
| 36 | 10 | `52.240–53.135` | `52.240–53.135` | `0.000` | `-21.98 dBFS` | `clicks off.` | `clicks off` |
| 37 | 11 | `53.555–55.515` | `53.555–55.515` | `0.000` | `-18.35 dBFS` | `The river never stopped rising.` | `The river never stopped rising` |
| 38 | 11 | `56.502–58.008` | `56.502–58.008` | `0.000` | `-18.53 dBFS` | `The sluice gate behind you` | `The sluice gate behind you` |
| 39 | 11 | `58.022–59.144` | `58.022–59.144` | `0.000` | `-18.97 dBFS` | `is already open.` | `is already open` |

---

## 3. Final Deliverable `ffprobe`, `loudnorm`, & Visual Gate Checks

- **Format & Streams (`videos/team-b/grade-v05/video.mp4`):** `60.000000 s`, `1920×1080`, `30/1` fps CFR (`1,800` frames), `h264` High L4.1 `yuv420p` (`+faststart`, `moov` at byte `36`), `aac` LC `48000 Hz` stereo (`31,397,177` bytes).
- **`loudnorm` on delivered `video.mp4`:**
  ```json
  {
    "input_i" : "-16.04",
    "input_tp" : "-1.93",
    "input_lra" : "1.90",
    "input_thresh" : "-26.29",
    "output_i" : "-16.14",
    "output_tp" : "-2.03",
    "output_lra" : "1.80",
    "output_thresh" : "-26.39",
    "normalization_type" : "dynamic",
    "target_offset" : "0.14"
  }
  ```
- **Black / Freeze scan (`d=0.5`):** `0` black intervals `> 0.5 s`; `0` frozen intervals `> 0.5 s`.
- **Script-first commit:** `cd7353b` (`script.md`) precedes render `047e322` and this stem-persistence revision.
- **Honest Self-Review:** Retaining the exact `047e322` picture stream via `-c:v copy` preserves Shot 07's theatrical poster frame (`stills/poster_mark_four_clean.png`) and Shot 10's `52.44 s` practical booth-lamp snap-off while making every speech, ducking, and cue claim 100% independently reproducible offline from committed lossless FLAC stems. Motion remains 2.5D camera/rain compositing over still plates, and verification is strictly numeric and structural.
