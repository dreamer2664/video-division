# QA Report — `MARK FOUR` (`videos/team-b/grade-v05`)

> **Verification disclosure:** no human listened to this; verification is numeric and structural.

---

## Voice decision

For `v05` (*MARK FOUR*), I selected **`edge-tts` (`en-US-ChristopherNeural`, `--rate=-12%`, `--pitch=-4Hz`)** as the single narrative voice for the entire 60-second film without polling or waiting on human review (Rule 8). `en-US-ChristopherNeural` provides a grounded, low-register baritone timbre that avoids commercial-announcer brightness; slowing the prosody by `-12%` and lowering fundamental pitch by `-4 Hz` places the delivery squarely in the close, documentary-calm nocturnal register described in `doc/STYLE-BREAKDOWN.md` §6 (`137` words spoken across `53.92 s` of active speech within a `60.000 s` master). Critically, `edge-tts` streams deterministic `100 ns` `WordBoundary` offsets alongside the neural waveform, enabling every shot cut (`11` shots) and every `2–5` word amber/ivory/crimson caption beat (`39` cues) to be locked to real measured synthesiser timings before a single frame was rendered, while broadcast EQ (`85 Hz` HPF, `-2.2 dB` @ `330 Hz` mud cut, `+2.8 dB` @ `3.1 kHz` presence boost) ensures clear consonant intelligibility on small phone speakers over `+10.33 dB` sidechain-ducked rain and sub-cello ambience.

---

## 1. Acceptance Checklist (`specs/60s-video.md` & Wave 2 Brief)

| Requirement | Target | Measured Result | Status |
| :--- | :--- | :--- | :---: |
| **Duration** | `60.0 s ± 2.0 s` (`58.0–62.0 s`) | `60.000000 s` (`1,800` frames @ `30/1` fps) | PASS |
| **Resolution & Aspect** | `1920×1080` (`16:9` *KELVIN* widescreen) | `1920×1080` (`16:9`, progressive) | PASS |
| **Frame Rate** | `30 fps` constant | `r_frame_rate = 30/1`, `avg_frame_rate = 30/1` | PASS |
| **Video Codec / Pixel Format** | H.264, `yuv420p`, `+faststart` | `h264` (High L4.1), `yuv420p`, `moov` at byte `36` | PASS |
| **Audio Codec / Sample Rate** | AAC `48 kHz` stereo | `aac` (LC), `48000 Hz`, `2` channels (`stereo`) | PASS |
| **Integrated Loudness** | `-16 LUFS ± 0.5` | `-16.04 LUFS` (`loudnorm` JSON on final MP4) | PASS |
| **True Peak** | `≤ -1.0 dBTP` | `-1.65 dBTP` (`0.65 dB` safety margin) | PASS |
| **Voice-to-Bed Ducking** | Music/rain ducked `8–12 dB` under speech | `+10.33 dB` active RMS speech-to-bed margin | PASS |
| **Black / Frozen Frames** | None `> 0.5 s` | `0` black `> 0.5 s`; `0` frozen `> 0.5 s` | PASS |
| **Script Locked First** | Synthesised, timed & committed before render | Commit `cd7353b` (`script.md`) precedes render | PASS |
| **Extracted Stills** | `≥ 3` stills in `stills/` | `6` PNG stills (5 captioned + 1 clean poster frame) | PASS |
| **Workspace Snapshot Cap** | `/home/user` `< 128 MB` (intermediates in `/tmp`) | `67 MB` pre-commit (`< 100 MB` post-commit) | PASS |

---

## 2. Numeric Speech Verification

### 2.1 Verbatim `ffprobe` on Isolated Narration Stem (`/tmp/grade_v05_build/narration/narration_stem_48k.wav`)

```json
{
    "streams": [
        {
            "index": 0,
            "codec_name": "pcm_s16le",
            "codec_long_name": "PCM signed 16-bit little-endian",
            "codec_type": "audio",
            "codec_tag_string": "[1][0][0][0]",
            "codec_tag": "0x0001",
            "sample_fmt": "s16",
            "sample_rate": "48000",
            "channels": 2,
            "bits_per_sample": 16,
            "initial_padding": 0,
            "r_frame_rate": "0/0",
            "avg_frame_rate": "0/0",
            "time_base": "1/48000",
            "duration_ts": 2880000,
            "duration": "60.000000",
            "bit_rate": "1536000"
        }
    ],
    "format": {
        "filename": "/tmp/grade_v05_build/narration/narration_stem_48k.wav",
        "nb_streams": 1,
        "format_name": "wav",
        "format_long_name": "WAV / WAVE (Waveform Audio)",
        "duration": "60.000000",
        "size": "11520044",
        "bit_rate": "1536005",
        "probe_score": 99
    }
}
```

