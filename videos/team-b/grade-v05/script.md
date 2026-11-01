# `MARK FOUR` (`grade-v05` — Wave 2, *KELVIN* Nocturne Register)

- **Creator:** `grade` (Team B — Colour, Cinematography & Visual Finish)
- **Format:** `1920×1080` (16:9 widescreen), `30 fps` CFR, `60.000 s` (`1,800` frames), H.264 `yuv420p` (`+faststart`) + `48 kHz` stereo AAC (`-16.0 LUFS` target, `TP ≤ -1.0 dBTP`)
- **Spoken Spine:** `137` words synthesized first via `edge-tts` (`en-US-ChristopherNeural`, `--rate=-12%`, `--pitch=-4Hz`) with exact `100 ns` `WordBoundary` telemetry (`0.360 s` first syllable → `59.144 s` final syllable; `53.92 s` active speech + measured documentary breath pauses including a deliberate `1.120 s` pre-twist silence at `43.473 s–44.593 s`). All shot cuts and 2–5 word caption beats are locked directly to the measured synthesiser output before plate generation or rendering.

---

## 1. Premise & Structural Arc

A completely original nocturnal slow-burn thriller set in the rain-soaked, cold-light *KELVIN* register—moving away from `v04`'s harbour light calibration into a tense hydraulic mystery at an isolated stone river lock at `2:17 AM`.

1. **Immediate Hook & Rule (`0.000 s – 9.600 s`, Shots 01–02):** At `2:17 AM` in driving rain, the stone flood-lock on the Blackwater has one iron rule: never open the sluice if the river reaches **Mark Four**.
2. **Counted Escalation & Anomaly (`9.600 s – 33.167 s`, Shots 03–06):** A forty-year night routine logs the rising water every fifteen minutes (`1:45 — Mark Two`, `2:00 — Mark Three`). Four inches of cold rain fall in twenty minutes—yet the river eerily freezes three millimeters below the crimson Mark Four line, flat as dark glass.
3. **Poster Frame & Investigation (`33.167 s – 44.200 s`, Shots 07–08):** Carrying a blazing amber storm lantern out onto the monumental floodlit dam catwalk (**Shot 07 — Signature Poster Image**), you shine the light down the wet stone lock wall and discover empty, raw bolt holes beneath the water surface—followed by a deliberate **`1.120 s` breath pause** (`43.473 s – 44.593 s`).
4. **The Turn & Haunting Landing (`44.200 s – 60.000 s`, Shots 09–11):** Someone unbolted the brass `MARK IV` plate and bolted it two feet higher. Behind you, the amber desk lamp in the keeper's booth clicks off. The river never stopped rising—the sluice gate behind you is already open.

---

## 2. Colour Architecture (Four High-Contrast `33³` 3D `.cube` LUTs)

Built with **stronger toe crush, steeper midtone S-curve contrast, and tighter highlight halation** than `v04`:

| Regime | 3D LUT File | Colour Register | Applied Shots |
| :--- | :--- | :--- | :--- |
| **I. Abyssal Slate** | `luts/blackwater_slate.cube` | Crushed obsidian shadows (`#050912`), steel-silver `5600 K` floodlight rain streaks, isolated crimson numeral `IV` | Shots `01`, `02`, `03` |
| **II. Chiaroscuro Amber** | `luts/amber_ledger.cube` | Deep Prussian storm night (`#060D1A`) split-toned against rich `2200 K` oilskin/lantern tungsten (`#F5B942`) with warm bloom | Shots `04`, `07` *(Poster)*, `08` |
| **III. Mercury Dread** | `luts/mercury_stillness.cube` | Cold `4300 K` cyan-emerald industrial vapour, ink-black mirror water, surgical separation on the `#E53935` red datum line | Shots `05`, `06` |
| **IV. Storm Breach** | `luts/sluice_breach.cube` | Stark `6800 K` ice-blue storm moonlight (`#7FB2E5`), wet stone wrench scars, extinguished booth glass, crimson alarm accent | Shots `09`, `10`, `11` |

---

## 3. Master Shot List & Real Synthesiser Timings (`1,800` Frames @ `30 fps`)

Every shot duration was locked **after** measuring `en-US-ChristopherNeural` (`--rate=-12% --pitch=-4Hz`) word boundaries:

