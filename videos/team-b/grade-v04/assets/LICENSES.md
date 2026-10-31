# Asset Provenance & Licences — `grade-v04` (`KELVIN`)

Every visual, colour-grading, typographic, and audio asset in `videos/team-b/grade-v04/` is either **generated originally for this piece** or **verified CC0 1.0 Public Domain Dedication**, with zero watermarks and zero third-party copyright restrictions.

## 1. Visual Source Plates (`assets/plates/`)

| File | Origin | Creator / Attribution | Licence | Source URL |
|---|---|---|---|---|
| `shot_01_raw.jpg` … `shot_09_raw.jpg` | Original AI-generated flat 16:9 cinema plates created in sandbox by `grade` | `grade` (Agency Video Division) | **CC0 1.0 / Agency Internal Sample** | Generated directly in workspace (`assets/plates/`) |
| `shot_10_raw.jpg` | *Jetty in fog at Holländaröd 1* (cropped 16:9 `1920×1080`) | W.carter | **CC0 1.0 Universal** (`http://creativecommons.org/publicdomain/zero/1.0/deed.en`) | `https://commons.wikimedia.org/wiki/File:Jetty_in_fog_at_Holl%C3%A4ndar%C3%B6d_1.jpg` |
| `shot_11_raw.jpg` | *Alone On The Ocean* (cropped 16:9 `1920×1080`) | Jack Rains | **CC0 1.0 Universal** (`http://creativecommons.org/publicdomain/zero/1.0/deed.en`) | `https://commons.wikimedia.org/wiki/File:Alone_On_The_Ocean_(Unsplash).jpg` |
| `shot_12_raw.jpg` | *Mussel Rock Park Coastal Bluffs* (cropped 16:9 `1920×1080`) | Lee Ball (`User:Catleeball`) | **CC0 1.0 Universal** (`http://creativecommons.org/publicdomain/zero/1.0/deed.en`) | `https://commons.wikimedia.org/wiki/File:Mussel_Rock_Park_Coastal_Bluffs.jpg` |

## 2. 3D Colour Grading LUTs (`assets/luts/`)
- `01_cold_slate_dusk.cube`, `02_sodium_amber.cube`, `03_mercury_storm.cube`, `04_silver_dawn.cube`: Mathematically authored `33×33×33` Adobe/Resolve `.cube` 3D LUTs generated deterministically by `project/generate_luts.py` — **Original work (`grade`), CC0 1.0**.

## 3. Slow-Motion Optical Overlays (`project/generate_overlays.py`)
- Procedural slow-motion diagonal rain sheets, drifting sea mist, warm tungsten/sodium halation bloom, and water-surface specular shimmer — **Original work (`grade`), CC0 1.0**.

## 4. Sound Design & Score (`project/build_audio.py` → `assets/audio_master_48k.wav`)
- 100% original procedural electro-acoustic score & coastal sound design synthesized from scratch via Python (`numpy` / `scipy`) + `sox` + FFmpeg EBU R128 `loudnorm` (harbour tide foley, night rain droplets, 120 Hz sodium lamp hum, `D2+A2` foghorn fifth, ferry bell pan, Atlantic storm swell, bowed metallic harmonics, felt-piano/cello score resolving `Dm(add9) → Bbmaj7#11 → Gm9 → Cm11 → A7b9 → Dmaj9`) — **Original work (`grade`), CC0 1.0**.

## 5. Fonts Used in Burned-in Captions
- **Inter** (`fonts-inter` Debian package) — SIL Open Font License 1.1 (OFL-1.1).
- **EB Garamond** (`fonts-ebgaramond` Debian package) — SIL Open Font License 1.1 (OFL-1.1).
