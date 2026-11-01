# `MARK SEVEN` — Production Script, Valley Scale Schedule & Two-Station Relay (`videos/team-b/grade-v08`)

- **Runtime:** `60.000 s` (`1,800` frames @ `30.000 fps` CFR, `1920×1080` progressive)
- **Escalation Axis (`v05` → `v06` → `v07` → `v08`):** **A Place Larger Than a Room** (stepping outside the subterranean dam rooms of `v05–v07` into a **three-mile basalt river gorge, the exterior 400-foot concrete arch dam, a canyon steel truss railway bridge, and the flooded street grid of the evacuated river town of Lowgate** two miles downstream).
- **Time & Premise:** **`03:14 AM`** — thirty-seven minutes after **Vault Six** blew its internal window bolts in *MARK SIX* (`02:37 AM`). Four thousand residents of Lowgate were evacuated to high ground before midnight. Across two miles of rain-swept canyon air, **CREST** (on the wet concrete parapet atop the 400-foot dam) and **LEVEE** (on the stone riverwalk above flooded Main Street in Lowgate) track the crest down the valley—and discover where the builders placed **`MARK SEVEN`**, and what drowning one room inside the dam bought an entire town.

---

## 1. Two-Station Valley Relay Design (`0.000 s` Overlap — Honest Axis, No Fourth Voice)

| Station ID | Physical Location Across the Valley | Engine Voice & Prosody | Acoustic / Spectral Treatment | Stereo Azimuth | Caption Coding |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **`A` (`CREST`)** | Concrete parapet walkway atop the `400 ft` hydroelectric arch dam (`Elev. 480 ft`) | `en-US-ChristopherNeural` (`--rate=-11% --pitch=-5Hz`, deep House US baritone, `F0 ≈ 108 Hz`) | Full-range storm-hooded close-mic (`75–8,000 Hz`, `+1.8 dB @ 125 Hz`) + mechanical relay key clicks | **Left (`-36%`, `+5.42 dB` L-bias)** | Left-aligned (`-88 px`), `#F5D14E` House Amber bar (`CREST ·`) |
| **`B` (`LEVEE`)** | Stone levee steps overlooking flooded Main Street in evacuated **Lowgate** (`2.0 mi` downriver) | `en-GB-SoniaNeural` (`--rate=+4% --pitch=+4Hz`, British hydrological survey engineer, `F0 ≈ 205 Hz`) | Waterproof VHF field transceiver (`350–3,300 Hz` 4th-order bandpass + mild RF drive + VHF squelch tail) | **Right (`+36%`, `+5.42 dB` R-bias)** | Right-aligned (`+88 px`), cold cyan signal bar (`LEVEE ·`) |

---

## 2. Locked Ten-Turn Ridge-to-Town Script (`0.420 s – 58.880 s`, Zero Gaps `> 1.14 s`)

| Turn | Spk | Start (`s`) | End (`s`) | Gap (`s`) | Spoken Line |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **01** | **`A` (`CREST`)** | `0.420` | `6.865` | `0.725` | *"Three fourteen, thirty-seven minutes after Vault Six flooded inside the dam, and the gorge is full."* |
| **02** | **`B` (`LEVEE`)** | `7.590` | `13.722` | `0.725` | *"Lowgate levee, two miles downstream, every house is empty, and black water is across the rail yard."* |
| **03** | **`A` (`CREST`)** | `14.447` | `20.512` | `0.725` | *"All four spillway gates are wide open, and the canyon crest is passing the railway bridge now."* |
| **04** | **`B` (`LEVEE`)** | `21.237` | `26.431` | `0.725` | *"White water is hitting the steel girders on the bridge, and backing slow water down Main Street."* |
| **05** | **`A` (`CREST`)** | `27.156` | `32.267` | `0.725` | *"Marks One through Five are on the dam, Six was the vault, where is Mark Seven?"* |
| **06** | **`B` (`LEVEE`)** | `32.992` | `37.850` | `0.725` | *"Not on the dam, they stenciled Mark Seven on the iron streetlamp in the town square."* |
| **07** | **`A` (`CREST`)** | `38.575` | `40.947` | `0.725` | *"Tell me where the water is on that post."* |
| **08** | **`B` (`LEVEE`)** | `41.672` | `46.350` | **`1.137`** | *"The amber lamp is still burning, and the river just stopped two inches below Mark Seven."* |
| **09** | **`A` (`CREST`)** | `47.487` | `52.780` | `0.725` | *"Drowning one concrete room inside the dam took two inches off a three-mile river."* |
| **10** | **`B` (`LEVEE`)** | `53.505` | `58.880` | `1.120` *(tail)* | *"Four thousand people left their keys on the counter, and their town is still standing at Mark Seven."* |

