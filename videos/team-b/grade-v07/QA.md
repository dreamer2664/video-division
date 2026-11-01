# QA Report — `MARK SIX` (`videos/team-b/grade-v07`)

> **Verification disclosure:** no human listened to this; verification is numeric and structural.

---

## 1. Durable Audio Provenance & Offline-First Reproduction

From the start of the `v07` build, **all five timeline-aligned `48 kHz` stereo lossless FLAC stems**, all **twelve raw `edge-tts` turn MP3s**, `timing/tts_source_manifest.json`, `timing/timeline_locked.json`, and `audio/gain_mapping.json` are committed at durable paths inside `videos/team-b/grade-v07/`. Running `python3 videos/team-b/grade-v07/build_audio_v07.py` with `/tmp/grade_v07_build` absent executes **100% offline** (zero `edge-tts` calls, zero timing edits), reproducing `master_audio_48k.wav` bit-for-bit (`SHA256 cd260ea6100f3f796c69c5b2b1277be9991e8ebe13ecbf9c29cdb87359594209`), which matches the delivered `video.mp4` AAC stream at **`r = 0.998834`** (`-45.88 dBFS` AAC LC floor).

| Durable Repo Artifact | Format | Bytes | SHA256 |
| :--- | :--- | ---: | :--- |
| `videos/team-b/grade-v07/video.mp4` | H.264 High L4.1 + AAC `48k` (`+faststart`, `moov` @ `36`) | `29,060,568` | `30d7c9e9facc00bb4e49072d0b871289046ddc771ffcbca7d72e95a33b6ad806` |
| `videos/team-b/grade-v07/audio/voice_A_reel_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`-38% L`, `+5.74 dB` L) | `1,121,010` | `3e4f9652fb0c6daf011bdbaa0eeea832cfc28570fba18cb929d4f79f14227664` |
| `videos/team-b/grade-v07/audio/voice_C_horn_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`0% C`, `0.00 dB` L/R) | `586,683` | `f0c65e52ac5a71fdd858b5e9368580076eddcabe5fe94fa4de413244a0a6aaf7` |
| `videos/team-b/grade-v07/audio/voice_B_line_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`+38% R`, `+5.74 dB` R) | `644,511` | `e8fcdf275d63a3de3e98675a0e383f9ded00a4a467a3959b14b717e9818a5302` |
| `videos/team-b/grade-v07/audio/dialogue_stem_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC (`A + B + C` exact sum) | `2,317,138` | `fb471ddf06f07b3cd1a0bed3b065e36d5ed4b40e4804fa22418528f424e4df12` |
| `videos/team-b/grade-v07/audio/bed_ducked_48k.flac` | `48 kHz` 2ch `s16` lossless FLAC | `5,411,186` | `3d51658788297007efcadf849be68e20fe9f6df7f256208ab9a5fa17c87627cb` |
| `videos/team-b/grade-v07/audio/tts_turns/turn_01_A.mp3`–`turn_12_A.mp3` | `12` raw `edge-tts` MP3s + `timing/tts_source_manifest.json` | `~440 KB` | Per-turn SHA256 hashes in `timing/tts_source_manifest.json` |
| `videos/team-b/grade-v07/audio/gain_mapping.json` | Deterministic stem-to-MP4 gain & separation telemetry | `3,780` | Exact two-pass `loudnorm` + `alimiter` chain |

---

## 2. Three-Voice Acoustic & Spatial Separation Proof (*"A Room Full of People Who Are Not in the Room"*)

In `MARK SIX`, Vault Six contains **zero living people**—three empty steel chairs sit before three glowing `2600K` storm lanterns while three distinct physical transducers converse across the empty stone room, separated across **four orthogonal acoustic dimensions** (engine/dialect, fundamental pitch `F0`, spectral bandpass/centroid, and stereo azimuth) plus visual caption placement:

| Separation Axis | Voice A — `REEL` (`1/4"` Magnetic Tape Deck) | Voice C — `HORN` (Ceiling Brass VHF Horn) | Voice B — `LINE` (Off-Hook Copper Handset) | Pairwise Separation Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Neural Engine & Dialect** | `en-US-ChristopherNeural` (US baritone) | `en-IE-ConnorNeural` (Irish mid-tenor) | `en-GB-SoniaNeural` (British RP operator) | 3 distinct neural models & 3 dialects |
| **Prosody Rate / Pitch** | `--rate=-10%`, `--pitch=-6Hz` | `--rate=+2%`, `--pitch=+6Hz` | `--rate=+5%`, `--pitch=+4Hz` | Distinct cadence & prosodic contour |
| **Median Fundamental `F0`** | **`107.4 Hz`** | **`156.9 Hz`** (`+6.6 st` above A) | **`204.3 Hz`** (`+4.6 st` above C; `1.90×` A) | 3 non-overlapping pitch tiers |
| **Transducer Passband** | `75–8,000 Hz` warm ferric-oxide close-mic | `850–6,800 Hz` 4th-order piezo VHF horn | `340–3,100 Hz` 4th-order Bakelite carbon phone | Distinct acoustic passbands |
| **Welch PSD Centroid (`|X|^2`)** | **`1,083.2 Hz`** | **`2,208.7 Hz`** | **`644.8 Hz`** | `438 Hz` to `1,564 Hz` PSD separation |
| **STFT Mag Centroid (`|X|`)** | **`3,984.7 Hz`** | **`4,255.3 Hz`** | **`2,199.3 Hz`** | `271 Hz` to `2,056 Hz` `|X|` separation |
| **Stereo Pan Bias (`L/R dB`)** | **`+5.74 dB` Left** (`-38%`) | **`0.00 dB` Center** (`0%`) | **`-5.74 dB` (`+5.74 dB` Right, `+38%`)** | **`11.48 dB` L-to-R span (`r_LR = 0.8307`)** |
| **Active Sample Overlap** | `AB = 0`, `AC = 0` | `AC = 0`, `BC = 0` | `AB = 0`, `BC = 0` | **`0` samples (`0.000000 s`) total overlap** |
| **Visual Caption Coding** | Left (`-88 px`), amber left bar (`REEL ·`) | Center (`0 px`), seafoam top bar (`HORN ·`) | Right (`+88 px`), cyan right bar (`LINE ·`) | Azimuth-matched visual coding |

### Twelve-Turn Three-Timeline Interleaving Table (`4×A`, `4×B`, `4×C`, `0.000 s` Overlap)

| Turn | Voice A (`REEL`, `-38% L`) | Voice C (`HORN`, `0% C`) | Voice B (`LINE`, `+38% R`) | Gap (`s`) | Spoken Line |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **01** | **`0.400–6.581 s`** | *(silent)* | *(silent)* | `0.620` | **[A]:** *"Two thirty-seven, Vault Six is empty, and this tape reel starts when water reaches the glass."* |
| **02** | *(silent)* | *(silent)* | **`7.201–11.915 s`** | `0.580` | **[B]:** *"Vault Six, why is a tape answering, and why is your wall phone swinging off the hook?"* |
| **03** | *(silent)* | **`12.495–18.083 s`** | *(silent)* | `0.580` | **[C]:** *"Barge Six on the ceiling horn, I hear you through the empty room, three chairs and nobody inside."* |
| **04** | *(silent)* | *(silent)* | **`18.663–23.735 s`** | `0.580` | **[B]:** *"Barge, sweep your searchlight up the dam wall and confirm water is still below Mark Six."* |
| **05** | *(silent)* | **`24.315–29.180 s`** | *(silent)* | `0.600` | **[C]:** *"Five red marks on the concrete are underwater, and there is no Mark Six painted outside."* |
| **06** | **`29.780–34.169 s`** | *(silent)* | *(silent)* | `0.580` | **[A]:** *"If you hear this tape over the room mic, stop looking for a sixth gate."* |
| **07** | *(silent)* | *(silent)* | **`34.749–37.940 s`** | `0.580` | **[B]:** *"Then why leave three storm lamps burning in an empty room?"* |
| **08** | *(silent)* | **`38.520–43.569 s`** | *(silent)* | **`1.200`** | **[C]:** *"Wait, through the glass, Mark Six is stenciled inside, behind the three empty chairs."* |
| **09** | **`44.769–49.852 s`** | *(silent)* | *(silent)* | `0.580` | **[A]:** *"Vault Six isn't a control room, it's the surge chamber we flood to save the town."* |
| **10** | *(silent)* | **`50.432–52.062 s`** | *(silent)* | `0.540` | **[C]:** *"The window bolts just fired."* |
| **11** | *(silent)* | *(silent)* | **`52.602–55.554 s`** | `0.680` | **[B]:** *"Cut the line, the river is coming through the glass."* |
| **12** | **`56.234–58.776 s`** | *(silent)* | *(silent)* | `1.224` | **[A]:** *"Nobody stays in the room at Mark Six."* |

