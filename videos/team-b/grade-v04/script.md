# `KELVIN` — Four Temperatures of Night

- **Assignment:** `v04` (Team B — Visual Workflow: Colour Grading, Slow Motion & Sound Design)
- **Worker:** `grade` (reporting to Manager B / `lux`)
- **Target Duration:** `60.000 s` (`1,800` frames at `30 fps`, within `58.0–62.0 s` spec contract)
- **Format:** `1920×1080` · `30 fps` · `H.264 (libx264, yuv420p, +faststart)` · `48 kHz stereo AAC` · `-16.0 LUFS` integrated (`TP ≤ -1.0 dBTP`)

---

## 1. Creative Premise & Dramatic Structure

**Logline:** Across one rain-swept night in a working coastal harbour, natural daylight surrenders to three eras of artificial light—warm incandescent beacon, monochromatic `2100 K` sodium vapour, and storm-lashed `4200 K` industrial mercury-halide—before `6500 K` dawn washes the world back to its true colour.

Rather than treating colour grading as decorative polish over static slides, **`KELVIN` makes colour temperature the dramatic engine of the piece**. Every raw source plate (`assets/plates/shot_01_raw.png` … `shot_12_raw.png`) is authored with flat, wide-latitude neutral tonality ("log-style digital negative") so that the `.cube` 3D LUTs, split-tone RGB `curves`, live temporal grade transitions (`blend`), sub-pixel camera motion (`zoompan` over 2.25× supersampled plates), and slow-motion atmospheric overlays (falling rain, rolling sea fog, sodium halation, water shimmer) carry the storytelling.

### Narrative Arc (Not a Slideshow, Not a Loop)
1. **ACT I — HOOK (`00.0 s – 12.0 s`) · `5600 K → 3800 K` · *LAST DAYLIGHT***
   - *Visual:* Cold steel-slate twilight on wet basalt pier stones (`00.0 s`), punctured at `04.0 s` by a warm tungsten harbour beacon igniting across dark water.
   - *Sonic:* Tidalwash against stone pilings; at `04.0 s`, a deep resonant harbour foghorn fifth (`D2 + A2`) blooms across coastal canyon reverb.
   - *Hook thesis:* When the sun leaves the coast, the harbour has to invent its own colour.
2. **ACT II-A — DEVELOPMENT (`12.0 s – 28.0 s`) · `2100 K` · *LOW-PRESSURE SODIUM***
   - *Visual:* Streetlamps click on. Neutral stone arches, a lone night-ferry cabin window, and rain-beaded iron railings are steeped in `2100 K` amber-gold midtones and deep Prussian-blue shadows, with slow-motion diagonal rain streaks and warm halation breathing across wet surfaces.
   - *Sonic:* 120 Hz transformer hum, crisp micro-droplet rain transients, felt-piano voicings (`Bb maj7#11 → G min9`), and a distant ferry bell panning left-to-right.
3. **ACT II-B — ESCALATION & CLIMAX (`28.0 s – 46.0 s`) · `4200 K` · *MERCURY ARC & STORM SURGE***
   - *Visual:* Midnight squall hits the outer terminal. Shot 07 executes a **live in-camera colour-grade transformation** (`blend` sweeping a fogbound gantry crane silhouette from flat ungraded silver mist into high-contrast cyan-emerald & crimson-beacon split tone). Shot 08 captures slow-motion ocean spray suspended against a concrete seawall; Shot 09 pushes toward a mint-lit coastal watchtower window against cobalt storm rain.
   - *Sonic:* Bowed metallic harmonic swell, low-passed Atlantic wave roar, sub-bass pulse (`C min11 → A7b9`) building to peak intensity at `44.5 s`—then dropping into sudden stillness at `46.0 s`.
4. **ACT III — RESOLUTION (`46.0 s – 60.0 s`) · `6500 K` · *SILVER DAWN***
   - *Visual:* Relay switch clicks off; artificial sodium dies. Mirror-still tidal flats, a drifting wooden skiff, and the open headland horizon emerge in clean, luminous `6500 K` bleach-silver and pale rose rim light, remaining in living motion through frame `1,800`.
   - *Sonic:* Crystalline morning bell (`D5`) opening into a warm Picardy-third `D major9` resolution over gentle glass-water tide.

---

## 2. Typography & Caption Legibility Contract

