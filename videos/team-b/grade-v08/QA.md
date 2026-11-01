# QA Report — `MARK SEVEN` (`videos/team-b/grade-v08`)

> **Honest No-Listen Verification Paragraph:** No human listened to this audio or watched this picture in real time during build or QA. Every claim below—integrated loudness (`-16.14 LUFS`), true peak (`-2.10 dBTP`), zero active-sample voice overlap (`0` samples), fundamental pitch tiers (`106.67 Hz` vs `210.53 Hz`), speech-band stereo azimuth (`+5.11..+5.13 dB` Left vs `-5.17..-5.15 dB` Right), active-turn dialogue-over-bed margin (`+10.55 dB`), `WordBoundary`-to-caption lock (`0.000 s` drift across `39` cues), and zero black/freeze/silence violations—is established purely by deterministic signal measurement, `ffprobe`/`ffmpeg` filter telemetry, and still-frame inspection. Subjective human prosody, emotional pacing, and acoustic naturalness remain unverified until human review.

---

## 0. Pre-Render Escalation Choice & Signature Wall-Frame Declaration

### Chosen Escalation Axis (`v05` → `v06` → `v07` → `v08`)
- **Decision (committed in `2f9d43d` prior to plate generation & render):** **Option 1 — A Place Larger Than a Room** (the three-mile Blackwater basalt river gorge, the exterior `400 ft` concrete arch dam, the canyon steel truss railway bridge, and the flooded street grid of the evacuated river town of **Lowgate** two miles downstream at `03:14 AM`).
- **Justification:** `v05` (*MARK FOUR*, 1 voice), `v06` (*MARK FIVE*, 2 voices), and `v07` (*MARK SIX*, 3 voices) escalated speaker count inside enclosed subterranean concrete rooms (`6–12 m` wide) looking *out* through glass at rising water. Adding a fourth voice inside another room would have been diminishing-returns gimmickry. Stepping **outside** the dam thirty-seven minutes after Vault Six blew its surge bolts tests whether the Division House Look (`500T` `0.004` shadow toe crush, steep midtone S-curve, `[1.00, 0.38, 0.08]` red-amber halation, cold `6500K–7000K` storm rain/mist, and **one warm `2600K` practical per frame**) holds across monumental landscape architecture—and delivers the dramatic resolution of the entire series: *drowning one concrete room inside the dam took two inches off a three-mile river*, stopping the flood two inches below **`MARK SEVEN`** in the center of town.

### Signature Wall-Frame Named Before Render (`2f9d43d` → `50fe807`)
- **Named Wall-Frame:** **Shot 08 (`41.300–47.100 s`, exact frame `1398` @ `46.600 s` → `videos/team-b/grade-v08/stills/wall_frame_mark_seven_clean.png`)**
- **Composition & Grade:** A dead-symmetrical one-point architectural night photograph straight down flooded Main Street of evacuated **Lowgate** at `03:14 AM`—mirror-black slackwater covering the cobblestones curb-to-curb between dark wet 1930s brick storefronts (`DRUG STORE`, `BANK`, `HARDWARE`), the `400 ft` concrete arch dam rising through cold `6500K` canyon storm mist at the end of the avenue, and dead-center in the flooded street a solitary cast-iron municipal benchmark lamppost burning at `2600K` (`500T` red-amber halation bloom) above crisp white stenciled letters **`MARK SEVEN`** standing dry above the black waterline and casting a golden reflection straight toward camera.

---

## 1. Durable Audio Provenance & Offline-First Reproduction

All **four timeline-aligned `48 kHz` stereo lossless FLAC stems**, all **ten raw `edge-tts` turn MP3s**, `timing/tts_source_manifest.json`, `timing/timeline_locked.json`, `timing/captions_locked.json`, and `audio/gain_mapping.json` are committed inside `videos/team-b/grade-v08/`. Running `python3 videos/team-b/grade-v08/build_audio_v08.py` with `/tmp/grade_v08_build` absent executes **100% offline** (zero `edge-tts` calls, zero timing edits), reproducing `master_audio_48k.wav` bit-for-bit (`SHA256 e966749c86e8be3d6fd30aaef753daeab0e77edddcd164564c8716397814e3b6`), which matches the delivered `video.mp4` AAC stream at **`r = 0.999458`** (`-49.03 dBFS` AAC LC floor; joint stem-to-mix fit `r = 0.997070`, lag `144` samples / `3.0 ms` @ `48 kHz`).

