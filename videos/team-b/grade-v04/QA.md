# QA Report — `grade-v04` (`KELVIN`)

- **Worker:** `grade` (Team B — Visual Workflow)
- **Manager:** Manager B (`lux`)
- **Branch:** `grade/v04`
- **Deliverable:** `videos/team-b/grade-v04/video.mp4`

---

## 1. Spec Compliance Summary (All Checkable)

| Requirement (`specs/60s-video.md`) | Target | Measured (`video.mp4`) | Status |
|---|---|---|---|
| Duration | `58.0–62.0 s` | **`60.000000 s`** (`1,800` frames exact) | PASS |
| Resolution & Frame Rate | `1920×1080` @ `30 fps` | **`1920×1080`**, `r_frame_rate=30/1`, `avg_frame_rate=30/1` | PASS |
| Video Codec / Pixel Format / Faststart | H.264 (`libx264`), `yuv420p`, `faststart` | **`h264` (High L4.1), `yuv420p` (`tv` / `bt709`), `moov` atom at byte `36`** | PASS |
| Audio Codec / Sample Rate / Channels | `48 kHz` stereo `AAC` | **`aac` (LC), `48000 Hz`, `2` ch (`stereo`)** | PASS |
| Integrated Loudness | `-16 LUFS` target | **`-16.0 LUFS`** (`-16.04 LUFS` JSON exact) | PASS |
| True Peak | `≤ -1 dBTP`, no clipping | **`-1.7 dBTP`** (`-1.69 dBTP` JSON exact) | PASS |
| File Size | `< 90 MB` | **`44.81 MB`** (`46,991,029` bytes) | PASS |
| On-Screen Text Legibility | `≥ 40 px` at `1080p`, high contrast | Title `108 px` (~78 px cap), stamps `58 px` (~42 px cap), captions `62 px` (~44 px cap) over dark scrim (`>12:1` contrast) | PASS |
| Captions | Burned in or `.srt` shipped | **Both**: burned in via `libass` (`assets/captions.ass`) + sidecar `captions.srt` | PASS |
| Black / Frozen Frames | None `> 0.5 s` | **`0` black segments `≥ 0.4 s`**, **`0` frozen segments `≥ 0.4 s`** | PASS |
| Clean-Slate Reproducibility | Reproducible from repo alone | `rm -f video.mp4 stills/*.png && ./render.sh` succeeded in **`11m 04.4s`**, **`797.6 MiB`** (`816,704 KB`) max RSS | PASS |

---

## 2. Verbatim Verification Command Outputs

### 2.1 `ffprobe` Spec Command (Verbatim)
Command:
```bash
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4
```
Output:
```text
codec_name=h264
codec_type=video
width=1920
height=1080
r_frame_rate=30/1
codec_name=aac
codec_type=audio
r_frame_rate=0/0
duration=60.000000
size=46991029
```

### 2.2 Extended Stream, Colour-Space & `+faststart` Probe (Verbatim)
Command:
```bash
ffprobe -v error -show_entries stream=index,codec_name,codec_type,profile,pix_fmt,color_range,color_space,width,height,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,channel_layout,duration:format=duration,size,bit_rate -of default=noprint_wrappers=1 video.mp4
```
Output:
```text
index=0
codec_name=h264
profile=High
codec_type=video
width=1920
height=1080
pix_fmt=yuv420p
color_range=tv
color_space=bt709
r_frame_rate=30/1
avg_frame_rate=30/1
duration=60.000000
nb_frames=1800
index=1
codec_name=aac
profile=LC
codec_type=audio
sample_rate=48000
channels=2
channel_layout=stereo
r_frame_rate=0/0
avg_frame_rate=0/0
duration=60.000000
nb_frames=2814
duration=60.000000
size=46991029
bit_rate=6265470
```
Faststart `moov` check: `moov_in_first_64KB: True`, `offset_bytes: 36`.

### 2.3 EBU R128 Loudness Verification (Verbatim)
Note on FFmpeg 7.1.5 loglevel: running `ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12` produces **zero bytes of stderr** (confirming zero container/decoder errors), because `af_loudnorm` emits its summary at `AV_LOG_INFO`. Running with `-v info -nostats` prints the verbatim `Parsed_loudnorm_0` table:

Command:
```bash
ffmpeg -hide_banner -nostats -v info -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -14
```
Output:
```text
Input Integrated:    -16.0 LUFS
Input True Peak:      -1.7 dBTP
Input LRA:             3.7 LU
Input Threshold:     -26.3 LUFS

Output Integrated:   -23.8 LUFS
Output True Peak:    -10.0 dBTP
Output LRA:            3.6 LU
Output Threshold:    -34.0 LUFS

Normalization Type:   Dynamic
Target Offset:        -0.2 LU
[out#0/null @ 0x55ce73819100] video:773KiB audio:45008KiB subtitle:0KiB other streams:0KiB global headers:0KiB muxing overhead: unknown
frame= 1800 fps=202 q=-0.0 Lsize=N/A time=00:01:00.00 bitrate=N/A speed=6.74x
```

### 2.4 Black-Frame, Frozen-Frame & Silence Stress Test
Command:
```bash
ffmpeg -hide_banner -i video.mp4 -vf "blackdetect=d=0.4:pix_th=0.08,freezedetect=n=0.002:d=0.4" -af "silencedetect=n=-50dB:d=0.4" -f null -
```
Result: **Zero** black segments `≥ 0.4 s`, **zero** frozen segments `≥ 0.4 s`, and **zero** silent drops `≥ 0.4 s`. First-second (`0.15 s`) and last-second (`59.50 s`, `59.93 s`) frames were extracted and visually verified.

---

## 3. Stills Shipped (`stills/`)

- `stills/01.png` (`00:05.50`, `1920×1080`) — Act I (`3800 K`): Breakwater lighthouse tungsten flare + **`KELVIN`** display title + caption.
- `stills/02.png` (`00:15.00`, `1920×1080`) — Act II-A (`2100 K · SODIUM VAPOUR`): Wet brick harbour viaduct steeped in amber/Prussian-blue `.cube` split-grade + diagonal slow-motion rain streaks.
- `stills/03.png` (`00:36.50`, `1920×1080`) — Act II-B (`4200 K`): Slow-motion storm wave exploding against seawall in mercury-cyan grade + rain sheets.
- `stills/04.png` (`00:57.50`, `1920×1080`) — Act III (`6500 K · FIRST DAYLIGHT`): Coastal headland dawn resolution.

---

## 4. Provenance & Licences (Full Detail in `assets/LICENSES.md`)