All burned-in typography is rendered at `1920×1080` over a soft lower-third luminance scrim (`rgba(8, 12, 18, 0.58)` + `3 px` shadow) guaranteeing `> 11:1` contrast ratio and strict compliance with the `≥ 40 px` legibility requirement:
- **Title Display (`KELVIN`):** `88 px` Inter Bold, tracking `+12 px`, `#F5F3EC`
- **Kelvin Chapter Stamp (top-left):** `44 px` Inter SemiBold, `#E8EDF2` / Kelvin-accent tint (strictly `≥ 40 px`)
- **Burned-in Narrative Captions (bottom center):** `50 px` EB Garamond Regular / SemiBold, `#F7F5EE` with `3 px` dark shadow (`#070A0F`)
- **Sidecar Subtitle File:** `captions.srt` (exact matching timecodes shipped alongside burned-in video)

---

## 3. Master Shot List & Per-Shot Timings (`60.000 s` Exact)

Transition math: 12 graded shots with individual clip lengths summing to `65.50 s`, joined by 11 filmic cross-dissolves (`0.50 s` / `15 frames` each, `-5.50 s` overlap) = **`60.000 s` (`1,800` frames at `30.00 fps`)**. Zero black frames (`> 0.5 s`) and zero frozen frames (`> 0.5 s`).

| Shot | Master Timeline | Clip Dur | Kelvin / LUT | Subject (Raw Neutral Plate) | Slow-Motion & `blend` Layer | Camera (`zoompan` 2.25×) | Sound Cue | On-Screen Text / Caption (`≥ 44 px`) |
|---|---|---|---|---|---|---|---|---|
| **01** | `00.00 – 04.00 s` | `4.50 s` (135f) | `5600 K` `01_cold_slate_dusk.cube` | Wet basalt harbour pier stones reflecting fading steel-blue horizon | Slow-motion water ripple shimmer (`blend=softlight`) + mist | Smooth low-angle forward dolly (`z: 1.02 → 1.12`) | Cold harbour tide wash, subtle wind air | `5600 K · LAST DAYLIGHT` *(44px)* / `"At dusk, the harbour loses the sun first."` *(50px, 00.4–03.7s)* |
| **02** | `04.00 – 08.00 s` | `4.50 s` (135f) | `3800 K` `01_cold_slate_dusk.cube` + warm beacon `curves` | Concrete breakwater lighthouse lantern igniting amber against slate sea | Breathing warm tungsten halation flare (`blend=screen`) | Slow lateral drift right + push (`z: 1.03 → 1.11`) | Deep `D2+A2` foghorn harmonic + canyon reverb | **`KELVIN`** *(88px title, 04.3–07.6s)* / `"Artificial light steps in to hold the coast."` *(50px)* |
| **03** | `08.00 – 12.00 s` | `4.50 s` (135f) | `3200 K` twilight split-tone | Long coastal causeway road curving along dark tidal water, distant lamps waking | Drifting sea fog ribbon across horizon (`blend=screen`) | Slow crane pull-back (`z: 1.13 → 1.03`) | Suspended `Dm(add9)` cello pad enters | `"Every lamp rewrites the colour of the dark."` *(50px, 08.3–11.6s)* |
| **04** | `12.00 – 17.50 s` | `6.00 s` (180f) | `2100 K` `02_sodium_amber.cube` | Rain-slicked brick viaduct arches beneath glowing streetlamps | Slow-motion diagonal rain streaks (`blend=screen`) + puddle shimmer | Steady forward glide under arch (`z: 1.02 → 1.14`) | Lamp relay click, 120 Hz hum, soft night rain | `2100 K · SODIUM VAPOUR` *(44px)* / `"Low-pressure sodium turns stone and rain to amber."` *(50px, 12.4–17.0s)* |
| **05** | `17.50 – 23.00 s` | `6.00 s` (180f) | `2100 K` `02_sodium_amber.cube` + cyan shadow `colorbalance` | Solitary warm-lit passenger ferry cabin window seen across wet dark deck | Slow-motion rain droplets & warm glass bloom (`blend=softlight`) | Slow pan left-to-right across glass (`z: 1.06 → 1.12`) | Felt piano (`Bbmaj7#11`), distant ferry bell L→R | `"Inside one lit window, warmth becomes an island."` *(50px, 18.0–22.5s)* |
| **06** | `23.00 – 28.00 s` | `5.50 s` (165f) | `2100 K` deep amber/Prussian split `curves` | Macro iron harbour railing covered in hanging raindrops reflecting twin lights | Shimmering optical bokeh drift (`blend=screen`) | Slow macro pull-back + upward drift (`z: 1.15 → 1.04`) | Close rain droplets on iron, `Gm9` bass swell | `"Shadows sink into Prussian blue between the pools of gold."` *(50px, 23.4–27.5s)* |
| **07** | `28.00 – 34.00 s` | `6.50 s` (195f) | `4200 K` **Dynamic Live Grade Sweep** (`log → 03_mercury_storm.cube`) | Towering harbour gantry cranes in heavy sea fog over shipping channel | Live `blend` sweep from ungraded grey fog into deep cyan-emerald & red beacon grade + fast fog | Slow upward tilt & push (`z: 1.02 → 1.13`) | Bowed metallic harmonic + rising storm wind | `4200 K · MERCURY ARC` *(44px)* / `"Midnight shifts the spectrum—cold cyan steel and warning red."` *(50px, 28.5–33.5s)* |
| **08** | `34.00 – 40.00 s` | `6.50 s` (195f) | `4200 K` `03_mercury_storm.cube` + high-contrast S-curve | Heavy ocean wave exploding into suspended spray against concrete harbour wall | Slow-motion drifting mist & airborne spray particles (`blend=screen`) | Dramatic slow push into crest (`z: 1.03 → 1.16`) | Deep Atlantic wave impact + low-passed sub roar | `"In slow motion, the storm surge hangs like carved glass."` *(50px, 34.5–39.5s)* |
| **09** | `40.00 – 46.00 s` | `6.50 s` (195f) | `4200 K` fluorescent mint / cobalt night `curves` | Solitary harbour watchtower glass room glowing pale green-white in driving rain | Heavy rain sheets + pulsing storm lightning rim (`blend=addition`) | Slow push toward watchtower glass (`z: 1.02 → 1.15`) | Peak `A7b9` harmonic tension cresting at `44.5s`, sudden drop | `"Four thousand Kelvin holds the watch until the squall breaks."` *(50px, 40.5–45.4s)* |
| **10** | `46.00 – 51.00 s` | `5.50 s` (165f) | `6500 K` `04_silver_dawn.cube` | Unlit streetlamp post silhouetted above mirror-still tidal flats at first light | Gentle horizontal water shimmer (`blend=softlight`) | Calm horizon glide left (`z: 1.08 → 1.03`) | Relay click-off; pure `D5` bell into calm air | `6500 K · SILVER DAWN` *(44px)* / `"Before sunrise, the sensors click off one by one."` *(50px, 46.4–50.5s)* |
| **11** | `51.00 – 55.50 s` | `5.00 s` (150f) | `6500 K` `04_silver_dawn.cube` + rose-silver highlight lift | Wooden skiff moored on glass-calm harbour water catching pale rose mist | Slow rising morning vapour (`blend=screen`) | Gentle pull-back revealing water (`z: 1.12 → 1.03`) | Warm `Dmaj9` chord blooms in stereo field | `"Silver water remembers every colour without keeping one."` *(50px, 51.4–55.0s)* |
| **12** | `55.50 – 60.00 s` | `4.50 s` (135f) | `6500 K` clean daylight curve + luminous silver roll-off | Wide coastal headland overlooking parting sea fog and open silver-blue ocean | Living mist drift + sunlit water glint right to `60.00 s` | Slow expansive forward float (`z: 1.02 → 1.10`) | Lingering `Dmaj9` harmonic shimmer + gentle tide to `60.0s` | `"6500 K — Day returns the world to itself."` *(50px, 55.8–59.6s)* |

