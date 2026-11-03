# `ab-grade` Operational Guide — Reading the Metrics Table & Unified Film Finishing

**Owner:** `grade` (Team B)  
**Artifacts & Reproducer:** `research/ab-grade/` · `research/ab-grade/metrics.json` · `python3 research/build_ab_benchmark.py` (`0` API calls, 100% offline)  
**3D Print LUT:** `research/ab-grade/stills/kodak_5219_2383_house.cube` (`33×33×33`, `SHA256 c3f67dbb45b0322f71afac0ad7066acb65ec5281dbbee12a55534596c312fa3d`)

---

## 1. How to Read the `ab-grade` Metrics Table

`python3 research/build_ab_benchmark.py` emits `research/ab-grade/metrics.json` (summarized in `research/ab-grade/README.md`), measuring every plate and voice stem **before** and **after** treatment so grading and mixing decisions are audited numerically rather than by eye/ear alone.

### 1.1 Image Grading Columns (`image_benchmarks.stills` & `cross_shot_consistency`)

| Metric Column | Unit | What It Measures Physically | House Target / Pass Band | Failure Signature |
| :--- | :--- | :--- | :--- | :--- |
| **`Toe P01` / `P02`** | `IRE` (`0–100`) | 1st / 2nd percentile luminance — optical `D_max` shadow floor of Kodak `2383` print stock. | **`2.5 – 3.1 IRE`** (`P02` cross-shot `σ < 0.10 IRE`; measured `0.054 IRE`, **`5.9×` tighter** than raw `0.321 IRE`) | `< 0.8 IRE` = crushed digital OLED void; `> 5.0 IRE` = washed-out milky gray lift. |
| **`Median Y`** | `IRE` (`0–100`) | Scene midtone placement (`P50` luma). | **`11.5 – 17.5 IRE`** (low-key theatrical) or consistent register anchor | Large cut-to-cut jumps (`> 1.5 stops`) flash the viewer's eye on hard cuts. |
| **`before/after_midtone_range_stops`** | `stops` (`log2`) | Max-to-min scene-linear median luminance ratio across consecutive shots in a reel. | **`< 1.0 stop`** across matched scenes (`2.295 → 0.833 stops`, **`-63.7%` jump cut**) | `> 2.0 stops` = uncalibrated per-shot AI renders that do not share one camera roll. |
| **`P95–P05 Spread`** | `IRE` | Central 90% luminance dynamic span (`Y_P95 - Y_P05`). | **`48 – 68 IRE`** | `< 35 IRE` = flat muddy plate; `> 85 IRE` = harsh unrolled digital contrast. |
| **`Entropy`** | `bits` (`0–8`) | 256-bin Shannon tonal entropy `-∑ p log2(p)` across `[0, 1]` luma. | **`>= 6.80 bits`** | Low entropy (`< 6.2 bits`) = posterized banding or clumped shadow/highlight spikes. |
| **`Crushed <0.8` / `Clipped >99.2`** | `%` of pixels | Fraction of frame lost to pure zero black (`< 0.8 IRE`) or hard full-scale clip (`> 99.2 IRE` in any RGB channel). | **`0.00% / 0.00%`** | Raw AI plates routinely crush `1.5–8.0%` of shadows and hard-clip emitter cores. |
| **`Mid/Shad` & `High/Mid`** | `stops` (`log2`) | Scene-linear luminance ratios `μ_mid / μ_shad` (`P25–P75` vs `<P25`) and `μ_high / μ_mid` (`>P75` vs `P25–P75`). | **`2.4 – 3.3 stops`** (Mid/Shad) · **`2.4 – 3.6 stops`** (High/Mid) | `< 1.8 stops` = mushy zone collapse; `> 4.0 stops` = harsh digital specular snap. |
| **`Warm/Cool ΔChroma`** | `CIE ΔE*ab` | Chromatic distance `hypot(Δa*, Δb*)` between top warm practical pixels and cool ambient shadow/water pixels in CIE `1976 L*a*b*`. | **`>= 22 ΔE*ab`** with `120°–165°` hue opposition | `< 12 ΔE*ab` = monochromatic color wash where practical lamps fail to separate from walls. |
| **`Max Chroma P99`** | `C*ab` | 99th-percentile CIE `L*a*b*` chroma `sqrt(a*^2 + b*^2)` — Beer-Lambert subtractive dye guard check. | **`<= 46 C*ab`** | `> 50 C*ab` = radioactive additive neon cyan/green LEDs that read as CGI rather than film dye. |

### 1.2 Voice Chain Columns (`voice_benchmarks`)

| Metric Column | Unit | What It Measures Physically | House Target / Pass Band |
| :--- | :--- | :--- | :--- |
| **`Integrated Loudness` / `TP`** | `LUFS` / `dBTP` | ITU-R BS.1770-4 / EBU R128 integrated loudness and `4×` oversampled True Peak. | **`-16.0 ± 0.2 LUFS`** · **`TP <= -1.5 dBTP`** |
| **`Spectral Tilt 100–8k`** | `dB/octave` | Log-frequency Welch PSD slope across `100–8,000 Hz`. | **`-3.3 to -4.8 dB/oct`** (`> -2.7 dB/oct` indicates buzzy first-gen TTS vocoder harmonics) |
| **`Sibilance 6–8.5k`** | `dB` rel. body | `6.0–8.5 kHz` fricative energy relative to `100–500 Hz` chest body. | **`-14.0 to -17.5 dB`** (`> -11.5 dB` = harsh un-de-essed synthetic `s/sh` bursts) |
| **`F0 Med` & `F0 Core IQR`** | `Hz` & `semitones` | Median fundamental pitch and interquartile (`P75 - P25`) melodic movement across voiced frames. | **`IQR >= 5.0 st`** for expressive narration (`< 4.3 st` = mean-collapsed monotone corridor) |