| Shot | Frames | Timeline (`s`) | Dur (`s`) | Speech Span (`s`) | LUT | Visual Composition & Camera Motion | Spoken Narration (`137` words total) |
| :---: | :---: | :---: | :---: | :---: | :--- | :--- | :--- |
| **01** | `0–179` | `0.000–5.967` | `5.967` | `0.360–5.772` | `blackwater_slate` | Wide architectural frame of the ancient Blackwater stone river lock at `2:17 AM` in heavy driving rain under cold `5600 K` floodlights; churning dark water below. Slow push-in (`1.00→1.07×`). | *"At two seventeen in the morning, the old stone lock on the Blackwater has only one rule."* |
| **02** | `179–288` | `5.967–9.600` | `3.633` | `6.152–9.405` | `blackwater_slate` | Tight low-angle close-up of wet carved Roman numerals `II`, `III`, and a crimson-painted brass `IV` plate bolted into glistening black granite above rain-lashed black water. Subtle vertical drift. | *"Never open the sluice if the rain reaches Mark Four."* |
| **03** | `288–444` | `9.600–14.800` | `5.200` | `9.825–14.612` | `blackwater_slate` | Elevated wide shot of the solitary stone lock-keeper's bridge booth spanning black rushing water in torrential silver rain; one warm `2200 K` amber window glowing inside Prussian darkness. Slow lateral glide. | *"For forty years, a night keeper has logged the water every fifteen minutes."* |
| **04** | `444–612` | `14.800–20.400` | `5.600` | `14.992–20.183` | `amber_ledger` | Interior macro through rain-beaded glass: open brass-cornered leather logbook under a warm `2200 K` desk lamp (`01:45 — MARK II`, `02:00 — MARK III` in wet black fountain ink), brass pocket watch beside it. Slow push-in. | *"One forty-five: Mark Two. Two o'clock: Mark Three."* |
| **05** | `612–828` | `20.400–27.600` | `7.200` | `20.603–27.399` | `mercury_stillness` | Close-up of a rain-drenched cast-iron sluice gearwheel and brass hydro-gauge needle frozen dead still under cold `4300 K` cyan-emerald mercury vapour light while heavy silver rain sheets pour past. Slow creep-in. | *"Outside, four inches of cold rain fall in twenty minutes. Yet the gauge stops moving."* |
| **06** | `828–995` | `27.600–33.167` | `5.567` | `27.799–32.933` | `mercury_stillness` | Waterline macro inside the stone chamber: black mirror-flat water hovering `3 mm` beneath a razor-sharp painted red datum stripe under cold cyan light, eerie concentric rain ripples barely disturbing the surface. | *"Three millimeters below the red line. Still as dark glass."* |
| **07** | `995–1136` | `33.167–37.867` | `4.700` | `33.373–37.663` | `amber_ledger` | **[SIGNATURE POSTER IMAGE]** Dead-center symmetrical 35mm anamorphic wide shot: a solitary keeper in a wet yellow oilskin coat stands at the center of the narrow rain-swept stone dam catwalk holding a blazing `2200 K` amber storm lantern between towering cyan-lit steel floodgates and abyssal storm sky. | *"So you carry the lantern out onto the catwalk to check for a jammed float."* |
| **08** | `1136–1326` | `37.867–44.200` | `6.333` | `38.083–43.473` *(+ `0.727 s` hold in silence)* | `amber_ledger` | High-angle beam of warm amber lantern light slicing down the wet vertical stone lock wall; just beneath the glossy dark waterline, four raw, empty threaded bolt holes and a pale rectangular stone scar gleam back. | *"Your light hits the wet stone wall. And you see the empty bolt holes."* *(followed by deliberate `1.120 s` pre-twist pause)* |
| **09** | `1326–1485` | `44.200–49.500` | `5.300` | `44.593–49.266` | `sluice_breach` | **[THE TURN]** Stark `6800 K` close-up of the relocated brass `IV` plate bolted freshly into wet drilled stone two feet higher—bright silver wrench scratches and crimson paint gleaming while black water surges far above the original submerged scar below. | *"Someone unbolted Mark Four, and moved the brass plate two feet higher."* |
| **10** | `1485–1600` | `49.500–53.333` | `3.833` | `49.726–53.135` | `sluice_breach` | Reverse wide shot looking back through driving rain along the wet stone catwalk toward the keeper's booth: the warm amber window suddenly extinguishes into cold `6800 K` blue storm darkness (`52.24 s` on *"clicks off"*), dark wet boot-prints leading away from the sluice wheel. | *"Behind you, the lamp in the keeper's booth clicks off."* |
| **11** | `1600–1800` | `53.333–60.000` | `6.667` | `53.555–59.144` | `sluice_breach` | Final haunting shot: massive dark iron sluice gate yawning open in cold `6800 K` storm light as black floodwater roars silently over the stone threshold, fading smoothly to black in the final `0.60 s`. | *"The river never stopped rising. The sluice gate behind you is already open."* |

---

## 4. Caption Architecture (`STYLE-BREAKDOWN.md` §4 — 39 Verbatim `2–5` Word Beats)

- **Typography:** `Inter Bold` (`62 px` at `1080p`), centered at `y = 930 px` over a subtle feathered obsidian backing pill (`rgba(5, 8, 15, 0.72)`) + `4 px` dark outline so muted playback carries 100% of the story without obscuring widescreen composition.
- **Colour Coding:** Cold ivory (`#F2F5FA`) structural words + **sodium/lantern amber (`#F5C84B`)** key focal words, shifting to **warning crimson (`#E8453C`)** strictly on the rule/breach beats (`MARK FOUR.`, `red line.`, `bolt holes.`, `Mark Four,`, `two feet higher.`, `clicks off.`, `is already open.`).
- **Exact Word-Boundary Cue Sheet (`0.000 s` drift vs `WordBoundary` telemetry):**