### 2.2 `silencedetect=n=-40dB:d=1` Across Full Mix & Isolated Voice Stem

- **Full mix (`videos/team-b/grade-v05/video.mp4`):**
  ```text
  $ ffmpeg -hide_banner -i videos/team-b/grade-v05/video.mp4 -af silencedetect=n=-40dB:d=1 -f null -
  (0 silence intervals > 1.0 s below -40 dB; longest sub--40 dB span = 0.000 s)
  ```
- **Isolated voice stem (`narration_stem_48k.wav`, verifying spoken cadence has no dead hole swallowing the middle of the film):**
  ```text
  [silencedetect] silence_start: 17.195833 | silence_end: 18.313292 | silence_duration: 1.117458  (clause breath between '1:45 — Mark Two.' and '2:00 — Mark Three.')
  [silencedetect] silence_start: 24.639250 | silence_end: 25.730771 | silence_duration: 1.091521  (sentence breath before 'Yet the gauge stops moving.')
  [silencedetect] silence_start: 30.262521 | silence_end: 31.341167 | silence_duration: 1.078646  (dramatic beat before 'Still as dark glass.')
  [silencedetect] silence_start: 40.245396 | silence_end: 41.381333 | silence_duration: 1.135938  (lantern reveal beat before 'And you see the empty bolt holes.')
  [silencedetect] silence_start: 43.495750 | silence_end: 44.722958 | silence_duration: 1.227208  (DELIBERATE PRE-TWIST PAUSE before 'Someone unbolted Mark Four...')
  [silencedetect] silence_start: 55.498458 | silence_end: 56.634542 | silence_duration: 1.136083  (final landing breath before 'The sluice gate behind you is already open.')
  ```
  Speech begins at `0.360 s` and ends at `59.144 s`; the longest pause anywhere in the solo voice track is **`1.227 s`** right at the ~73% narrative turn (`43.50 s–44.72 s`), filled on the master soundtrack by rain and a double sub-bass heartbeat pulse.

### 2.3 Caption Cue Times vs. Speech Segment (`WordBoundary`) Alignment

All `39` caption beats (`2–5` words each, `Inter Display Bold 58 px`, ivory `#F2F5FA` + amber `#F5C84B` + crimson `#E8453C` on dark pill `#05080F`) are generated directly from `edge-tts` `WordBoundary` telemetry (`0.000 s` drift):