| Durable Repo Artifact | Format | Bytes | SHA256 |
| :--- | :--- | ---: | :--- |
| `videos/team-b/grade-v08/video.mp4` | H.264 High L4.1 + AAC `48k` (`+faststart`, `moov` @ `36`) | `31,845,395` | `45a68bbc6ba6df00c6200df1933408986790f4260dfa1720d13530a5fed17ab2` |
| `videos/team-b/grade-v08/audio/voice_A_crest_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`-36% L`, `+5.20 dB` L) | `1,401,678` | `3579cf1882de27f5fe4113c49ba8028db50a953b5bd44e4efe029b1fc4924091` |
| `videos/team-b/grade-v08/audio/voice_B_levee_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`+36% R`, `+5.20 dB` R) | `1,258,436` | `fbf5638fcb348a68c8b527d8f9ef288367e3363375102e98e634953ba1006337` |
| `videos/team-b/grade-v08/audio/dialogue_stem_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`A + B` exact sum) | `2,642,581` | `561d5535f0f1ed46b1fcdaca02d93ce93d9cfb21d77b54081d9ebae5cc82a6ef` |
| `videos/team-b/grade-v08/audio/bed_ducked_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC | `4,741,939` | `f2f518757c79b7fe433a00be26177de2769f6f7054a85d01f8ffd2cadb4146e1` |
| `videos/team-b/grade-v08/audio/tts_turns/turn_01_A.mp3`–`turn_10_B.mp3` | `10` raw `edge-tts` MP3s + `timing/tts_source_manifest.json` | `~415 KB` | Per-turn SHA256 verified (`0.000000 s` telemetry drift) |
| `videos/team-b/grade-v08/audio/gain_mapping.json` | Deterministic stem-to-MP4 gain & separation telemetry | `2,980` | Exact two-pass `loudnorm` + `alimiter` chain |

---

## 2. Two-Station Valley Relay Separation Proof (`CREST` ↔ `LEVEE`, `0.000 s` Overlap)

| Separation Axis | Station A — `CREST` (`400 ft` Dam Parapet) | Station B — `LEVEE` (Lowgate Levee `2 mi` Downriver) | Separation Verdict |
| :--- | :--- | :--- | :--- |
| **Neural Engine & Dialect** | `en-US-ChristopherNeural` (`--rate=-11% --pitch=-5Hz`) | `en-GB-SoniaNeural` (`--rate=+4% --pitch=+4Hz`) | Distinct US baritone vs British RP engineer |
| **`lux` Autocorrelation `F0` (`<450 Hz`)** | **`106.67 Hz`** (`435` voiced windows) | **`210.53 Hz`** (`498` voiced windows; **`1.97×` A**) | Nearly full-octave (`11.8 st`) pitch separation |
| **Transducer Passband & EQ** | `75–8,000 Hz` full-range chest close-mic (`+125 Hz` warmth) | `310–3,600 Hz` 4th-order VHF transceiver (`+2.25 kHz` peak) | Distinct close-mic vs VHF radio passband |
| **Stem Stereo Pan (`L/R dB`)** | **`+5.20 dB` Left** (`-36%`) | **`-5.20 dB` (`+5.20 dB` Right, `+36%`)** | **`10.40 dB` L-to-R span (`r_LR = 0.8533`)** |
| **Mix Speech-Band (`350–3400 Hz`) `L-R`** | **`+5.11` to `+5.13 dB` Left** | **`-5.17` to `-5.15 dB` Right** | Cleanly preserved in final `video.mp4` |
| **Active Sample Overlap** | `0` samples above `1 LSB` | `0` samples above `1 LSB` | **`0.000000 s` overlap; strict `A/B` alternation** |

### Ten-Turn Ridge-to-Town Interleaving Table (`5×A`, `5×B`, `0.000 s` Overlap)