| Cue | Shot | Start (`s`) | End (`s`) | Words | Caption Text |
| :---: | :---: | :---: | :---: | :---: | :--- |
| 01 | 01 | `0.360` | `1.539` | 2 | `At 2:17` |
| 02 | 01 | `1.553` | `2.135` | 3 | `in the morning,` |
| 03 | 01 | `2.434` | `3.598` | 4 | `the old stone lock` |
| 04 | 01 | `3.613` | `4.479` | 3 | `on the Blackwater` |
| 05 | 01 | `4.493` | `5.772` | 4 | `has only one rule.` |
| 06 | 02 | `6.152` | `7.501` | 4 | `Never open the sluice` |
| 07 | 02 | `7.515` | `8.567` | 4 | `if the rain reaches` |
| 08 | 02 | `8.581` | `9.405` | 2 | `MARK FOUR.` |
| 09 | 03 | `9.825` | `10.933` | 3 | `For forty years,` |
| 10 | 03 | `11.174` | `11.998` | 3 | `a night keeper` |
| 11 | 03 | `12.012` | `13.191` | 4 | `has logged the water` |
| 12 | 03 | `13.205` | `14.612` | 3 | `every fifteen minutes.` |
| 13 | 04 | `14.992` | `17.208` | 3 | `1:45 — Mark Two.` |
| 14 | 04 | `18.209` | `20.183` | 3 | `2:00 — Mark Three.` |
| 15 | 05 | `20.603` | `22.194` | 3 | `Outside, four inches` |
| 16 | 05 | `22.208` | `23.529` | 4 | `of cold rain fall` |
| 17 | 05 | `23.543` | `24.637` | 3 | `in twenty minutes.` |
| 18 | 05 | `25.624` | `26.391` | 3 | `Yet the gauge` |
| 19 | 05 | `26.405` | `27.399` | 2 | `stops moving.` |
| 20 | 06 | `27.799` | `29.290` | 3 | `Three millimeters below` |
| 21 | 06 | `29.305` | `30.228` | 3 | `the red line.` |
| 22 | 06 | `31.215` | `32.933` | 4 | `Still as dark glass.` |
| 23 | 07 | `33.373` | `34.751` | 5 | `So you carry the lantern` |
| 24 | 07 | `34.765` | `35.958` | 4 | `out onto the catwalk` |
| 25 | 07 | `35.972` | `36.640` | 3 | `to check for` |
| 26 | 07 | `36.654` | `37.663` | 3 | `a jammed float.` |
| 27 | 08 | `38.083` | `38.949` | 3 | `Your light hits` |
| 28 | 08 | `38.964` | `40.285` | 4 | `the wet stone wall.` |
| 29 | 08 | `41.271` | `41.925` | 3 | `And you see` |
| 30 | 08 | `41.939` | `43.473` | 4 | `the empty bolt holes.` |
| 31 | 09 | `44.593` | `46.468` | 4 | `Someone unbolted Mark Four,` |
| 32 | 09 | `46.752` | `48.101` | 5 | `and moved the brass plate` |
| 33 | 09 | `48.116` | `49.266` | 3 | `two feet higher.` |
| 34 | 10 | `49.726` | `51.175` | 4 | `Behind you, the lamp` |
| 35 | 10 | `51.189` | `52.226` | 4 | `in the keeper's booth` |
| 36 | 10 | `52.240` | `53.135` | 2 | `clicks off.` |
| 37 | 11 | `53.555` | `55.515` | 5 | `The river never stopped rising.` |
| 38 | 11 | `56.502` | `58.008` | 5 | `The sluice gate behind you` |
| 39 | 11 | `58.022` | `59.144` | 3 | `is already open.` |

---

## 5. Sound & Mix Architecture (`48 kHz` Stereo, `-16.0 LUFS`)

- **Foreground Spine (`0 dBFS` reference bus → `-16.0 LUFS` master):** `en-US-ChristopherNeural` (`--rate=-12% --pitch=-4Hz`) sculpted with gentle `85 Hz` high-pass (removing rumble without thinning baritone chest), `+2.0 dB` presence shelf at `2.8 kHz` for phone-speaker intelligibility, and gentle `3:1` broadcast levelling.
- **Original Procedural Score & Nocturnal Rain Bed (ducked `9.5–11.5 dB` below active speech via envelope sidechain):**
  - Layered stereo rain texture (fine slate patter + storm gust wash, muted inside the glass booth on Shot 04, swelling outside on Shots 05–11).
  - Dark bowed C-minor sub-cello pedal (`C1/G1/Eb2` evolving harmonic drone) that drops to near-total stillness on Shot 06 (*"Still as dark glass"*) and holds a tense heartbeat pulse across the `1.120 s` pre-twist pause (`43.473 s–44.593 s`).
  - Diegetic nocturnal foley: distant quarter-hour clock chime at `14.95 s`, brass gauge tick arrest at `26.40 s`, crisp mechanical switch click at `52.50 s` (*"clicks off"*), and deep surging sluice-water rumble from `53.5 s–59.6 s`.
