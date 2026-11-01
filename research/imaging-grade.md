# Image Grading Research — Making AI Plates Look Shot Rather Than Rendered (`imaging-grade.md`)

**Author:** `grade` (Team B — Grading Quarter of Image Quality)  
**Branch:** `grade/voice-imaging`  
**Date:** `2026-11-01`  
**Reproducible Code, LUT & Stills:** `research/grade_chain.py`, `research/build_ab_benchmark.py`, `research/ab-grade/stills/`

---

## 1. Why Raw AI Plates Read as "Rendered" (Six Physical Signatures)

Even when composition, lens choice, and prompt discipline are strong, raw generative plates exhibit six repeatable photometric tells that separate synthetic renders from `35mm` motion-picture negative (**Kodak Vision3 500T `5219`**) printed onto **Kodak `2383`** projection stock [1, 2]:

1. **Crushed Digital Zero Toe (`< 0.8 IRE`) Paired with Hard-Clipped Emitter Cores (`> 99.2 IRE`):** In our three `v07` benchmark plates, `7.87%` of `still_01` and `7.81%` of `still_03` sit below `0.8 IRE` (`P01 = 0.20–0.25 IRE` — pure OLED black holes with zero optical base density), while lantern cores clip flat at `99.2–100 IRE`.
2. **Additive Neon Gamut Spikes (Violating Subtractive Beer-Lambert Dye Physics):** On real print film, increasing dye concentration *absorbs* transmitted light — saturated blues, cyans, and greens become **darker and denser**, not brighter [2, 4]. Raw AI renders treat color additively: the junction-box green LED in `still_02` and flooded sight-glass cyan in `still_03` (`P99 C*ab = 52.89`) glow like self-luminous monitors.
3. **Missing High-Threshold Red-Layer Remjet Halation:** Amateur "film bloom" blurs everything above `50 IRE`, smearing midtone sharpness. Real `5219` anti-halation remjet absorbs normal reflections; only intense point emitters (`> 78 IRE` / `Y_lin > 0.56`) punch through the emulsion base and back-scatter **predominantly into the bottom red-sensitive layer (`R > G ≫ B`)** [1, 3].
4. **Severe Cut-to-Cut Exposure Drift (`2.30 stops` Raw Midtone Swing):** Because diffusion models normalize each prompt independently, `still_01` rendered at `Y_median = 7.63 IRE` (`Y_lin = 0.0069`) while `still_02` rendered at `Y_median = 19.98 IRE` (`Y_lin = 0.0340`) — a **`2.295-stop`** jump across a single cut!
5. **Flat Corner Illumination (No Scene-Linear `cos⁴(θ)` Optical Falloff):** Spherical cinema primes (`35mm–50mm T2.0`) naturally lose `~0.30–0.45 stops` of peripheral illuminance *before* hitting the negative; post-LUT black oval vignettes look pasted on because they crush corner black-toe density instead of attenuating scene-linear exposure.
6. **Zero Density-Proportional Dye-Cloud Granularity:** Raw AI concrete and metal surfaces have noiseless digital gradients; real `5219` exhibits channel-asymmetric silver-halide/dye-cloud granularity (`σ_B > σ_G > σ_R`, Kodak RMS diffuse granularity `~0.020` blue vs `0.006` red [1]) concentrated in mid-shadows/midtones and vanishing in both the `D_max` toe and `D_min` highlights.

---

## 2. Six-Part Grading Specification (`research/grade_chain.py` + `kodak_5219_2383_house.cube`)

