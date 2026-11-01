# `research/ab-grade/` — Reproducible Voice & Image Grading Benchmark Suite

**Author:** `grade` (Team B) · **Branch:** `grade/voice-imaging`

Every file in this directory is deterministically reproducible offline (`0` API calls, `0` network access required) from the committed `sources/` inputs by running:

```bash
python3 research/build_ab_benchmark.py
```

---

## 1. Voice Benchmark Artifacts (`research/ab-grade/audio/`)

### A. Full `v07` (*MARK SIX*) Narration — Old Chain vs New Chain (`4` Turns)
- `audio/v07_narration_old_chain.flac` (`20.53 s`, `-21.91 LUFS`, `-2.65 dB/oct` tilt, `-10.96 dB` sibilance) — exact reproduction of `v07`'s legacy `75–8,000 Hz` chain + uniform `0.58 s` digital-zero gaps.
- `audio/v07_narration_new_chain.flac` (`20.89 s`, **`-16.00 LUFS`**, **`-2.06 dBTP`**, `-3.39 dB/oct` tilt, `-14.16 dB` sibilance) — exact same raw `v07` stems processed through `research/vocal_chain.py` with asymmetric pauses and physiological pre-phrase breath/booth-air conditioning.

### B. `~15 s` Before / After Voice Sample & Honest 3-Sentence Engine A/B (`191` chars verbatim)
Script tested across every stem below:
> *"If you hear this tape over the room mic, stop looking for a sixth gate. Vault Six isn't a control room, it's the surge chamber we flood to save the town. Nobody stays in the room at Mark Six."*

| File | Description | Duration | Loudness (`LUFS` / `TP`) | Tilt (`dB/oct`) | Sibilance (`dB`) | `F0` Med (`Hz`) | `F0` Core IQR (`st`) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `audio/sample_15s_before_v07_old_chain.flac` | **BEFORE:** `edge-tts Christopher` (`-10%/-6Hz`) + Old `v07` Chain | `13.76 s` | `-21.80 / -7.82` | `-2.43` | `-10.70` | `107.95` | `4.94` |
| `audio/sample_15s_after_local_chris_new_chain.flac` | **AFTER (Local Same Voice):** `Christopher` (`0%/0Hz`) + `vocal_chain.py` | `12.91 s` | `-16.00 / -2.06` | `-3.32` | `-14.04` | `114.43` | `5.86` |
| `audio/sample_15s_after_local_brian_new_chain.flac` | **AFTER (Local Clean Tilt):** `BrianMultilingual` (`0%/0Hz`) + `vocal_chain.py` | `13.57 s` | `-16.00 / -2.07` | `-4.07` | `-17.15` | `124.28` | `4.26` |
| `audio/sample_15s_elevenlabs_v2_brian_highstab_chained.flac` | **ElevenLabs Control:** `eleven_multilingual_v2` `Brian` (`stability=0.78`) + `vocal_chain.py` | `12.75 s` | `-15.99 / -1.99` | `-4.49` | `-14.64` | `98.19` | `6.64` |
| `audio/sample_15s_elevenlabs_v2_brian_expressive_chained.flac` | **AFTER (ElevenLabs Hero):** `eleven_multilingual_v2` `Brian` (`stability=0.35, style=0.18`) + `vocal_chain.py` | `13.07 s` | `-16.00 / -1.54` | `-4.27` | `-14.66` | `105.52` | **`6.65`** |
| `audio/sample_15s_elevenlabs_v2_bill_doc_chained.flac` | **AFTER (ElevenLabs Weathered):** `eleven_multilingual_v2` `Bill` (`stability=0.38`, `...`/`—`) + `vocal_chain.py` | `16.14 s` | `-16.01 / -1.88` | `-4.07` | `-15.98` | `121.84` | `4.39` |

---

## 2. Image Grading Benchmark Artifacts (`research/ab-grade/stills/`)

- **Reusable Division 3D LUT:** `stills/kodak_5219_2383_house.cube` (`33×33×33` `.cube`, usable via `ffmpeg -vf lut3d=research/ab-grade/stills/kodak_5219_2383_house.cube`)
- **Three `1920×1080` Before / After Stills + Side-by-Side Contact Cards:**
  1. `stills/still_01_before.jpg` · `stills/still_01_after.jpg` · `stills/still_01_ab_card.jpg` (*Wide Vault Room — Lantern Practicals vs Storm Spillway*)
  2. `stills/still_02_before.jpg` · `stills/still_02_after.jpg` · `stills/still_02_ab_card.jpg` (*Overhead Vaulted Arch — Brass Horn & Distant Cage Lamp*)
  3. `stills/still_03_before.jpg` · `stills/still_03_after.jpg` · `stills/still_03_ab_card.jpg` (*Macro Sight-Glass — Oil Lantern vs Submerged Cyan Chamber*)

### Image Metrics Summary Table (`metrics.json`)

| Still | State | Toe `P01` (`IRE`) | Median `Y` (`IRE`) | `P95–P05` Spread (`IRE`) | Entropy (`bits`) | Crushed `<0.8` / Clipped `>99.2` (`%`) | Mid/Shad & High/Mid (`stops`) | Warm/Cool `ΔChroma` (`ΔE*ab`) | Max Chroma `P99` (`C*ab`) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Still 01** | Before | `0.20` | `7.63` | `45.84` | `6.497` | `7.87% / 0.44%` | `3.13 / 4.03` | `45.11` | `39.17` |
| **Still 01** | **After** | **`2.69`** | **`11.96`** | **`62.49`** | **`6.825`** | **`0.00% / 0.00%`** | **`2.56 / 3.55`** | **`43.46`** | **`36.54`** |
| **Still 02** | Before | `0.59` | `19.98` | `56.68` | `7.285` | `1.48% / 0.07%` | `3.14 / 2.55` | `27.35` | `26.26` |
| **Still 02** | **After** | **`2.72`** | **`16.60`** | **`49.03`** | **`6.947`** | **`0.00% / 0.00%`** | **`2.85 / 2.45`** | **`23.73`** | **`23.85`** |
| **Still 03** | Before | `0.25` | `9.57` | `46.53` | `6.706` | `7.81% / 0.15%` | `3.85 / 3.47` | `57.45` | `52.89` |
| **Still 03** | **After** | **`2.64`** | **`12.96`** | **`56.90`** | **`6.881`** | **`0.00% / 0.00%`** | **`3.14 / 3.09`** | **`50.73`** | **`44.53`** |

- **Cross-Shot Consistency Gain:** Inter-shot midtone exposure jump reduced by **`63.7%`** (`2.295 stops → 0.833 stops`); black-toe `P02` std tightened **`5.9×`** (`0.321 → 0.054 IRE`).

---

## 3. Standalone CLI Usage for Division Pipelines

```bash
# Treat any mono/stereo TTS or voice stem to -16.0 LUFS broadcast documentary spec:
python3 research/vocal_chain.py raw_tts.mp3 treated_vo.flac --report vo_metrics.json

# Grade any raw plate to 1920x1080 5219->2383 photochemical print + export 3D LUT:
python3 research/grade_chain.py raw_plate.jpg graded_plate.png --export-lut house.cube --report grade_metrics.json
```
