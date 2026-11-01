# QA Report — `MARK FIVE` (`videos/team-b/grade-v06`)

> **Verification disclosure:** no human listened to this; verification is numeric and structural.

---

## Audio Stem Provenance & Honest Scratch Disclosure

- **Honest disclosure on `c37de32` scratch state:** During the initial Wave 3 build (`4d3a547` / `c37de32`), the intermediate `48 kHz` WAV stems (`voice_A_narrator_48k.wav`, `voice_B_responder_48k.wav`, `dialogue_stem_48k.wav`) were written to `/tmp/grade_v06_build` and cleared before turn-end snapshot to keep `/home/user` below `128 MB`. Re-querying `edge-tts` (`en-US-ChristopherNeural` and `en-GB-SoniaNeural`) reproduces the exact locked `WordBoundary` schedule across all `133` words (`0.000000 s` maximum timestamp difference vs `timing/timeline_locked.json`), while the cloud MP3 neural vocoder introduces stochastic sample variance.
- **No synthetic claim over lost scratch:** Rather than claiming fresh stems were the deleted `/tmp` files from `2dfd4511d7a285a02b9ae825e9d554091bfc8ce9b1690e8110315995e787d987`, we persisted all four timeline-aligned `48 kHz` stereo lossless FLAC stems, raw per-turn TTS MP3 sources, `timing/tts_source_manifest.json`, and `audio/gain_mapping.json` inside `videos/team-b/grade-v06/`, and remuxed **only the audio stream** (`ffmpeg -c:v copy`) onto the untouched `4d3a547` H.264 video bitstream.
- **Offline-by-default exact reproduction:** Running `python3 videos/team-b/grade-v06/build_audio_v06.py` with `/tmp/grade_v06_build` absent consumes the committed `.flac` stems and `audio/gain_mapping.json` **100% offline** (no `edge-tts` calls, no edits to `timing/timeline_locked.json`), reproducing `master_audio_48k.wav` bit-for-bit (`SHA256 2b4d71671e2d47234149d2183d6e23388529357cdfc54177bfc074d8c263af89`), which matches the delivered `video.mp4` AAC stream at **`r = 0.998956`** (`-45.80 dBFS` AAC LC floor).

| Durable Repo Artifact | Format | Bytes | SHA256 |
| :--- | :--- | ---: | :--- |
| `videos/team-b/grade-v06/video.mp4` | H.264 (`-c:v copy` from `4d3a547`) + AAC `48k` | `27,765,746` | `626cb67bf2c5d526db620886ce950de1834a8d1c225390fc33ccedb7fcc2151a` |
| `videos/team-b/grade-v06/audio/voice_A_narrator_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`28% L`) | `1,630,410` | `e1f7e794645caf77e2af8e89e01747c330632f48028882e71e9844dd4ef1645b` |
| `videos/team-b/grade-v06/audio/voice_B_responder_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`28% R`, `340–3,450 Hz`) | `970,078` | `60751c800e216675f019b90091b020f395a4d5f2cb1ebc8f5a0e778911e1f989` |
| `videos/team-b/grade-v06/audio/dialogue_stem_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`Voice A + Voice B`, `0` overlap) | `2,582,955` | `f61f0d0793068066219c1ee551cfb6336eb09a662033b652f51ebc73785ac61f` |
| `videos/team-b/grade-v06/audio/bed_ducked_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC | `5,536,813` | `701079cc55f2a8ddb56cb198d16e0b9043637d1edef5bb1ccaf3ebe52766cce8` |
| `videos/team-b/grade-v06/audio/tts_turns/turn_01_A.mp3`–`turn_10_B.mp3` | `10` raw `edge-tts` MP3s + `timing/tts_source_manifest.json` | `~392 KB` | Individual hashes in `timing/tts_source_manifest.json` |
| `videos/team-b/grade-v06/audio/gain_mapping.json` | Pre-scale + 2-pass `loudnorm` + `alimiter` chain | `3,640` | Deterministic stem-to-MP4 gain & separation telemetry |

---

## Voice decision

For `v06` (*MARK FIVE*), the narrative escalates from solo monologue to a live ten-turn nocturnal interrogation between two audibly, spectrally, and spatially distinct speakers chosen autonomously without polling human reviewers (Rule 8):