---

## 3. Ten-Shot Exterior Valley & Flooded Town Schedule (`1,800` Frames @ `30 fps`)

| Shot | Window (`s`) | Frames | 3D LUT (`.cube`) | Camera / Weather Motion | Landscape / Architectural Night Composition |
| :---: | :---: | :---: | :--- | :--- | :--- |
| **01** | `0.000–7.200` | `216` | `valley_obsidian_500t.cube` | Slow cliffside push-in + heavy rain/mist | High basalt cliff overlook at `03:14 AM` looking down upon the monumental `400 ft` concrete arch dam and three-mile canyon in torrential `6500K` storm rain; one warm `2600K` sodium parapet lamp glows on the wet foreground walkway. |
| **02** | `7.200–14.067` | `206` | `gorge_cyan_6500k.cube` | Lateral drift right across flooded tracks | Lowgate rail yard two miles downstream: steel tracks disappearing beneath black mirror sheet-water in driving rain, dark brick freight depot silhouettes, and a single `2600K` amber switchman lantern reflecting across flooded ties. |
| **03** | `14.067–20.867` | `204` | `spillway_storm_7000k.cube` | Telephoto push-in + heavy spillway spray |Monumental exterior face of the concrete hydroelectric dam at night: four open spillway chutes thundering white flood plumes into cold `7000K` canyon mist while one warm `2600K` amber turbine-deck beacon burns on the powerhouse wall. |
| **04** | `20.867–26.800` | `178` | `spillway_storm_7000k.cube` | Lateral drift left + wind-whipped rain | Riveted black-steel railway truss bridge spanning the basalt gorge: boiling floodwater surges inches beneath the iron lower chord while a solitary `2600K` brass bridge clearance lantern glows through storm spray. |
| **05** | `26.800–32.633` | `175` | `valley_obsidian_500t.cube` | Slow upward tilt up wet basalt cliff | Vertical wet columnar basalt canyon wall below the dam tailrace: boiling silver-cyan river water drowning a weathered `MARK V` gauge below bare black rock lit by one `2600K` caged inspection lamp. |
| **06** | `32.633–38.200` | `167` | `lowgate_sodium_2600k.cube` | Push-in from stone levee over flooded street | Elevated night view from Lowgate's sandbagged stone levee steps into empty 1930s brick storefronts: shallow black backwater mirrors the dark street toward a lone `2600K` town-square streetlamp in the distance. |
| **07** | `38.200–41.300` | `93` | `gorge_cyan_6500k.cube` | Tight waterline push-in + rain ripples | Low water-level telephoto close-up on the wet cast-iron streetlamp post in the flooded square: gentle rain rings ripple across black slackwater lapping **two inches below** white stenciled letters **`MARK SEVEN`** lit by warm `2600K` amber glow from above. |
| **08** | `41.300–47.100` | `174` | `valley_obsidian_500t.cube` | Slow symmetrical pull-back *(Wall-Frame @ `1398`)* | **Signature Wall-Frame (`stills/wall_frame_mark_seven_clean.png`):** Dead-symmetrical wide architectural night photograph straight down flooded Main Street of evacuated Lowgate—mirror-black slackwater curb-to-curb between dark wet brick facades, the distant arch dam veiled in cold `6500K` canyon mist at the end of the avenue, and dead-center the solitary burning `2600K` cast-iron streetlamp with **`MARK SEVEN`** stenciled dry above the black waterline. |
| **09** | `47.100–53.133` | `181` | `spillway_storm_7000k.cube` | High canyon rim lateral drift + drifting mist | Vast high-altitude ridge panorama of the entire three-mile basalt river gorge S-curve at `03:14 AM`: cold `6500K` storm clouds parting over the mist-shrouded dam upstream and the single warm `2600K` pinpoint of Lowgate's town square lamp two miles downstream. |
| **10** | `53.133–60.000` | `206` | `lowgate_sodium_2600k.cube` | Slow final pull-back along stone riverfront | Quiet final wide tableau along Lowgate's wet stone riverfront promenade: empty dark mill buildings intact behind iron railings, rain easing over receding black mirror water, and one `2600K` brass levee lamp casting a long unbroken amber reflection to camera. |