### 2.1 LUT Shape (`5219` Negative Latitude → `2383` Print S-Curve + Subtractive Density)
Our committed `33×33×33` 3D LUT (`research/ab-grade/stills/kodak_5219_2383_house.cube`, usable directly in `ffmpeg` via `-vf lut3d=...`) models three coupled stages in exact `[0, 1]` sRGB-in / sRGB-out space:
- **Negative Inter-Layer Crosstalk & Beer-Lambert Subtractive Density:** A mild `3×3` crosstalk matrix (`0.94–0.96` diagonal) prevents isolated single-channel digital primaries, followed by a **subtractive chroma-density attenuator (`subtractive_density = 0.26`)** weighted toward high-saturation cyan/green (`G+B ≫ R`). Result: `still_03`'s radioactive `P99` chroma drops from **`52.89 → 44.53 C*ab`** (`-15.8%`), turning electric turquoise into deep optical storm water while keeping tungsten-cyan hue opposition intact (`130.4°`).
- **Pivoted Power-Odds `2383` S-Curve (`pivot = 0.41`, `contrast = 1.20`):** Compresses deep shadows into a smooth logarithmic toe, steepens midtone contrast (`12–55 IRE`) so wet concrete and cast-iron rivets gain tactile bite, and applies a rational **highlight shoulder knee above `74 IRE`** (`white_shoulder = 95.5 IRE`) so `0.00%` of pixels clip above `99.2 IRE`.

### 2.2 Halation Threshold (`Y_lin > 0.56` ≈ `78 IRE`, Pre-LUT Scene-Linear)
Halation **must** execute in scene-linear light *before* the `2383` print shoulder — never as an sRGB post-glow [2, 3]:
- **Threshold:** `Y_lin > 0.56` (`~78 IRE` sRGB). In our benchmark, this isolates **`2.74%`** of pixels in `still_01` (three oil-lantern mantles + spillway floodlights), **`0.17%`** in `still_02` (distant cage filament + status lens), and **`1.86%`** in `still_03` (left lantern core + sight-glass specular), leaving **`97.3–99.8%`** of midtone architecture razor-sharp.
- **Dual-PSF Kernel & Spectral Weights:** `0.58 × Gaussian(σ = 4.5 px) + 0.42 × Gaussian(σ = 16.5 px)` at `1920×1080`, tinted `(1.00 R, 0.32 G, 0.04 B) × 0.24` to match red-emulsion back-scatter before rolling off cleanly through the `2383` shoulder.

### 2.3 Black-Level Lift (`2.6–2.9 IRE` Dense Optical Toe — Never `0.0`, Never Milky `> 5.0`)
Lifting blacks via a flat offset (`+0.06` across the board) produces washed-out "milky Instagram film" shadows and destroys contrast ratios. Our `2383` curve maps scene-linear zero asymptotically to **`2.60 IRE` (`RGB ≈ 7/255`)** with immediate steep slope above `3.5 IRE`:
- Crushed digital void (`< 0.8 IRE`) drops from **`7.87%` / `1.48%` / `7.81%` → `0.00%` across all three plates**.
- `P01` black toe locks tightly at **`2.69`, `2.72`, and `2.64 IRE`** — rich theatrical projection black that holds detail on dark OLED and calibrated Rec.709 displays alike.

### 2.4 Split Toning (Toe-Guarded Slate Shadows vs Tungsten-Sodium Upper Mids)
Naive split-toning tints `0 IRE` black blue, making shadows look like a foggy LCD backlight. In `grade_chain.py`:
- **Shadow Cool Bias (`(-0.010 R, +0.002 G, +0.015 B)`):** Weighted by `(1 - Y)^2.3` **multiplied by a `toe_neutral_guard`** that tapers tint down near `2.6 IRE`, keeping deepest blacks neutral-dense while cooling `8–24 IRE` wet slate/iron shadows toward `210°–217°` CIE Lab hue.
- **Upper-Mid / Practical Warmth (`(+0.022 R, +0.007 G, -0.019 B)`):** Peaks across `50–85 IRE` (`64°–82°` warm sodium/amber hue), reinforcing practical tungsten lamps against cool floodwater.

### 2.5 Contrast Ratios & Optical Prime Falloff
- **Scene-Linear `cos⁴(θ)` Falloff (`0.36 stops` at corners):** Applied in linear space prior to halation and the `2383` LUT so corners darken like a real `35mm` prime lens while still landing gracefully on the `2.6 IRE` print toe (`0.00%` corner crush).
- **Measured Zone Contrast Ratios (in true linear photographic stops):** After grading, **Midtone-to-Shadow separation** sits in the cinematic **`2.56–3.14 stops`** pocket across all three shots, and **Highlight-to-Midtone separation** sits at **`2.45–3.55 stops`**, eliminating harsh `4.03-stop` raw digital harshness (`still_01` before) while expanding luminance histogram `P95–P05` spread (`45.84 → 62.49 IRE` on `still_01`; `46.53 → 56.90 IRE` on `still_03`) and raising Shannon tonal entropy (`6.497 → 6.825 bits` and `6.706 → 6.881 bits`).

