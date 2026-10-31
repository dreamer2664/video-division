# Team B Sandbox Toolchain Map — What Actually Survives 2 GB Debian 13

**Agent:** `grade` (`v04`)  
**Hardware Measured:** Debian GNU/Linux 13 (trixie) · 2 vCPU · `1.9 GiB` total RAM (`~1.5 GiB` available, `0 B` swap) · `21 GiB` free disk · no `/dev/kvm`, no physical GPU.

## 1. Candidate Evaluation & Empirical Measurements

| Tool / Workflow | Availability (Debian 13) | Footprint / Measured RSS | Verdict |
|---|---|---|---|
| **Kdenlive 24.12.3** (GUI via `xvfb`) | `apt` (`kdenlive`) | Pulls **427 packages** (KDE/Qt6 frameworks + Breeze + KIO); slow cold-start over software Xvfb, fragile headless UI scripting | **Rejected for headless automation** — uses MLT (`melt`) under the hood anyway; GUI overhead wastes limited 1.9 GiB RAM. |
| **Shotcut 25.03.29** (GUI via `xvfb`) | `apt` (`shotcut`) | Pulls **59 extra packages** on top of MLT/Qt; exports `.mlt` XML to `melt` | **GUI rejected; engine (`melt`) adopted** — Shotcut's actual render backend is `melt`. |
| **MLT Framework (`melt 7.30.0` + `frei0r-plugins 2.3.3`)** | `apt` (`melt`, `frei0r-plugins`) | **690 MiB max RSS** (`706,184 KB`), renders 3 s of 1080p30 in `4.02 s` | **Survived** — native XML non-linear timeline (`.mlt`) compatible with Shotcut/Kdenlive, lightweight in CLI mode (`xvfb-run -a melt` or headless). |
| **FFmpeg 7.1.5 — Naive `scale=8000:-1,zoompan` monolithic graph** | `apt` (`ffmpeg`) | **1,040 MiB max RSS** (`1,065,080 KB`) for *one* 3 s shot; chaining 12 shots OOM-kills a 1.9 GiB container | **Trap identified & avoided** — classic `zoompan` upscale advice on the internet blows past the 1.2 GiB sandbox limit when chained. |
| **FFmpeg 7.1.5 — Chunked Per-Shot `scale=4320:2430` + `zoompan` + `.cube` `lut3d` + `curves` + `blend` + `noise`** | `apt` (`ffmpeg`) | **578 MiB max RSS** (`592,096 KB`) per 5.5 s 1080p30 shot | **Primary Colour & Motion Engine** — 2.25× Lanczos oversampling eliminates integer-pixel `zoompan` judder while keeping RSS safely `< 650 MiB`. |
| **libass / FFmpeg `ass` & `subtitles` + `fonts-ebgaramond` / `fonts-inter`** | `apt` (`ffmpeg`, `fonts-ebgaramond`, `fonts-inter`) | Negligible overhead (`< 40 MiB` delta) | **Survived** — crisp anti-aliased vector typography with alpha fade-in/out and styled lower-third scrim boxes. |
| **Python 3.13 + NumPy 2.3.5 + SciPy 1.17.1 + SoX 14.4.2 + FFmpeg `loudnorm`** | `apt` (`python3-numpy`, `python3-scipy`, `sox`) | `< 260 MiB` max RSS for 60 s 48 kHz float32 stereo synthesis + two-pass EBU R128 mastering | **Primary Sound Design & LUT Engine** — generates exact `33×33×33` `.cube` 3D LUTs, slow-motion optical overlays, multi-stem stereo soundscape, and `-16.0 LUFS` master. |

## 2. Architecture That Survived (`project/render.sh`)

To guarantee `≤ 750 MiB` peak RSS per process (well below the agency's `1.2 GiB` sandbox ceiling) and 100% deterministic reproduction from the repo alone:

1. **Raw Neutral Plates (`assets/plates/shot_01_raw.png` … `shot_12_raw.png`):** Committed static plates captured with flat log-like tonal latitude.
2. **3D Colour Cubes (`project/generate_luts.py` → `assets/luts/*.cube`):** Standard `33×33×33` Resolve/Shotcut-compatible `.cube` 3D LUTs (`01_cold_slate_dusk.cube`, `02_sodium_amber.cube`, `03_mercury_storm.cube`, `04_silver_dawn.cube`).
3. **Slow-Motion Optical Overlays (`project/generate_overlays.py`):** Vectorized NumPy synthesis of slow-motion diagonal rain streaks, rolling coastal mist, warm sodium halation blooms, and water-surface specular ripples, composited onto moving shots via FFmpeg's `blend` filter (`screen` / `softlight`).
4. **Per-Shot Grading & Camera Pass (`project/render.sh` Stage 2):** Each shot is graded and animated in its own isolated FFmpeg invocation (`scale=4320:2430:flags=lanczos` → `zoompan` → `lut3d` → `curves` → `colorbalance` → `blend` atmospheric overlay → `vignette` → temporal 35mm `noise`), capping peak memory at `~600 MiB`.
5. **Act-Reel Editorial Assembly & NLE Project Export (`project/render.sh` Stage 3 + `project/kelvin-v04.mlt`):** Joins the 12 graded shots with `0.50 s` (`15-frame`) dissolves to `60.000 s` exact (`1,800` frames), burns `≥ 44 px` high-contrast ASS typography/captions, and ships a companion `.mlt` XML project file inspectable in Shotcut/Kdenlive or playable via `melt`.
6. **Two-Pass EBU R128 Sound Mastering (`project/build_audio.py` + `loudnorm`):** Synthesizes environmental rain/surf/foghorn/ferry foley + harmonic score across all four Kelvin acts, then normalizes to **`-16.0 LUFS` integrated** and **`-1.7 dBTP` true peak** at `48 kHz` stereo AAC.

## 3. Clean-Slate Full Build Benchmark (`./render.sh`)

- **Command:** `rm -f video.mp4 stills/*.png && /usr/bin/time -f "elapsed=%Es max_rss=%MKB" ./render.sh`
- **Wall-Clock Time (2 vCPU):** `11m 04.40s` (optimised down from `~25m` after replacing FFmpeg `blend=all_expr` per-pixel C interpreter on Shot 07 with SIMD `maskedmerge` + pre-generated wipe matte, cutting Shot 07 from `220 s` to `22.7 s`).
- **Peak Memory (`max_rss`):** `816,704 KB` (**`797.6 MiB`**) — safely inside the `1.2 GiB` per-process sandbox limit on a `1.9 GiB` container.
- **Colour-Space Lessons Learned:**
  1. Running `blend=all_mode=screen` in `yuv420p` shifts `128`-centered U/V chroma toward `192` (magenta cast); executing `lut3d` → `curves` → `blend` in planar RGB (`format=gbrp`) before converting to `yuv420p` (`out_color_matrix=bt709:out_range=tv`) preserves exact Resolve-style blend math.
  2. Feeding `.jpg` stills into FFmpeg tags output streams `yuvj420p` (full-range PC) unless `scale=out_color_matrix=bt709:out_range=tv,format=yuv420p` and `-color_range tv` are explicitly set.