| Turn | Station A (`CREST`, `-36% L`) | Station B (`LEVEE`, `+36% R`) | Mix `L-R` (`dB`) | Gap (`s`) | Spoken Line |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **01** | **`0.440–6.885 s`** | *(silent)* | `+5.11` | `0.755` | **[A]:** *"Three fourteen, thirty-seven minutes after Vault Six flooded inside the dam, and the gorge is full."* |
| **02** | *(silent)* | **`7.640–13.772 s`** | `-5.15` | `0.755` | **[B]:** *"Lowgate levee, two miles downstream, every house is empty, and black water is across the rail yard."* |
| **03** | **`14.527–20.592 s`** | *(silent)* | `+5.13` | `0.755` | **[A]:** *"All four spillway gates are wide open, and the canyon crest is passing the railway bridge now."* |
| **04** | *(silent)* | **`21.347–26.541 s`** | `-5.17` | `0.755` | **[B]:** *"White water is hitting the steel girders on the bridge, and backing slow water down Main Street."* |
| **05** | **`27.296–32.407 s`** | *(silent)* | `+5.12` | `0.755` | **[A]:** *"Marks One through Five are on the dam, Six was the vault, where is Mark Seven?"* |
| **06** | *(silent)* | **`33.162–38.020 s`** | `-5.16` | `0.755` | **[B]:** *"Not on the dam, they stenciled Mark Seven on the iron streetlamp in the town square."* |
| **07** | **`38.775–41.147 s`** | *(silent)* | `+5.11` | `0.755` | **[A]:** *"Tell me where the water is on that post."* |
| **08** | *(silent)* | **`41.902–46.580 s`** | `-5.15` | **`0.917`** | **[B]:** *"The amber lamp is still burning, and the river just stopped two inches below Mark Seven."* |
| **09** | **`47.497–52.790 s`** | *(silent)* | `+5.11` | `0.755` | **[A]:** *"Drowning one concrete room inside the dam took two inches off a three-mile river."* |
| **10** | *(silent)* | **`53.545–58.920 s`** | `-5.17` | `1.080` | **[B]:** *"Four thousand people left their keys on the counter, and their town is still standing at Mark Seven."* |

### Per-10-Second Body-Window Speech Activity & Matched Active-Window Ducking Proof

Measured on the committed `audio/*.flac` stems and final `video.mp4` (`85.87%` declared turn coverage across `60.000 s`; matched active-speech RMS: `dialogue_stem_48k.flac = -23.46 dBFS` vs `bed_ducked_48k.flac = -34.01 dBFS` → **`+10.55 dB` speech-over-bed dominance**):