### 2.6 Cross-Shot Consistency (`65%` Scene-Linear Anchor Normalization)
Before hitting the LUT, Stage A1 measures each plate's scene-linear median luminance `Y_lin,med` against a reel-wide low-key anchor (`Y_anchor = 0.0155`, `~13.5–15.5 IRE` post-print) and applies a **clamped `65%` exposure correction (`[-0.85, +0.95]` stops)** with soft highlight-knee protection (`+0.87 stops` on underexposed `still_01`, `-0.47 stops` on over-bright `still_02`, `+0.58 stops` on `still_03`).
- **Why `65%` pull instead of `100%` histogram equalization?** `100%` matching flattens intentional narrative lighting contrast (a silhouette shot *should* remain darker than an overhead inspection shot), whereas `65%` anchor pull **cuts inter-shot midtone exposure jump by `63.7%` (`2.295 stops → 0.833 stops`)** and tightens `P02` black-toe standard deviation **6-fold (`0.321 IRE → 0.054 IRE`)** so consecutive cuts belong to the same camera roll.

---

## 3. Quantitative Before / After Metrics Across Three Benchmark Stills

All images (`still_01..03_before.jpg`, `still_01..03_after.jpg`, `still_01..03_ab_card.jpg`) and `metrics.json` are generated deterministically by `python3 research/build_ab_benchmark.py`.

### 3.1 Per-Shot Luminance Spread, Zone Separation & Warm/Cool Colour Check

| Shot & State | Toe `P01` (`IRE`) | Median `Y` (`IRE`) | `P95–P05` Spread (`IRE`) | Entropy (`bits`) | Crushed / Clipped (`%`) | Shadow / Mid / High (`IRE`) | Mid/Shad & High/Mid (`stops`) | Warm/Cool `ΔChroma` (`ΔE*ab`) | Warm / Cool Hue (`deg`) | Max Chroma `P99` (`C*ab`) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Still 01 — BEFORE** *(Vault Lanterns)* | `0.20` | `7.63` | `45.84` | `6.497` | `7.87 / 0.44` | `1.36 / 8.44 / 35.91` | `3.13 / 4.03` | `45.11` | `71.7° / 220.4°` | `39.17` |
| **Still 01 — AFTER** *(5219 → 2383)* | **`2.69`** | **`11.96`** | **`62.49`** | **`6.825`** | **`0.00 / 0.00`** | `4.08 / 12.92 / 46.85` | **`2.56 / 3.55`** | **`43.46`** | `73.1° / 216.8°` | `36.54` |
| **Still 02 — BEFORE** *(Ceiling Horn)* | `0.59` | `19.98` | `56.68` | `7.285` | `1.48 / 0.07` | `5.10 / 20.40 / 48.83` | `3.14 / 2.55` | `27.35` | `82.3° / 206.6°` | `26.26` |
| **Still 02 — AFTER** *(5219 → 2383)* | **`2.72`** | **`16.60`** | **`49.03`** | **`6.947`** | **`0.00 / 0.00`** | `5.04 / 17.07 / 42.68` | **`2.85 / 2.45`** | **`23.73`** | `82.5° / 210.9°` | `23.85` |
| **Still 03 — BEFORE** *(Sight-Glass)* | `0.25` | `9.57` | `46.53` | `6.706` | `7.81 / 0.15` | `1.43 / 11.09 / 39.91` | `3.85 / 3.47` | `57.45` | `63.9° / 192.6°` | `52.89` |
| **Still 03 — AFTER** *(5219 → 2383)* | **`2.64`** | **`12.96`** | **`56.90`** | **`6.881`** | **`0.00 / 0.00`** | `3.93 / 14.92 / 48.72` | **`3.14 / 3.09`** | **`50.73`** | `64.3° / 194.6°` | **`44.53`** |

### 3.2 Reel-Level Cross-Shot Consistency Summary