---

## 2. Applying `kodak_5219_2383_house.cube` + Voice `loudnorm` in One Pipeline (Cross-Referencing `scripts/render_15s.sh`)

Tally's reproducible proof script [**`scripts/render_15s.sh`**](../../scripts/render_15s.sh) runs three steps:
1. `scripts/make_cue_sheet.py` → `cue_sheets/sleep_premise/cue_sheet.json`
2. `scripts/gen_voice.py` → `audio/15s_proof/voice.mp3` + `word_timestamps.json` (skipped offline when `ELEVENLABS_API_KEY` is unset)
3. `scripts/render_counter.py` → encodes raw sRGB PNG frames + `apad`-padded `voice.mp3` to `output/15s_counter.mp4`

Measured directly on `origin/main`'s `output/15s_counter.mp4`, step `[3/3]` currently emits **ungraded raw sRGB** video and **`-24.26 LUFS / -7.81 dBTP`** audio (`8.26 LU` below division target). Below are the two exact ways to wire the `ab-grade` `.cube` LUT + `-16 LUFS` vocal chain into that pipeline.

### Option A — Two-Pass Finishing Command on Any Finished Film (e.g. right after `scripts/render_15s.sh`)

Run directly from the repository root on `output/15s_counter.mp4` (or any rendered `video.mp4`):

```bash
IN="output/15s_counter.mp4"
OUT="output/15s_counter_graded.mp4"
LUT="research/ab-grade/stills/kodak_5219_2383_house.cube"
VCHAIN="highpass=f=80,equalizer=f=355:t=q:w=1.85:g=-3.2,equalizer=f=3000:t=q:w=1.15:g=1.8,acompressor=threshold=-20dB:ratio=3:attack=22:release=220:makeup=2"

# Pass 1: Measure exact EBU R128 parameters after vocal EQ + 3:1 optical compression
STATS=$(ffmpeg -hide_banner -nostats -i "$IN" \
  -af "${VCHAIN},loudnorm=I=-16:TP=-1.8:LRA=11:print_format=json" \
  -f null - 2>&1 | sed -n '/{/,/}/p')

IN_I=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["input_i"])' <<< "$STATS")
IN_TP=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["input_tp"])' <<< "$STATS")
IN_LRA=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["input_lra"])' <<< "$STATS")
IN_TH=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["input_thresh"])' <<< "$STATS")
OFFSET=$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["target_offset"])' <<< "$STATS")

# Pass 2: Apply tetrahedral 5219->2383 3D LUT + linear -16 LUFS voice master in one encode
ffmpeg -y -v error -i "$IN" \
  -vf "format=rgb24,lut3d=file=${LUT}:interp=tetrahedral,format=yuv420p" \
  -af "${VCHAIN},loudnorm=I=-16:TP=-1.8:LRA=11:measured_I=${IN_I}:measured_TP=${IN_TP}:measured_LRA=${IN_LRA}:measured_thresh=${IN_TH}:offset=${OFFSET}:linear=true" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -r 30 \
  -c:a aac -ar 48000 -ac 2 -b:a 192k \
  -movflags +faststart \
  "$OUT"
```

*(Note: `TP=-1.8` in pre-encode `loudnorm` provides `0.3 dB` of AAC lossy-reconstruction headroom so the muxed `.mp4` always measures strictly `<= -1.50 dBTP` — verified on `output/15s_counter.mp4` at **`-16.08 LUFS / -1.81 dBTP`**).*

### Option B — Single-Encode Integration Inside `scripts/render_15s.sh` / `scripts/render_counter.py`

To avoid encoding H.264 twice, pre-treat the voice stem with `research/vocal_chain.py` (full 8-stage chain including `6–8.5 kHz` split-band de-esser and `8.7–23.8 ms` studio early reflections) between steps `[2/3]` and `[3/3]` of `scripts/render_15s.sh`, then apply `lut3d` + `loudnorm` directly in `render_counter.py`'s `ffmpeg` mux:

```bash
# Step [2.5/3] in scripts/render_15s.sh — treat dry voice stem offline via vocal_chain.py:
python3 research/vocal_chain.py audio/15s_proof/voice.mp3 /tmp/voice_treated.flac

# Step [3/3] single-pass frame + audio mux (replaces raw mux in scripts/render_counter.py):
ffmpeg -y -loglevel error \
  -framerate 30 -i /tmp/frames_15s/%05d.png \
  -i /tmp/voice_treated.flac \
  -filter_complex "\
    [0:v]format=rgb24,lut3d=file=research/ab-grade/stills/kodak_5219_2383_house.cube:interp=tetrahedral,format=yuv420p[v]; \
    [1:a]apad=pad_dur=15.0,loudnorm=I=-16:TP=-1.8:LRA=11[a]" \
  -map "[v]" -map "[a]" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -r 30 \
  -c:a aac -ar 48000 -ac 2 -b:a 192k \
  -movflags +faststart -t 15.0 \
  output/15s_counter.mp4
```

> **Note on spatial stages:** `kodak_5219_2383_house.cube` bakes the exact `5219 → 2383` S-curve, `2.6 IRE` optical black toe, Beer-Lambert subtractive dye density, and slate/amber split-tone into a zero-overhead `33³` 3D LUT (`200+ fps` in `ffmpeg`). When grading narrative photographic plates before animation, run `python3 research/grade_chain.py raw.jpg graded.png` so scene-linear `65%` cross-shot exposure anchoring, `cos⁴(θ)` prime falloff, and pre-LUT `Y_lin > 0.56` red-layer halation also execute.