| Window | Speech Duty (`%`) | `voice_A_crest` (`dBFS`) | `voice_B_levee` (`dBFS`) | `dialogue_stem` (`dBFS`) | `bed_ducked` (`dBFS`) | Final `video.mp4` Mix (`dBFS`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `00–10 s` | `75.2%` | `-25.36` | `-28.24` | `-23.56` | `-31.79` | `-18.18` |
| `10–20 s` | `79.8%` | `-25.71` | `-28.97` | `-24.03` | `-33.52` | `-18.39` |
| `20–30 s` | `74.2%` | `-28.69` | `-26.30` | `-24.32` | `-32.55` | `-18.35` |
| `30–40 s` | `73.8%` | `-27.41` | `-26.59` | `-23.97` | `-32.59` | `-18.23` |
| `40–50 s` | `72.8%` | `-27.83` | `-26.76` | `-24.25` | `-30.10` | `-17.89` |
| `50–60 s` | `72.4%` | `-30.00` | `-26.15` | `-24.65` | `-32.70` | `-18.59` |

---

## 3. Technical & House-Look Acceptance Checklist (`specs/60s-video.md` + `DIRECTIVE-2026-11-01-house-look.md`)

| Check | Spec Target | Measured Result | Verdict |
| :--- | :--- | :--- | :---: |
| **Duration** | `58.0–62.0 s` (`60.0 s` target) | `60.000000 s` (`1,800` frames @ `30/1` fps CFR) | PASS |
| **Resolution & Aspect** | `1920×1080` landscape (`16:9`) | `1920×1080` progressive (`< 90 MB` at `31.85 MB`) | PASS |
| **Video Stream** | H.264 `yuv420p` `+faststart` | `h264` High L4.1, `yuv420p`, `moov` atom at byte `36` | PASS |
| **Audio Stream** | `48 kHz` stereo AAC | `aac` LC, `48000 Hz`, `2` channels (`stereo`) | PASS |
| **Integrated Loudness** | `-16.0 LUFS ± 0.5` | **`-16.14 LUFS`** (`loudnorm` JSON on final MP4) | PASS |
| **True Peak** | `≤ -1.0 dBTP` | **`-2.10 dBTP`** (`1.10 dB` safety margin) | PASS |
| **Silence Check (`-40dB`, `1s`)** | No dead hole / no gap `> 1.2 s` | `0` silences `> 1.0 s` on full mix; max pause on soloed dialogue stem is **`1.171 s`** (`< 1.20 s`) | PASS |
| **Black / Freeze Check (`>0.5s`)** | `0` segments `> 0.5 s` | `0` black `> 0.5 s`; `0` frozen `> 0.5 s` | PASS |
| **House-Look Color & Scale** | `500T` LUT + halation + valley scale | `10` exterior gorge/dam/town plates, `4` `33^3` `.cube` LUTs (`black_floor=0.004`), `[1.0, 0.38, 0.08]` halation, rain + mist | PASS |
| **Caption Legibility & Sync** | `2–5` words/cue, `≥ 40 px`, `WordBoundary` | `52 px` `InterDisplay-Bold`, **`39` cues strictly `3–5` words** (`0.000 s` drift; `#F5D14E` / White / `#EA443C`) | PASS |
| **Git Discipline (Rule 11)** | Pre-render Wall-Frame & script; render before polish | `2f9d43d` (`script.md` + pre-render `QA.md` Wall-Frame) → `bcb3a75` (plates/LUTs/stems) → `50fe807` (render checkpoint) → `QA.md` polish | PASS |
| **Wall-Frame & Stills** | `≥ 3` stills + 1 wall-worthy frame | `6` PNG stills incl. `stills/wall_frame_mark_seven_clean.png` (Shot 08 flooded Main Street & `MARK SEVEN` lamp) | PASS |
| **Workspace Budget** | `/home/user` `< 128 MB` | `< 122 MB` (`< 128 MB` snapshot budget) | PASS |

---

## 4. Caption Cue Alignment (`39` House-Look `3–5` Word `WordBoundary`-Locked Cues, `0.000 s` Drift)

| Cue | Spk | Shot | Words | Caption Cue (`s`) | Speech (`WordBoundary`) (`s`) | Drift (`s`) | Display Text |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 01 | `A` | 01 | `4` | `0.440–2.757` | `0.440–2.757` | `0.000` | `Three fourteen thirty-seven minutes` |
| 02 | `A` | 01 | `4` | `2.772–4.162` | `2.772–4.162` | `0.000` | `after Vault Six flooded` |
| 03 | `A` | 01 | `4` | `4.176–5.608` | `4.176–5.608` | `0.000` | `inside the dam and` |
| 04 | `A` | 01 | `4` | `5.623–6.775` | `5.623–6.775` | `0.000` | `the gorge is full` |
| 05 | `B` | 02 | `4` | `7.640–9.358` | `7.640–9.358` | `0.000` | `Lowgate levee two miles` |
| 06 | `B` | 02 | `4` | `9.371–10.873` | `9.371–10.873` | `0.000` | `downstream every house is` |
| 07 | `B` | 02 | `4` | `10.885–12.364` | `10.885–12.364` | `0.000` | `empty and black water` |
| 08 | `B` | 02 | `5` | `12.376–13.662` | `12.376–13.662` | `0.000` | `is across the rail yard` |
| 09 | `A` | 03 | `4` | `14.527–16.128` | `14.527–16.128` | `0.000` | `All four spillway gates` |
| 10 | `A` | 03 | `4` | `16.142–17.448` | `16.142–17.448` | `0.000` | `are wide open and` |
| 11 | `A` | 03 | `4` | `17.463–18.586` | `17.463–18.586` | `0.000` | `the canyon crest is` |
| 12 | `A` | 03 | `5` | `18.600–20.482` | `18.600–20.482` | `0.000` | `passing the railway bridge now` |
| 13 | `B` | 04 | `4` | `21.347–22.597` | `21.347–22.597` | `0.000` | `White water is hitting` |
| 14 | `B` | 04 | `4` | `22.609–23.522` | `22.609–23.522` | `0.000` | `the steel girders on` |
| 15 | `B` | 04 | `4` | `23.535–24.785` | `23.535–24.785` | `0.000` | `the bridge and backing` |
| 16 | `B` | 04 | `4` | `24.797–26.431` | `24.797–26.431` | `0.000` | `slow water down Main Street` |
| 17 | `A` | 05 | `4` | `27.296–28.672` | `27.296–28.672` | `0.000` | `Marks One through Five` |
| 18 | `A` | 05 | `4` | `28.687–29.501` | `28.687–29.501` | `0.000` | `are on the dam` |
| 19 | `A` | 05 | `4` | `29.782–30.863` | `29.782–30.863` | `0.000` | `Six was the vault` |
| 20 | `A` | 05 | `4` | `31.130–32.297` | `31.130–32.297` | `0.000` | `where is Mark Seven` |
| 21 | `B` | 06 | `4` | `33.162–34.040` | `33.162–34.040` | `0.000` | `Not on the dam` |
| 22 | `B` | 06 | `4` | `34.316–35.759` | `34.316–35.759` | `0.000` | `they stenciled Mark Seven` |
| 23 | `B` | 06 | `4` | `35.770–36.960` | `35.770–36.960` | `0.000` | `on the iron streetlamp` |
| 24 | `B` | 06 | `4` | `36.972–37.910` | `36.972–37.910` | `0.000` | `in the town square` |
| 25 | `A` | 07 | `4` | `38.775–39.463` | `38.775–39.463` | `0.000` | `Tell me where the` |
| 26 | `A` | 07 | `5` | `39.477–41.037` | `39.477–41.037` | `0.000` | `water is on that post` |
| 27 | `B` | 08 | `4` | `41.902–42.743` | `41.902–42.743` | `0.000` | `The amber lamp is` |
| 28 | `B` | 08 | `4` | `42.756–43.909` | `42.756–43.909` | `0.000` | `still burning and the` |
| 29 | `B` | 08 | `4` | `43.921–45.087` | `43.921–45.087` | `0.000` | `river just stopped two` |
| 30 | `B` | 08 | `4` | `45.099–46.470` | `45.099–46.470` | `0.000` | `inches below Mark Seven` |
| 31 | `A` | 09 | `4` | `47.497–49.239` | `47.497–49.239` | `0.000` | `Drowning one concrete room` |
| 32 | `A` | 09 | `4` | `49.253–50.573` | `49.253–50.573` | `0.000` | `inside the dam took` |
| 33 | `A` | 09 | `3` | `50.587–51.486` | `50.587–51.486` | `0.000` | `two inches off` |
| 34 | `A` | 09 | `3` | `51.500–52.680` | `51.500–52.680` | `0.000` | `a three-mile river` |
| 35 | `B` | 10 | `4` | `53.545–54.879` | `53.545–54.879` | `0.000` | `Four thousand people left` |
| 36 | `B` | 10 | `4` | `54.891–55.540` | `54.891–55.540` | `0.000` | `their keys on the` |
| 37 | `B` | 10 | `4` | `55.552–57.019` | `55.552–57.019` | `0.000` | `counter and their town` |
| 38 | `B` | 10 | `3` | `57.031–57.932` | `57.031–57.932` | `0.000` | `is still standing` |
| 39 | `B` | 10 | `3` | `57.944–58.810` | `57.944–58.810` | `0.000` | `at Mark Seven` |

---

## 5. Verbatim Command Outputs (`ffprobe`, `loudnorm`, `silencedetect` on Durable Repo Paths)

### 5.1 Verbatim `ffprobe` on Final Deliverable (`videos/team-b/grade-v08/video.mp4`, SHA256 `45a68bbc6ba6df00c6200df1933408986790f4260dfa1720d13530a5fed17ab2`)

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
            "bit_rate": "4044265",
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
            "time_base": "1/48000",
            "start_pts": 0,
            "start_time": "0.000000",
            "duration_ts": 2880000,
            "duration": "60.000000",
            "bit_rate": "192713",
            "nb_frames": "2814"
        }
    ],
    "format": {
        "filename": "videos/team-b/grade-v08/video.mp4",
        "nb_streams": 2,
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "start_time": "0.000000",
        "duration": "60.000000",
        "size": "31845395",
        "bit_rate": "4246052",
        "probe_score": 100
    }
}
```

### 5.2 Verbatim `loudnorm` JSON Measurement on `videos/team-b/grade-v08/video.mp4`

```json
{
	"input_i" : "-16.14",
	"input_tp" : "-2.10",
	"input_lra" : "2.40",
	"input_thresh" : "-26.16",
	"output_i" : "-16.01",
	"output_tp" : "-1.96",
	"output_lra" : "2.10",
	"output_thresh" : "-26.02",
	"normalization_type" : "dynamic",
	"target_offset" : "0.01"
}
```

### 5.3 `ffprobe` & `silencedetect=n=-40dB:d=1` on Committed Stems & Final Mix

```text
--- videos/team-b/grade-v08/audio/voice_A_crest_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=1401678