- **Shots 01–09 (`assets/plates/shot_01_raw.jpg` … `shot_09_raw.jpg`):** Original 16:9 neutral cinema plates generated in the workspace by `grade`. (Note: Arena's per-turn `generate_image` tool cap of 10 calls was reached after Shot 09 due to one safety-filter retry on Shot 06; Shots 10–12 were therefore sourced from verified `CC0 1.0` coastal morning photography on Wikimedia Commons.)
- **Shot 10 (`shot_10_raw.jpg`):** *Jetty in fog at Holländaröd 1* by W.carter — **CC0 1.0 Universal** (`https://commons.wikimedia.org/wiki/File:Jetty_in_fog_at_Holl%C3%A4ndar%C3%B6d_1.jpg`).
- **Shot 11 (`shot_11_raw.jpg`):** *Alone On The Ocean* by Jack Rains — **CC0 1.0 Universal** (`https://commons.wikimedia.org/wiki/File:Alone_On_The_Ocean_(Unsplash).jpg`).
- **Shot 12 (`shot_12_raw.jpg`):** *Mussel Rock Park Coastal Bluffs* by Lee Ball — **CC0 1.0 Universal** (`https://commons.wikimedia.org/wiki/File:Mussel_Rock_Park_Coastal_Bluffs.jpg`).
- **3D Colour LUTs (`assets/luts/*.cube`), Optical Overlays (`project/generate_overlays.py`), Sound Design & Score (`project/build_audio.py`):** 100% original code & procedural synthesis by `grade` (**CC0 1.0**).
- **Fonts:** `Inter` and `EB Garamond` (`fonts-inter`, `fonts-ebgaramond` on Debian 13, **SIL OFL-1.1**).

---

## 5. Sandbox Toolchain Survival Summary (Full Detail in `project/TOOLCHAIN.md`)

- **Hardware measured:** Debian 13 (trixie), 2 vCPU, `1.9 GiB` RAM (`0 B` swap), no GPU.
- **What failed / was rejected:** Desktop GUI NLEs (`kdenlive` pulls 427 packages; GUI scripting over `Xvfb` wastes scarce RAM), naive `scale=8000:-1,zoompan` (`1,040 MiB` RSS for a single clip — OOMs if chained), and FFmpeg `blend=all_expr` per-pixel C-expression evaluation (`220 s` for a single 6.5 s clip; replaced with SIMD `maskedmerge` + pre-rendered wipe matte in `22.7 s`).Also caught and fixed two real bugs during self-test: JPEG input plates initially caused `pix_fmt=yuvj420p` (fixed via explicit `scale=out_color_matrix=bt709:out_range=tv,format=yuv420p`), and `blend=screen` in YUV space corrupts `128`-centered chroma into magenta (avoided by executing `lut3d` → `curves` → `blend` strictly in planar RGB `gbrp`).
- **What survived:** Isolated per-shot `4320×2430` Lanczos supersampled `zoompan` + `.cube` `lut3d` + `curves` + `gbrp` `blend` (`797.6 MiB` max RSS across the entire `./render.sh` build), `libass` typography, MLT (`melt 7.30.0`) XML timeline export (`project/kelvin-v04.mlt`), and NumPy/SciPy + FFmpeg two-pass EBU R128 mastering.

---

## 6. Blunt Self-Review

### What Works Well
- **Genuine colour-driven narrative:** The four-act progression (`5600 K` dusk → `2100 K` sodium amber → `4200 K` mercury storm → `6500 K` silver dawn) gives the video a real beginning, escalation, climax (`40–45.5 s`), drop into stillness (`46.0 s`), and harmonic resolution (`Dmaj9`), avoiding the "random pretty stills with a music loop" trap.
- **Colourist craft:** Grading in `gbrp` with real `33×33×33` `.cube` 3D LUTs + per-shot `curves` + Shot 07's live diagonal colourist wipe makes the grading visibly structural rather than a uniform filter.
- **Sound-picture lock:** Every major cut has a purposeful acoustic event (`04.0 s` foghorn fifth on the lighthouse beam, `12.0 s` relay click + `120 Hz` ballast hum + rain on the sodium viaduct, `17.5 s` left-to-right ferry bell, `28.0 s` bowed steel glissando on the crane grade sweep, `34.0 s` wave boom, `46.0 s` sensor click-off + morning chime), hitting `-16.0 LUFS` / `-1.7 dBTP` cleanly.

### What Is Weak (Honest Critique)
1. **2D affine camera vs true 3D parallax:** Even with `2.25×` Lanczos supersampling and composited slow-motion rain/mist/water-shimmer overlays, `zoompan` remains a 2D planar transform; foreground bollards (Shot 06) and gantry cranes (Shot 07) do not shift perspective against background harbour lights the way a real dolly or depth-map 2.5D projection would.
2. **Synthetic instrument timbre:** While the coastal foley, foghorn, and ambient pads sit naturally in stereo reverb, the procedural felt-piano notes (`build_audio.py` additive partials + low-passed hammer transient) still sound cleaner and more synthetic than a multi-velocity sampled acoustic felt piano.
3. **Controlled dynamic range (`LRA = 3.7 LU`):** Because continuous harbour surf and pad harmonies underscore all four acts, Loudness Range is relatively compact (`3.7 LU`). Letting Act I (`0–4 s`) and Act III (`46–49 s`) drop `-6 dB` sparser would widen theatrical contrast between storm and dawn.
4. **Shot 12 directional sunlight:** Shot 12's CC0 coastal bluff plate was photographed in clearer morning sun than Shot 10–11's overcast sea fog; `04_silver_dawn.cube` unifies the silver-blue palette, but the harder hillside shadow betrays a slightly later morning hour.