1. **Narrator (`KEEPER`, Voice A — Lower Spillway Tower):** **`edge-tts` `en-US-ChristopherNeural`** rendered at **`--rate=-11% --pitch=-5Hz`**. Processed as a close-mic, full-bandwidth (`80 Hz – 8,000 Hz`) deep American male baritone with a measured median fundamental pitch of **`105.3 Hz`** and spectral centroid of **`1,981.7 Hz`** (`+1.5 dB` chest warmth at `132 Hz`, `-2.4 dB` boxiness cut at `320 Hz`, `+2.6 dB` consonant presence at `2,950 Hz`), panned **Left-Center (`-28%`, `L = 0.880, R = 0.550`, `+4.08 dB` L-channel bias)**.
2. **Responder (`COPPER LINE`, Voice B — Field-Telephone Caller):** **`edge-tts` `en-GB-SoniaNeural`** rendered at **`--rate=+4% --pitch=+2Hz`**. Choosing a clipped British RP female operator voice creates an immediate **`1.96×` (~1 full octave) fundamental pitch separation (`206.0 Hz` vs `105.3 Hz`)**, distinct dialect (`en-GB` vs `en-US`), and brisker procedural dispatch cadence (`+4%` vs `-11%`). Acoustically, Voice B is passed through a 4th-order Butterworth **`340 Hz – 3,450 Hz` Bakelite copper-handset bandpass** with mild carbon-transmitter saturation, `+3.4 dB` upper-mid presence at `1,750 Hz`, gated analog wire floor, and mechanical cradle/alligator-clip transients (measured spectral centroid **`1,078.5 Hz`** with zero low-end energy masking Voice A's baritone chest), panned **Right-Center (`+28%`, `L = 0.550, R = 0.880`, `+4.08 dB` R-channel bias)** for an **`8.16 dB` inter-speaker L/R differential** (measured stereo L/R correlation on final `video.mp4` = **`0.8524`**) that remains 100% phase-coherent when summed to mono on phone speakers.

---

## 1. Two-Timeline Dialogue Interleaving & Body-Window Activity (`0.000 s` Overlap Proof)

Across all `2,880,000` stereo samples (`60.000 s @ 48 kHz`), `sum((abs(voice_A) > 0) & (abs(voice_B) > 0)) == 0 samples` (**`0.000000 s` overlap**), and `voice_A_narrator_48k.flac + voice_B_responder_48k.flac == dialogue_stem_48k.flac` sample-for-sample.

| Turn | Narrator Timeline — Voice A (`en-US-ChristopherNeural`, `28% L`) | Responder Timeline — Voice B (`en-GB-SoniaNeural`, `28% R`, Handset) | Gap to Next Turn (`s`) | Overlap (`s`) | Spoken Dialogue |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **01** | **`0.400 s – 9.929 s`** (`9.529 s`) | *(silent)* | `0.820 s` *(cradle lift)* | `0.000` | **[A]:** *"At two twenty-four, seven minutes after the upper lock breached, the copper wall phone rings. A line dead since nineteen eighty-nine."* |
| **02** | *(silent)* | **`10.749 s – 15.388 s`** (`4.639 s`) | `0.680 s` | `0.000` | **[B]:** *"Lower Tower, come in. Confirm your water is still below Mark Five."* |
| **03** | **`16.068 s – 21.524 s`** (`5.456 s`) | *(silent)* | `0.680 s` | `0.000` | **[A]:** *"I check the spillway wall outside. Four inches below the red five."* |
| **04** | *(silent)* | **`22.204 s – 26.539 s`** (`4.335 s`) | `0.620 s` | `0.000` | **[B]:** *"Good. Whatever you hear on the roof, do not draw the spillway pins."* |
| **05** | **`27.159 s – 31.126 s`** (`3.967 s`) | *(silent)* | `0.680 s` | `0.000` | **[A]:** *"Wait. How do you know something is walking on the roof?"* |
| **06** | *(silent)* | **`31.806 s – 35.196 s`** (`3.390 s`) | `0.680 s` | `0.000` | **[B]:** *"Follow the copper telephone wire down beneath your window sill."* |
| **07** | **`35.876 s – 41.163 s`** (`5.287 s`) | *(silent)* | **`1.280 s`** *(pre-twist beat)* | `0.000` | **[A]:** *"My lamp hits the wet stone floor. The wire is cut clean through."* |
| **08** | *(silent)* | **`42.443 s – 50.170 s`** (`7.727 s`) | `0.780 s` | `0.000` | **[B]:** *"I'm not calling from Basin Control. I'm on your roof, clipped to the stub. And Mark Five wasn't painted to measure the river."* |
| **09** | **`50.950 s – 55.886 s`** (`4.936 s`) | *(silent)* | `0.880 s` *(lamp dims)* | `0.000` | **[A]:** *"I raise the lamp. Mark Five is stenciled across the ceiling."* |
| **10** | *(silent)* | **`56.766 s – 58.833 s`** (`2.067 s`) | `1.167 s` *(tail disconnect)* | `0.000` | **[B]:** *"It marks how high your tower fills."* |

### Per-10-Second Body-Window Speech Activity & Matched Active-Window Ducking Proof

Measured directly from the committed `audio/*.flac` stems and final `video.mp4` (`85.56%` active speech duty across `60.000 s`; matched active-speech RMS: `dialogue_stem_48k.flac = -23.93 dBFS` vs `bed_ducked_48k.flac = -34.35 dBFS` → **`+10.42 dB` speech-over-bed dominance**):

| Window | Speech Duty (`%`) | `voice_A_narrator_48k.flac` RMS (`dBFS`) | `voice_B_responder_48k.flac` RMS (`dBFS`) | `dialogue_stem_48k.flac` RMS (`dBFS`) | `bed_ducked_48k.flac` RMS (`dBFS`) | Final `video.mp4` Mix RMS (`dBFS`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `00–10 s` | `95.3%` | `-24.21` | `silent` | `-24.21` | `-34.77` | `-18.88` |
| `10–20 s` | `85.7%` | `-27.86` | `-27.09` | `-24.45` | `-34.11` | `-18.92` |
| `20–30 s` | `87.0%` | `-27.39` | `-27.90` | `-24.63` | `-34.62` | `-19.25` |
| `30–40 s` | `86.4%` | `-26.15` | `-27.75` | `-23.87` | `-34.12` | `-18.50` |
| `40–50 s` | `87.2%` | `-33.80` | `-26.11` | `-25.43` | `-32.34` | `-19.50` |
| `50–60 s` | `71.7%` | `-26.89` | `-30.44` | `-25.30` | `-32.25` | `-19.41` |

### Measured Acoustic Separation Summary (`audio/gain_mapping.json`)

| Metric | Voice A (`KEEPER`) | Voice B (`COPPER LINE`) | Separation / Target |
| :--- | :--- | :--- | :--- |
| **Engine Voice** | `en-US-ChristopherNeural` | `en-GB-SoniaNeural` | Distinct neural models & dialects |
| **Prosody Rate / Pitch** | `--rate=-11%`, `--pitch=-5Hz` | `--rate=+4%`, `--pitch=+2Hz` | `15%` rate delta + `7 Hz` shift |
| **Median Fundamental `F0`** | `105.3 Hz` | `206.0 Hz` | **`1.96×` (`~1.0` octave apart)** |
| **Spectral Centroid** | `1,981.7 Hz` (`80–8,000 Hz`) | `1,078.5 Hz` (`340–3,450 Hz` handset) | Non-competing spectral envelopes |
| **Stereo Pan Bias** | `+4.08 dB` Left (`28% L`) | `+4.08 dB` Right (`28% R`) | **`8.16 dB` L/R (`r_LR = 0.8524`)** |
| **Active Sample Overlap** | `0` samples | `0` samples | **`0.000000 s` overlap** |
| **Dialogue-to-Bed Ducking** | `+10.42 dB` RMS above score/rain | `+10.42 dB` RMS above score/rain | Within `8–12 dB` spec |

---

## 2. Technical & Speech Acceptance Checklist (`specs/60s-video.md`)

| Check | Spec Target | Measured Result | Verdict |
| :--- | :--- | :--- | :---: |
| **Duration** | `58.0–62.0 s` (`60.0 s` target) | `60.000000 s` (`1,800` frames @ `30/1` fps) | PASS |
| **Resolution & Aspect** | `1920×1080` landscape (`16:9`) | `1920×1080` progressive | PASS |
| **Video Stream** | H.264 `yuv420p` `+faststart` | `h264` High L4.1, `yuv420p`, `+faststart` (`-c:v copy` from `4d3a547`) | PASS |
| **Audio Stream** | `48 kHz` stereo AAC | `aac` LC, `48000 Hz`, `2` channels (`stereo`) | PASS |
| **Integrated Loudness** | `-16.0 LUFS ± 0.5` | **`-16.12 LUFS`** (`loudnorm` JSON on final MP4) | PASS |
| **True Peak** | `≤ -1.0 dBTP` | **`-1.81 dBTP`** (`0.81 dB` safety margin) | PASS |
| **Silence Check (`-40dB`, `1s`)** | No dead hole swallowing middle | `0` silences `> 1.0 s` on full mix (`1.333 s` max dialogue pause at `41.17 s` pre-twist beat) | PASS |
| **Black / Freeze Check (`>0.5s`)** | `0` segments `> 0.5 s` | `0` black `> 0.5 s`; `0` frozen `> 0.5 s` | PASS |
| **Durable Audio Stems** | Committed in-repo + offline repro | `4` lossless `.flac` stems + `10` raw `.mp3` turns + `gain_mapping.json` (`r = 0.998956`) | PASS |
| **Git Discipline (Rules & Spec)** | Script committed first; render committed before polish (Rule 11) | `36cd10d` (`script.md`) → `4d3a547` (render checkpoint) → stem persistence & QA polish | PASS |
| **Wall-Frame & Stills** | `≥ 3` stills + 1 wall-worthy frame | `6` PNG stills incl. `wall_frame_mark_five_clean.png` (Shot 05 oculus cistern) | PASS |

---

## 3. Caption Cue Alignment (`40` Two-Voice `2–5` Word Beats, `0.000 s` Drift)

Speaker A (`KEEP`) renders left-shifted (`-58 px`) with a vertical amber edge bar; Speaker B (`LINE`) renders right-shifted (`+58 px`) with a vertical cyan signal bar and `LINE ·` prefix:

| Cue | Spk | Shot | Caption Cue (`s`) | Speech (`WordBoundary`) (`s`) | Drift (`s`) | Display Text (`2–5` words) |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 01 | `A` | 01 | `0.400–1.692` | `0.400–1.692` | `0.000` | `At 2:24 AM,` |
| 02 | `A` | 01 | `1.973–3.083` | `1.973–3.083` | `0.000` | `seven minutes after` |
| 03 | `A` | 01 | `3.097–4.431` | `3.097–4.431` | `0.000` | `the upper lock breached,` |
| 04 | `A` | 01 | `4.642–6.482` | `4.642–6.482` | `0.000` | `the copper wall phone rings.` |
| 05 | `A` | 02 | `7.457–8.370` | `7.457–8.370` | `0.000` | `A line dead` |
| 06 | `A` | 02 | `8.384–9.929` | `8.384–9.929` | `0.000` | `since 1989.` |
| 07 | `B` | 02 | `10.749–12.300` | `10.749–12.300` | `0.000` | `Lower Tower, come in.` |
| 08 | `B` | 02 | `12.648–13.777` | `12.648–13.777` | `0.000` | `Confirm your water` |
| 09 | `B` | 02 | `13.790–14.547` | `13.790–14.547` | `0.000` | `is still below` |
| 10 | `B` | 02 | `14.559–15.388` | `14.559–15.388` | `0.000` | `MARK FIVE.` |
| 11 | `A` | 03 | `16.068–16.728` | `16.068–16.728` | `0.000` | `I check the` |
| 12 | `A` | 03 | `16.742–18.372` | `16.742–18.372` | `0.000` | `spillway wall outside.` |
| 13 | `A` | 03 | `19.347–20.470` | `19.347–20.470` | `0.000` | `Four inches below` |
| 14 | `A` | 03 | `20.484–21.524` | `20.484–21.524` | `0.000` | `the red five.` |
| 15 | `B` | 04 | `22.204–23.895` | `22.204–23.895` | `0.000` | `Good. Whatever you hear` |
| 16 | `B` | 04 | `23.907–24.544` | `23.907–24.544` | `0.000` | `on the roof,` |
| 17 | `B` | 04 | `24.796–25.433` | `24.796–25.433` | `0.000` | `do not draw` |
| 18 | `B` | 04 | `25.445–26.539` | `25.445–26.539` | `0.000` | `the spillway pins.` |
| 19 | `A` | 05 | `27.159–29.342` | `27.159–29.342` | `0.000` | `Wait. How do you know` |
| 20 | `A` | 05 | `29.356–30.396` | `29.356–30.396` | `0.000` | `something is walking` |
| 21 | `A` | 05 | `30.410–31.126` | `30.410–31.126` | `0.000` | `on the roof?` |
| 22 | `B` | 06 | `31.806–32.660` | `31.806–32.660` | `0.000` | `Follow the copper` |
| 23 | `B` | 06 | `32.672–33.909` | `32.672–33.909` | `0.000` | `telephone wire down` |
| 24 | `B` | 06 | `33.921–35.196` | `33.921–35.196` | `0.000` | `beneath your window sill.` |
| 25 | `A` | 07 | `35.876–36.817` | `35.876–36.817` | `0.000` | `My lamp hits` |
| 26 | `A` | 07 | `36.831–38.180` | `36.831–38.180` | `0.000` | `the wet stone floor.` |
| 27 | `A` | 07 | `39.155–39.955` | `39.155–39.955` | `0.000` | `The wire is` |
| 28 | `A` | 07 | `39.969–41.163` | `39.969–41.163` | `0.000` | `cut clean through.` |
| 29 | `B` | 08 | `42.443–43.321` | `42.443–43.321` | `0.000` | `I'm not calling` |
| 30 | `B` | 08 | `43.333–44.546` | `43.333–44.546` | `0.000` | `from Basin Control.` |
| 31 | `B` | 08 | `44.929–45.903` | `44.929–45.903` | `0.000` | `I'm on your roof,` |
| 32 | `B` | 08 | `46.143–47.129` | `46.143–47.129` | `0.000` | `clipped to the stub.` |
| 33 | `B` | 09 | `47.513–48.403` | `47.513–48.403` | `0.000` | `And Mark Five` |
| 34 | `B` | 09 | `48.415–49.196` | `48.415–49.196` | `0.000` | `wasn't painted` |
| 35 | `B` | 09 | `49.208–50.170` | `49.208–50.170` | `0.000` | `to measure the river.` |
| 36 | `A` | 10 | `50.950–52.256` | `50.950–52.256` | `0.000` | `I raise the lamp.` |
| 37 | `A` | 10 | `53.232–54.706` | `53.232–54.706` | `0.000` | `Mark Five is stenciled` |
| 38 | `A` | 10 | `54.720–55.886` | `54.720–55.886` | `0.000` | `across the ceiling.` |
| 39 | `B` | 10 | `56.766–57.752` | `56.766–57.752` | `0.000` | `It marks how high` |
| 40 | `B` | 10 | `57.764–58.833` | `57.764–58.833` | `0.000` | `your tower fills.` |

---

## 4. Verbatim Command Outputs (`ffprobe`, `loudnorm`, `silencedetect` on Durable Repo Paths)

### 4.1 Verbatim `ffprobe` on Final Deliverable (`videos/team-b/grade-v06/video.mp4`, SHA256 `626cb67bf2c5d526db620886ce950de1834a8d1c225390fc33ccedb7fcc2151a`)

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
            "width": 1920,
            "height": 1080,
            "pix_fmt": "yuv420p",
            "level": 41,
            "field_order": "progressive",
            "r_frame_rate": "30/1",
            "avg_frame_rate": "30/1",
            "time_base": "1/15360",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 921600,
            "duration": "60.000000",
            "bit_rate": "3500610",
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
            "sample_fmt": "fltp",
            "sample_rate": "48000",
            "channels": 2,
            "channel_layout": "stereo",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 2880000,
            "duration": "60.000000",
            "bit_rate": "192416",
            "nb_frames": "2814"
        }
    ],
    "format": {
        "filename": "videos/team-b/grade-v06/video.mp4",
        "nb_streams": 2,
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "start_time": "0.000000",
        "duration": "60.000000",
        "size": "27765746",
        "bit_rate": "3702099",
        "probe_score": 100
    }
}
```

### 4.2 Verbatim `loudnorm` Measurement on Final `videos/team-b/grade-v06/video.mp4`

```json
{
	"input_i" : "-16.12",
	"input_tp" : "-1.81",
	"input_lra" : "2.50",
	"input_thresh" : "-26.56",
	"output_i" : "-16.15",
	"output_tp" : "-1.79",
	"output_lra" : "2.30",
	"output_thresh" : "-26.57",
	"normalization_type" : "dynamic",
	"target_offset" : "0.15"
}
```

### 4.3 `ffprobe` & `silencedetect=n=-40dB:d=1` on Committed Durable Stems & Full Mix

```text
--- videos/team-b/grade-v06/audio/voice_A_narrator_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=1630410