--- videos/team-b/grade-v08/audio/voice_B_levee_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=1258436

--- videos/team-b/grade-v08/audio/dialogue_stem_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=2642581

--- videos/team-b/grade-v08/audio/bed_ducked_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=4741939

# ffmpeg -i videos/team-b/grade-v08/audio/dialogue_stem_48k.flac -af silencedetect=n=-40dB:d=1 -f null -
silence_end: 14.686958 | silence_duration: 1.001896
silence_end: 27.456979 | silence_duration: 1.008250
silence_end: 47.645729 | silence_duration: 1.170542
silence_end: 60.000000 | silence_duration: 1.162438

# ffmpeg -i videos/team-b/grade-v08/video.mp4 -af silencedetect=n=-40dB:d=1 -f null -
0 silences > 1.0 s on full mix
```

---

## 6. Reproducibility, Asset Licences & Blunt Self-Review

### Reproducible Build Commands (Offline Default)
```bash
pip install -r videos/team-b/grade-v08/requirements.txt
python3 videos/team-b/grade-v08/build_v08.py
```

### First-Party Asset Provenance & Licences
- **Visual Plates (`plates/shot_01.jpg`–`shot_10.jpg`):** `10/10` original first-party `1920×1080` exterior valley, dam, bridge, and flooded-town plates generated specifically for `grade-v08` by `grade` (`0` stock footage, `0` reused prior-wave plates, `0` watermarks).
- **3D LUTs (`luts/*.cube`):** Four original `33×33×33` `500T` film-emulsion `.cube` LUTs (`valley_obsidian_500t.cube`, `gorge_cyan_6500k.cube`, `spillway_storm_7000k.cube`, `lowgate_sodium_2600k.cube`) generated procedurally by `generate_luts.py`.
- **Voices, Score & Foley (`build_audio_v08.py` + `audio/*.flac`):** Two-station synthetic neural TTS (`edge-tts`: `en-US-ChristopherNeural`, `en-GB-SoniaNeural`) + 100% first-party procedural NumPy/SciPy canyon storm rain, spillway roar, `< 310 Hz` bowed C-Phrygian-to-open-fifth sub-cello score, and spatialized relay/VHF/water foley.

### Blunt Self-Review
- **What is strong:** Choosing **scale (`a place larger than a room`)** rather than a fourth voice gives the entire `MARK` tetralogy an earned, architectural ending: stepping out of the concrete dam vaults into a three-mile basalt gorge and an evacuated river town reveals that Vault Six's sacrifice in *MARK SIX* shaved two inches off the river—the exact two inches keeping **`MARK SEVEN`** dry on the cast-iron streetlamp in the middle of Main Street (**Shot 08**, `stills/wall_frame_mark_seven_clean.png`). Every frame holds the `500T` `0.004` shadow crush, cold storm mist, wet mirror reflections, and single warm `2600K` practical at landscape scale.
- **What is weak:** Camera push-ins, rain streaks, and canyon mist remain 2.5D optical composites over still plates rather than true 3D fluid dynamics (within the `2 GB` sandbox RAM ceiling), and both stations are synthetic neural TTS verified numerically without human ears judging subtle dramatic cadence.