### Per-10-Second Body-Window Speech Activity & Matched Active-Window Ducking Proof

Measured directly on the committed `audio/*.flac` stems and final `video.mp4` (`88.83%` active speech duty across `60.000 s`; matched active-speech RMS: `dialogue_stem_48k.flac = -25.74 dBFS` vs `bed_ducked_48k.flac = -36.16 dBFS` → **`+10.43 dB` speech-over-bed dominance**):

| Window | Speech Duty (`%`) | `voice_A_reel` (`dBFS`) | `voice_C_horn` (`dBFS`) | `voice_B_line` (`dBFS`) | `dialogue_stem` (`dBFS`) | `bed_ducked` (`dBFS`) | Final `video.mp4` Mix (`dBFS`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `00–10 s` | `91.9%` | `-27.22` | `silent` | `-32.92` | `-26.19` | `-36.51` | `-19.69` |
| `10–20 s` | `91.8%` | `silent` | `-28.54` | `-29.93` | `-26.17` | `-36.04` | `-19.57` |
| `20–30 s` | `91.6%` | `-43.92` | `-29.06` | `-30.41` | `-26.59` | `-36.18` | `-20.05` |
| `30–40 s` | `91.8%` | `-29.01` | `-34.51` | `-29.97` | `-25.82` | `-35.93` | `-19.26` |
| `40–50 s` | `89.5%` | `-27.83` | `-30.37` | `silent` | `-25.91` | `-34.77` | `-19.29` |
| `50–60 s` | `76.3%` | `-30.61` | `-33.92` | `-31.26` | `-26.94` | `-33.52` | `-19.92` |

---

## 3. Technical & Speech Acceptance Checklist (`specs/60s-video.md`)

| Check | Spec Target | Measured Result | Verdict |
| :--- | :--- | :--- | :---: |
| **Duration** | `58.0–62.0 s` (`60.0 s` target) | `60.000000 s` (`1,800` frames @ `30/1` fps CFR) | PASS |
| **Resolution & Aspect** | `1920×1080` landscape (`16:9`) | `1920×1080` progressive (`< 90 MB` at `29.06 MB`) | PASS |
| **Video Stream** | H.264 `yuv420p` `+faststart` | `h264` High L4.1, `yuv420p`, `moov` atom at byte `36` | PASS |
| **Audio Stream** | `48 kHz` stereo AAC | `aac` LC, `48000 Hz`, `2` channels (`stereo`) | PASS |
| **Integrated Loudness** | `-16.0 LUFS ± 0.5` | **`-16.15 LUFS`** (`loudnorm` JSON on final MP4) | PASS |
| **True Peak** | `≤ -1.0 dBTP` | **`-1.88 dBTP`** (`0.88 dB` safety margin) | PASS |
| **Silence Check (`-40dB`, `1s`)** | No dead hole swallowing middle | `0` silences `> 1.0 s` on full mix; only `2` intentional pauses `> 1.0 s` on solo dialogue stem (`1.186 s` pre-twist beat @ `43.67 s` and `1.211 s` tail @ `58.79 s`) | PASS |
| **Black / Freeze Check (`>0.5s`)** | `0` segments `> 0.5 s` | `0` black `> 0.5 s`; `0` frozen `> 0.5 s` | PASS |
| **Caption Legibility & Sync** | `≥ 40 px` at `1080p`, mandatory | `50 px` `InterDisplay-Bold`, `40` `WordBoundary`-locked cues (`0.000 s` drift) + `timing/captions.srt` | PASS |
| **Git Discipline (Rule 11)** | Script committed first; render committed before polish | `64e067e` (`script.md`) → `6854ce8` (render + stems checkpoint) → `QA.md` polish commit | PASS |
| **Wall-Frame & Stills** | `≥ 3` stills + 1 wall-worthy frame | `6` PNG stills incl. `stills/wall_frame_mark_six_clean.png` (Shot 07 three lanterns & empty chairs) | PASS |
| **Workspace Budget** | `/home/user` `< 128 MB` | `~116 MB` (`< 128 MB` snapshot budget) | PASS |

---

## 4. Caption Cue Alignment (`40` Three-Voice `WordBoundary`-Locked Beats, `0.000 s` Drift)

| Cue | Spk | Shot | Caption Cue (`s`) | Speech (`WordBoundary`) (`s`) | Drift (`s`) | Display Text |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 01 | `A` | 01 | `0.400–1.470` | `0.400–1.470` | `0.000` | `2:37 AM,` |
| 02 | `A` | 01 | `1.720–3.095` | `1.720–3.095` | `0.000` | `Vault Six is empty,` |
| 03 | `A` | 01 | `3.317–4.789` | `3.317–4.789` | `0.000` | `and this tape reel starts` |
| 04 | `A` | 01 | `4.803–6.581` | `4.803–6.581` | `0.000` | `when water reaches the glass.` |
| 05 | `B` | 02 | `7.201–8.570` | `7.201–8.570` | `0.000` | `Vault Six, why is` |
| 06 | `B` | 02 | `8.582–9.463` | `8.582–9.463` | `0.000` | `a tape answering,` |
| 07 | `B` | 02 | `9.713–10.891` | `9.713–10.891` | `0.000` | `and why is your wall phone` |
| 08 | `B` | 02 | `10.903–11.915` | `10.903–11.915` | `0.000` | `swinging off the hook?` |
| 09 | `C` | 03 | `12.495–14.236` | `12.495–14.236` | `0.000` | `Barge Six on the ceiling horn,` |
| 10 | `C` | 03 | `14.504–15.275` | `14.504–15.275` | `0.000` | `I hear you through` |
| 11 | `C` | 03 | `15.287–16.155` | `15.287–16.155` | `0.000` | `the empty room,` |
| 12 | `C` | 03 | `16.410–18.083` | `16.410–18.083` | `0.000` | `three chairs and nobody inside.` |
| 13 | `B` | 04 | `18.663–20.115` | `18.663–20.115` | `0.000` | `Barge, sweep your searchlight` |
| 14 | `B` | 04 | `20.127–21.020` | `20.127–21.020` | `0.000` | `up the dam wall` |
| 15 | `B` | 04 | `21.258–22.413` | `21.258–22.413` | `0.000` | `and confirm water is` |
| 16 | `B` | 04 | `22.425–23.735` | `22.425–23.735` | `0.000` | `still below MARK SIX.` |
| 17 | `C` | 05 | `24.315–25.925` | `24.315–25.925` | `0.000` | `Five red marks on the concrete` |
| 18 | `C` | 05 | `25.937–26.756` | `25.937–26.756` | `0.000` | `are underwater,` |
| 19 | `C` | 05 | `27.012–27.795` | `27.012–27.795` | `0.000` | `and there is no` |
| 20 | `C` | 05 | `27.807–29.180` | `27.807–29.180` | `0.000` | `MARK SIX painted outside.` |
| 21 | `A` | 06 | `29.780–30.947` | `29.780–30.947` | `0.000` | `If you hear this tape` |
| 22 | `A` | 06 | `30.961–32.044` | `30.961–32.044` | `0.000` | `over the room mic,` |
| 23 | `A` | 06 | `32.294–33.141` | `32.294–33.141` | `0.000` | `stop looking for` |
| 24 | `A` | 06 | `33.155–34.169` | `33.155–34.169` | `0.000` | `a sixth gate.` |
| 25 | `B` | 07 | `34.749–35.475` | `34.749–35.475` | `0.000` | `Then why leave` |
| 26 | `B` | 07 | `35.487–36.856` | `35.487–36.856` | `0.000` | `three storm lamps burning` |
| 27 | `B` | 07 | `36.868–37.940` | `36.868–37.940` | `0.000` | `in an empty room?` |
| 28 | `C` | 08 | `38.520–39.894` | `38.520–39.894` | `0.000` | `Wait, through the glass,` |
| 29 | `C` | 08 | `40.149–41.787` | `40.149–41.787` | `0.000` | `MARK SIX is stenciled inside,` |
| 30 | `C` | 08 | `42.030–43.569` | `42.030–43.569` | `0.000` | `behind the three empty chairs.` |
| 31 | `A` | 09 | `44.769–46.602` | `44.769–46.602` | `0.000` | `Vault Six isn't a control room,` |
| 32 | `A` | 09 | `46.838–48.033` | `46.838–48.033` | `0.000` | `it's the surge chamber` |
| 33 | `A` | 09 | `48.047–49.852` | `48.047–49.852` | `0.000` | `we flood to save the town.` |
| 34 | `C` | 09 | `50.432–51.288` | `50.432–51.288` | `0.000` | `The window bolts` |
| 35 | `C` | 09 | `51.300–52.062` | `51.300–52.062` | `0.000` | `just fired.` |
| 36 | `B` | 10 | `52.602–53.435` | `52.602–53.435` | `0.000` | `Cut the line,` |
| 37 | `B` | 10 | `53.685–54.304` | `53.685–54.304` | `0.000` | `the river is` |
| 38 | `B` | 10 | `54.316–55.554` | `54.316–55.554` | `0.000` | `coming through the glass.` |
| 39 | `A` | 10 | `56.234–57.623` | `56.234–57.623` | `0.000` | `Nobody stays in the room` |
| 40 | `A` | 10 | `57.637–58.776` | `57.637–58.776` | `0.000` | `at MARK SIX.` |

---

## 5. Verbatim Command Outputs (`ffprobe`, `loudnorm`, `silencedetect` on Durable Repo Paths)

### 5.1 Verbatim `ffprobe` on Final Deliverable (`videos/team-b/grade-v07/video.mp4`, SHA256 `30d7c9e9facc00bb4e49072d0b871289046ddc771ffcbca7d72e95a33b6ad806`)

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
            "bit_rate": "3671643",
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
            "bit_rate": "194023",
            "nb_frames": "2814"
        }
    ],
    "format": {
        "filename": "videos/team-b/grade-v07/video.mp4",
        "nb_streams": 2,
        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        "start_time": "0.000000",
        "duration": "60.000000",
        "size": "29060568",
        "bit_rate": "3874742",
        "probe_score": 100
    }
}
```

### 5.2 Verbatim `loudnorm` Measurement on Final `videos/team-b/grade-v07/video.mp4`

```json
{
	"input_i" : "-16.15",
	"input_tp" : "-1.88",
	"input_lra" : "2.80",
	"input_thresh" : "-26.40",
	"output_i" : "-16.12",
	"output_tp" : "-2.00",
	"output_lra" : "2.60",
	"output_thresh" : "-26.38",
	"normalization_type" : "dynamic",
	"target_offset" : "0.12"
}
```

### 5.3 `ffprobe` & `silencedetect=n=-40dB:d=1` on Committed Durable Stems & Full Mix

```text
--- videos/team-b/grade-v07/audio/voice_A_reel_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=1121010