| Cue | Shot | Caption Cue (`s`) | Speech Segment (`s`) | Drift (`s`) | Caption Display (`2–5` words) | Spoken Words (`WordBoundary`) |
| :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| 01 | 01 | `0.360–1.539` | `0.360–1.539` | `0.000` | `At 2:17` | `At two seventeen` |
| 02 | 01 | `1.553–2.135` | `1.553–2.135` | `0.000` | `in the morning,` | `in the morning` |
| 03 | 01 | `2.434–3.598` | `2.434–3.598` | `0.000` | `the old stone lock` | `the old stone lock` |
| 04 | 01 | `3.613–4.479` | `3.613–4.479` | `0.000` | `on the Blackwater` | `on the Blackwater` |
| 05 | 01 | `4.493–5.772` | `4.493–5.772` | `0.000` | `has only one rule.` | `has only one rule` |
| 06 | 02 | `6.152–7.501` | `6.152–7.501` | `0.000` | `Never open the sluice` | `Never open the sluice` |
| 07 | 02 | `7.515–8.567` | `7.515–8.567` | `0.000` | `if the rain reaches` | `if the rain reaches` |
| 08 | 02 | `8.581–9.405` | `8.581–9.405` | `0.000` | `MARK FOUR.` | `Mark Four` |
| 09 | 03 | `9.825–10.933` | `9.825–10.933` | `0.000` | `For forty years,` | `For forty years` |
| 10 | 03 | `11.174–11.998` | `11.174–11.998` | `0.000` | `a night keeper` | `a night keeper` |
| 11 | 03 | `12.012–13.191` | `12.012–13.191` | `0.000` | `has logged the water` | `has logged the water` |
| 12 | 03 | `13.205–14.612` | `13.205–14.612` | `0.000` | `every fifteen minutes.` | `every fifteen minutes` |
| 13 | 04 | `14.992–17.208` | `14.992–17.208` | `0.000` | `1:45 — Mark Two.` | `One forty-five Mark Two` |
| 14 | 04 | `18.209–20.183` | `18.209–20.183` | `0.000` | `2:00 — Mark Three.` | `Two o'clock Mark Three` |
| 15 | 05 | `20.603–22.194` | `20.603–22.194` | `0.000` | `Outside, four inches` | `Outside four inches` |
| 16 | 05 | `22.208–23.529` | `22.208–23.529` | `0.000` | `of cold rain fall` | `of cold rain fall` |
| 17 | 05 | `23.543–24.637` | `23.543–24.637` | `0.000` | `in twenty minutes.` | `in twenty minutes` |
| 18 | 05 | `25.624–26.391` | `25.624–26.391` | `0.000` | `Yet the gauge` | `Yet the gauge` |
| 19 | 05 | `26.405–27.399` | `26.405–27.399` | `0.000` | `stops moving.` | `stops moving` |
| 20 | 06 | `27.799–29.290` | `27.799–29.290` | `0.000` | `Three millimeters below` | `Three millimeters below` |
| 21 | 06 | `29.305–30.228` | `29.305–30.228` | `0.000` | `the red line.` | `the red line` |
| 22 | 06 | `31.215–32.933` | `31.215–32.933` | `0.000` | `Still as dark glass.` | `Still as dark glass` |
| 23 | 07 | `33.373–34.751` | `33.373–34.751` | `0.000` | `So you carry the lantern` | `So you carry the lantern` |
| 24 | 07 | `34.765–35.958` | `34.765–35.958` | `0.000` | `out onto the catwalk` | `out onto the catwalk` |
| 25 | 07 | `35.972–36.640` | `35.972–36.640` | `0.000` | `to check for` | `to check for` |
| 26 | 07 | `36.654–37.663` | `36.654–37.663` | `0.000` | `a jammed float.` | `a jammed float` |
| 27 | 08 | `38.083–38.949` | `38.083–38.949` | `0.000` | `Your light hits` | `Your light hits` |
| 28 | 08 | `38.964–40.285` | `38.964–40.285` | `0.000` | `the wet stone wall.` | `the wet stone wall` |
| 29 | 08 | `41.271–41.925` | `41.271–41.925` | `0.000` | `And you see` | `And you see` |
| 30 | 08 | `41.939–43.473` | `41.939–43.473` | `0.000` | `the empty bolt holes.` | `the empty bolt holes` |
| 31 | 09 | `44.593–46.468` | `44.593–46.468` | `0.000` | `Someone unbolted Mark Four,` | `Someone unbolted Mark Four` |
| 32 | 09 | `46.752–48.101` | `46.752–48.101` | `0.000` | `and moved the brass plate` | `and moved the brass plate` |
| 33 | 09 | `48.116–49.266` | `48.116–49.266` | `0.000` | `two feet higher.` | `two feet higher` |
| 34 | 10 | `49.726–51.175` | `49.726–51.175` | `0.000` | `Behind you, the lamp` | `Behind you the lamp` |
| 35 | 10 | `51.189–52.226` | `51.189–52.226` | `0.000` | `in the keeper's booth` | `in the keeper's booth` |
| 36 | 10 | `52.240–53.135` | `52.240–53.135` | `0.000` | `clicks off.` | `clicks off` |
| 37 | 11 | `53.555–55.515` | `53.555–55.515` | `0.000` | `The river never stopped rising.` | `The river never stopped rising` |
| 38 | 11 | `56.502–58.008` | `56.502–58.008` | `0.000` | `The sluice gate behind you` | `The sluice gate behind you` |
| 39 | 11 | `58.022–59.144` | `58.022–59.144` | `0.000` | `is already open.` | `is already open` |

### 2.4 Verbatim `loudnorm` Measurement on Final `video.mp4`

```json
{
	"input_i" : "-16.04",
	"input_tp" : "-1.65",
	"input_lra" : "1.90",
	"input_thresh" : "-26.29",
	"output_i" : "-16.15",
	"output_tp" : "-1.75",
	"output_lra" : "1.80",
	"output_thresh" : "-26.40",
	"normalization_type" : "dynamic",
	"target_offset" : "0.15"
}
```

---

## 3. Verbatim `ffprobe` on Final Deliverable (`videos/team-b/grade-v05/video.mp4`)