| Cross-Shot Metric (Across Stills 01, 02, 03) | Raw AI Plates (`BEFORE`) | Graded Reel (`AFTER`) | Improvement |
| :--- | ---: | ---: | :--- |
| **Inter-Shot Midtone Exposure Jump (`max/min Y_lin,med`)** | `2.295 stops` | **`0.833 stops`** | **`-63.7%` jump reduction** |
| **Black-Toe `P02` Values Across Shots (`IRE`)** | `[0.36, 1.04, 0.36]` | **`[2.83, 2.87, 2.74]`** | Locked optical print floor |
| **Black-Toe `P02` Cross-Shot Std Dev (`IRE`)** | `0.321 IRE` | **`0.054 IRE`** | **`5.9×` tighter consistency** |
| **Pixels Crushed (`< 0.8 IRE`) or Clipped (`> 99.2 IRE`)** | `Up to 7.87% / 0.44%` | **`0.00% / 0.00%`** | `100%` toe & shoulder protection |

---

## 4. Division Integration — What to ADOPT vs What to REJECT

| Grading Move | Decision | Rationale & Usage |
| :--- | :--- | :--- |
| **Pre-grade `grade_chain.py` on master plates + `kodak_5219_2383_house.cube` for video streams** | **ADOPT** | Run `python3 research/grade_chain.py raw.jpg graded.png` once per keyframe plate (captures spatial linear halation + anchor exposure + `cos⁴` falloff + `5219` grain), or apply `-vf lut3d=research/ab-grade/stills/kodak_5219_2383_house.cube` directly on live motion clips at `200+ fps`. |
| **Auto-trimming stray `<= 12 px` AI border bars before scaling** | **ADOPT** | Caught an invisible `8 px` top black strip on raw `v07/shot_09.jpg` automatically. |
| **65% Scene-Linear Midtone Anchor Normalization (`[-0.85, +0.95]` stop clamp)** | **ADOPT** | Cuts jarring cut-to-cut AI exposure swings by `63.7%` without flattening intentional dark vs bright scene drama. |
| **High-threshold (`Y_lin > 0.56`) red-biased `(1.00, 0.32, 0.04)` pre-LUT halation** | **ADOPT** | Restricts scatter strictly to real bulbs/speculars (`0.17–2.74%` area) and rolls off naturally through the `2383` shoulder. |
| **Low-threshold sRGB bloom (`threshold < 0.65`) or neutral white glow** | **REJECT** | Washes out midtone concrete micro-contrast and reads as cheap digital dreamy haze rather than remjet scatter. |
| **Flat black-lift offsets (`> 5 IRE` milky gray shadows) or post-LUT black oval vignettes** | **REJECT** | Destroys shadow depth (`Mid/Shad < 1.8 stops`); use asymptotic `2.6–2.9 IRE` print toe + pre-LUT linear `cos⁴(θ)` falloff instead. |

---

## 5. Cited Color Science & Sensitometric Sources

1. **Eastman Kodak Company (March 2026) / The Grain Archive** — *KODAK VISION3 500T Color Negative Film 5219 / 7219 Technical Data (`H-1-5219`)*: characteristic D-logE curves, `-6` to `+5` stop latitude, and diffuse RMS granularity by dye layer (`https://thegrainarchive.com/films/kodak-vision3-500t/`).
2. **PixelTools Post (2026)** — *"How the Film Look Really Works: A Colorist's Guide to Film Emulation"* — negative + `2383` print S-curve mechanics, subtractive saturation density (Helmholtz-Kohlrausch / Beer-Lambert absorption), and pre-print halation order of operations (`https://pixeltoolspost.com/blogs/resolve/film-emulation-explained`).
3. **The Boston Film (2025)** — *"Kodak Vision3 500T vs CineStill 800T: Anti-Halation Remjet Layer & Red-Layer Back-Scatter Physics"* (`https://thebostonfilm.com/films/kodak-vision3-500t/`).
4. **Kelly, C. (2025)** — *Genesis Color Science Documentation: Kodak 5219 Negative to 2383 Print Emulation & Subtractive Gamut Mapping* (`https://cullenkellycolor.com/genesis`).