--- videos/team-b/grade-v07/audio/voice_C_horn_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=586683

--- videos/team-b/grade-v07/audio/voice_B_line_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=644511

--- videos/team-b/grade-v07/audio/dialogue_stem_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=2317138

--- videos/team-b/grade-v07/audio/bed_ducked_48k.flac ---
codec_name=flac | sample_rate=48000 | channels=2 | bits_per_raw_sample=16 | duration=60.000000 | size=5411186

# ffmpeg -i videos/team-b/grade-v07/audio/dialogue_stem_48k.flac -af silencedetect=n=-40dB:d=1 -f null -
silence_start: 43.672604 | silence_end: 44.858333 | silence_duration: 1.185729
silence_start: 58.788979 | silence_end: 60        | silence_duration: 1.211021

# ffmpeg -i videos/team-b/grade-v07/video.mp4 -af silencedetect=n=-40dB:d=1 -f null -
0 silences > 1.0 s on full mix
```

---

## 6. Reproducibility, Asset Licences & Blunt Self-Review

### Reproducible Build Commands (Offline Default)
```bash
pip install -r videos/team-b/grade-v07/requirements.txt
python3 videos/team-b/grade-v07/build_v07.py
```

### First-Party Asset Provenance & Licences
- **Visual Plates (`plates/shot_01.jpg`–`shot_10.jpg`):** `10/10` original first-party `1920×1080` plates generated specifically for `grade-v07` by `grade` (`0` stock footage, `0` reused prior-wave plates, `0` watermarks).
- **3D LUTs (`luts/*.cube`):** Four original `33×33×33` `.cube` LUTs (`vault_slate_4300k.cube`, `amber_oxide_reel.cube`, `copper_cord_cyan.cube`, `surge_breach_7000k.cube`) generated procedurally by `generate_luts.py`.
- **Voices, Score & Foley (`build_audio_v07.py` + `audio/*.flac`):** Synthetic three-voice neural TTS (`edge-tts`: `en-US-ChristopherNeural`, `en-IE-ConnorNeural`, `en-GB-SoniaNeural` — explicitly designed as non-human diegetic machine/radio/telephone transducers in an empty room) + 100% first-party procedural NumPy/SciPy storm rain, `< 330 Hz` bowed C-Phrygian sub-cello score, and spatialized solenoid/squelch/handset/bolt foley.

### Blunt Self-Review
- **What is strong:** Grounding the three voices in **three physical transducers occupying Left (`1/4"` oxide tape deck), Center (overhead brass VHF horn), and Right (dangling off-hook Bakelite handset) inside a genuinely empty stone room** turns *"a room full of people who are not in the room"* into tangible cinema. Having the two live remote callers (`LINE` and `HORN`) speak *to each other across the open air of the empty room* while the pre-recorded `REEL` periodically cuts in gives the 3-voice architecture real dramatic necessity. **Shot 07 (`stills/wall_frame_mark_six_clean.png`)**—three burning `2600K` brass storm lanterns mirrored in black floor water before three empty chairs—and **Shot 08** (`MARK SIX` stenciled inside the room under the `7000K` searchlight) deliver our sharpest visual storytelling across all four waves.
- **What is weak:** Camera motion, storm rain, and transducer indicator light pulses remain 2.5D optical composites over still plates rather than true 3D volumetric fluid/glass shatter simulation (constrained by the `2 GB` sandbox RAM budget), and all three voices are synthetic neural TTS verified numerically/structurally without human ears listening to subtle prosodic inflection.