--- videos/team-b/grade-v06/audio/voice_B_responder_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=970078

--- videos/team-b/grade-v06/audio/dialogue_stem_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=2582955

--- videos/team-b/grade-v06/audio/bed_ducked_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=5536813

# ffmpeg -i videos/team-b/grade-v06/audio/dialogue_stem_48k.flac -af silencedetect=n=-40dB:d=1 -f null -
silence_start: 6.483583  | silence_end: 7.567958  | silence_duration: 1.084375
silence_start: 18.352271 | silence_end: 19.506271 | silence_duration: 1.154
silence_start: 27.722188 | silence_end: 28.802896 | silence_duration: 1.080708
silence_start: 38.147333 | silence_end: 39.275833 | silence_duration: 1.1285
silence_start: 41.167646 | silence_end: 42.500521 | silence_duration: 1.332875
silence_start: 52.149812 | silence_end: 53.342521 | silence_duration: 1.192708
silence_start: 58.8375   | silence_end: 60        | silence_duration: 1.1625

# ffmpeg -i videos/team-b/grade-v06/video.mp4 -af silencedetect=n=-40dB:d=1 -f null -
0 silences > 1.0 s on full mix
```

---

## 5. Reproducibility, Provenance & Honest Self-Review

### Reproducible Build Commands (Offline Default)
```bash
pip install -r videos/team-b/grade-v06/requirements.txt
python3 videos/team-b/grade-v06/build_audio_v06.py
python3 videos/team-b/grade-v06/build_v06.py
```

### First-Party Asset Provenance
- **Plates (`plates/shot_01.jpg`–`shot_10.jpg`):** 10/10 original first-party `1920×1080` plates generated specifically for `grade-v06` by `grade` (`0` external downloads, `0` reused `v04`/`v05` plates, `0` assets from `references/`).
- **3D LUTs (`luts/*.cube`):** Four original `33×33×33` `.cube` LUTs (`spillway_obsidian.cube`, `copper_bakelite.cube`, `cyan_skylight.cube`, `ceiling_flood_6800k.cube`) generated by `generate_luts.py`.
- **Audio (`build_audio_v06.py` + `audio/*.flac`):** First-party dual-engine neural synthesis (`edge-tts` `en-US-ChristopherNeural` + `en-GB-SoniaNeural`) + procedural NumPy/SciPy storm rain, D-minor/Phrygian sub-cello score (`< 350 Hz`), and frame-locked Bakelite phone/footstep foley, with all lossless `48 kHz` stems committed inside `videos/team-b/grade-v06/audio/`.

### Honest Self-Review
- **Strengths:** Making the medium of the second voice (*a copper emergency phone wire severed at the floor and alligator-clipped on the roof*) the central physical mechanism of the twist turns the two-voice brief into genuine cinema rather than arbitrary narration trading. **Shot 05 (`stills/wall_frame_mark_five_clean.png`)**—the symmetrical subterranean granite cistern hall with vertical rain pouring through the circular oculus onto the lone amber storm lantern—is the strongest single frame in the *KELVIN / MARK* trilogy. Spectral, fundamental (`105.3 Hz` vs `206.0 Hz`), timbral (close-mic vs `340–3,450 Hz` copper handset), stereo (`±4.08 dB` L/R, `r_LR = 0.8524`), and visual caption separation make the two voices effortlessly distinct.
- **Limitations:** As with `v05`, camera motion and rain are 2.5D optical composites over still plates within a `2 GB` RAM budget, and both voices are synthetic neural TTS verified strictly through numeric/spectral/loudness telemetry rather than human listening.