```json
{
    "streams": [
        {
            "index": 0,
            "codec_name": "h264",
            "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
            "profile": "High",
            "codec_type": "video",
            "codec_tag_string": "avc1",
            "codec_tag": "0x31637661",
            "width": 1920,
            "height": 1080,
            "coded_width": 1920,
            "coded_height": 1080,
            "has_b_frames": 2,
            "pix_fmt": "yuv420p",
            "level": 41,
            "chroma_location": "left",
            "field_order": "progressive",
            "is_avc": "true",
            "r_frame_rate": "30/1",
            "avg_frame_rate": "30/1",
            "time_base": "1/15360",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 921600,
            "duration": "60.000000",
            "bit_rate": "3984132",
            "bits_per_raw_sample": "8",
            "nb_frames": "1800"
        },
        {
            "index": 1,
            "codec_name": "aac",
            "codec_long_name": "AAC (Advanced Audio Coding)",
            "profile": "LC",
            "codec_type": "audio",
            "codec_tag_string": "mp4a",
            "codec_tag": "0x6134706d",
            "sample_fmt": "fltp",
            "sample_rate": "48000",
            "channels": 2,
            "channel_layout": "stereo",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 2880000,
            "duration": "60.000000",
            "bit_rate": "192898",
            "nb_frames": "2814"
        }
    ],
    "format": {
        "filename": "/home/user/video-division/videos/team-b/grade-v05/video.mp4",
        "nb_streams": 2,
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "format_long_name": "QuickTime / MOV",
        "start_time": "0.000000",
        "duration": "60.000000",
        "size": "31395784",
        "bit_rate": "4186104",
        "probe_score": 100
    }
}
```

---

## 4. Reproducible Render Command & Asset Provenance

### Reproducible Build Command
```bash
python3 videos/team-b/grade-v05/build_v05.py
```
(`build_v05.py` sequentially runs `generate_luts.py`, `build_audio_v05.py`, and `render_v05.py`, keeping all temporary stems and per-shot clips in `/tmp/grade_v05_build` and writing `video.mp4` + `stills/` cleanly in-repo.)

### First-Party Asset & Provenance Ledger
- **Cinema Plates (`plates/shot_01.jpg` – `plates/shot_11.jpg`):** 100% first-party original plates created specifically for `grade-v05` by `grade` (`shot_01`–`shot_10` first-party AI cinema plates with optical continuity retouching on `shot_04`'s ledger lines; `shot_11` bespoke first-party matte/optical composite derived from `shot_01` with extinguished booth glass and crimson breach beacon). Zero third-party web downloads; zero reused `v04` plates; zero frames or audio reused from `references/`.
- **Colour Transforms (`luts/*.cube`):** Four original `33×33×33` 3D LUTs (`blackwater_slate.cube`, `amber_ledger.cube`, `mercury_stillness.cube`, `sluice_breach.cube`) authored mathematically from scratch in `generate_luts.py` by `grade`.
- **Audio (`build_audio_v05.py`):** First-party neural narration via `edge-tts` (`en-US-ChristopherNeural`) + procedural NumPy/SciPy stereo storm rain, bowed C-minor/Phrygian sub-cello score, and frame-locked foley.

---

## 5. Honest Self-Review

- **What hits the mark:** Pushing contrast deeper than `v04` paid off across all four colour regimes—especially **Shot 07 (`stills/poster_mark_four_clean.png` / `still_03_poster_catwalk.png`)**, where the dead-center oilskin silhouette holding a `2200 K` amber lantern between towering cyan-lit sluice piers delivers a genuine theatrical poster image. Synchronising Shot 10's practical `2200 K` booth window snap-off (`52.44 s`) directly to the spoken words *"clicks off."* and the mechanical switch transient creates a visceral audiovisual payoff, and locking all `39` `2–5` word amber/ivory/crimson captions to `100 ns` `WordBoundary` telemetry makes the story 100% legible muted without sacrificing `16:9` *KELVIN* cinematography.
- **Honest limitations:** Because the sandbox has `2 GB` RAM without swap, motion is driven via 2.5D bicubic camera choreography, layered parallax rain, practical light breathing, and temporal 35mm grain over still plates rather than full 3D fluid simulation; additionally, TTS prosody (`en-US-ChristopherNeural`), while calm and steady, lacks the micro-breath fragility of a live human actor in a dark booth, and audio balance was verified strictly through EBU R128 / RMS / spectral / silence telemetry rather than human ears.