---

## 4. Caption Transcript (`captions.srt` Alignment)

1. `00:00:00,400 --> 00:00:03,700` — At dusk, the harbour loses the sun first.
2. `00:00:04,300 --> 00:00:07,600` — KELVIN — Artificial light steps in to hold the coast.
3. `00:00:08,300 --> 00:00:11,600` — Every lamp rewrites the colour of the dark.
4. `00:00:12,400 --> 00:00:17,000` — 2100 K · Low-pressure sodium turns stone and rain to amber.
5. `00:00:18,000 --> 00:00:22,500` — Inside one lit window, warmth becomes an island.
6. `00:00:23,400 --> 00:00:27,500` — Shadows sink into Prussian blue between the pools of gold.
7. `00:00:28,500 --> 00:00:33,500` — 4200 K · Midnight shifts the spectrum—cold cyan steel and warning red.
8. `00:00:34,500 --> 00:00:39,500` — In slow motion, the storm surge hangs like carved glass.
9. `00:00:40,500 --> 00:00:45,400` — Four thousand Kelvin holds the watch until the squall breaks.
10. `00:00:46,400 --> 00:00:50,500` — 6500 K · Before sunrise, the sensors click off one by one.
11. `00:00:51,400 --> 00:00:55,000` — Silver water remembers every colour without keeping one.
12. `00:00:55,800 --> 00:00:59,600` — 6500 K — Day returns the world to itself.
