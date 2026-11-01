# `MARK SIX` — Production Script & Three-Voice Acoustic Schedule (`videos/team-b/grade-v07`)

- **Runtime:** `60.000 s` (`1,800` frames @ `30.000 fps` CFR, `1920×1080` progressive)
- **Series Finale:** Wave 4 (`MARK FOUR` → `MARK FIVE` → **`MARK SIX`**)
- **Premise:** *A room full of people who are not in the room.* At **2:37 AM**, thirteen minutes after the lower spillway tower flooded in *MARK FIVE*, **Vault Six**—a subterranean granite acoustic relay chamber built into the core of the dam—sits completely empty. Three steel chairs stand unoccupied around a wet slate table where three `2600K` storm lamps still burn. Not one human body is inside. Yet **three distinct voices** converse across the empty room from three physical transducers—until the barge spotter shines a `7000K` searchlight through the rain-lashed observation window and reads what is stenciled across the *interior* wall behind the empty chairs.

---

## 1. Three-Voice Acoustic & Spatial Design (`0.000 s` Overlap)

| Speaker ID | Diegetic Transducer in Empty Room | Engine Voice & Prosody | Acoustic / Spectral Treatment | Stereo Azimuth |Caption Style |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **`A` (`REEL`)** | `1/4"` brushed-steel reel-to-reel tape deck turning on Left console | `en-US-ChristopherNeural` (`--rate=-10% --pitch=-6Hz`, deep US baritone, `F0 ≈ 105 Hz`) | Warm full-range magnetic oxide close-mic (`75–8,000 Hz`, `+1.8 dB @ 128 Hz`, centroid `~1,960 Hz`) + mechanical solenoid start/stop clicks | **Left (`-38%`, `+5.74 dB` L-bias)** | Left-aligned (`-84 px`), warm `2600K` amber edge bar (`REEL ·`) |
| **`C` (`HORN`)** | Cast-brass marine VHF radio horn bolted dead-center to vaulted ceiling | `en-IE-ConnorNeural` (`--rate=+2% --pitch=+6Hz`, clear Irish mid-tenor, `F0 ≈ 158 Hz`) | Crisp piezoelectric brass VHF horn (`850–6,800 Hz` 4th-order bandpass, `+3.5 dB @ 3,350 Hz`, centroid `~2,780 Hz`) + VHF carrier squelch pips | **Dead Center (`0%`, `0.00 dB` L=R)** | Center-aligned (`0 px`), seafoam-emerald signal bar (`HORN ·`) |
| **`B` (`LINE`)** | Off-hook black Bakelite telephone handset swinging by its cord on Right wall | `en-GB-SoniaNeural` (`--rate=+5% --pitch=+4Hz`, clipped British RP operator, `F0 ≈ 210 Hz`) | Narrow copper-pair carbon telephone (`340–3,100 Hz` 4th-order bandpass + `tanh` carbon drive, centroid `~1,060 Hz`) + line cradle clicks | **Right (`+38%`, `+5.74 dB` R-bias)** | Right-aligned (`+84 px`), cold `6800K` cyan signal bar (`LINE ·`) |

---

## 2. Locked Twelve-Turn Three-Voice Script (`0.400 s – 58.776 s`)

| Turn | Spk | Start (`s`) | End (`s`) | Gap (`s`) | Spoken Line |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **01** | **`A` (`REEL`)** | `0.400` | `6.581` | `0.620` | *"Two thirty-seven, Vault Six is empty, and this tape reel starts when water reaches the glass."* |
| **02** | **`B` (`LINE`)** | `7.201` | `11.915` | `0.580` | *"Vault Six, why is a tape answering, and why is your wall phone swinging off the hook?"* |
| **03** | **`C` (`HORN`)** | `12.495` | `18.083` | `0.580` | *"Barge Six on the ceiling horn, I hear you through the empty room, three chairs and nobody inside."* |
| **04** | **`B` (`LINE`)** | `18.663` | `23.735` | `0.580` | *"Barge, sweep your searchlight up the dam wall and confirm water is still below Mark Six."* |
| **05** | **`C` (`HORN`)** | `24.315` | `29.180` | `0.600` | *"Five red marks on the concrete are underwater, and there is no Mark Six painted outside."* |
| **06** | **`A` (`REEL`)** | `29.780` | `34.169` | `0.580` | *"If you hear this tape over the room mic, stop looking for a sixth gate."* |
| **07** | **`B` (`LINE`)** | `34.749` | `37.940` | `0.580` | *"Then why leave three storm lamps burning in an empty room?"* |
| **08** | **`C` (`HORN`)** | `38.520` | `43.569` | **`1.200`** | *"Wait, through the glass, Mark Six is stenciled inside, behind the three empty chairs."* |
| **09** | **`A` (`REEL`)** | `44.769` | `49.852` | `0.580` | *"Vault Six isn't a control room, it's the surge chamber we flood to save the town."* |
| **10** | **`C` (`HORN`)** | `50.432` | `52.062` | `0.540` | *"The window bolts just fired."* |
| **11** | **`B` (`LINE`)** | `52.602` | `55.554` | `0.680` | *"Cut the line, the river is coming through the glass."* |
| **12** | **`A` (`REEL`)** | `56.234` | `58.776` | `1.224` *(tail)* | *"Nobody stays in the room at Mark Six."* |

---

## 3. Ten-Shot Visual & `.cube` 3D LUT Schedule (`1,800` Frames @ `30 fps`)

| Shot | Window (`s`) | Frames | 3D LUT (`.cube`) | Camera / Optical Motion | Visual Composition |
| :---: | :---: | :---: | :--- | :--- | :--- |
| **01** | `0.000–6.900` | `207` | `vault_slate_4300k.cube` | Slow axial push-in + rain on window | Wide subterranean granite Vault Six: three empty steel chairs at a wet slate console, three warm `2600K` storm lamps, cold `6500K` rain streaming down tall armored glass, `1/4"` reel deck turning on left desk. |
| **02** | `6.900–12.200` | `159` | `copper_cord_cyan.cube` | Subtle lateral drift left | Right granite bulkhead: an off-hook black Bakelite telephone handset dangling and swaying gently by its twisted cloth cord beside empty wet coat hooks in cold cyan window light. |
| **03** | `12.200–18.400` | `186` | `copper_cord_cyan.cube` | Low-angle slow upward tilt | Symmetrical vaulted stone ceiling: cast-brass marine VHF radio horn bolted dead-center overhead with a tiny emerald carrier pilot light and cyan rain caustics rippling across wet concrete. |
| **04** | `18.400–24.000` | `168` | `surge_breach_7000k.cube` | Exterior storm push-in + heavy rain | From the black churning river: a `7000K` xenon barge searchlight slices diagonally through torrential nocturnal rain up the monumental concrete dam face toward Vault Six's glowing window slit. |
| **05** | `24.000–29.500` | `165` | `surge_breach_7000k.cube` | Lateral drift right + heavy storm | Tight telephoto on the wet concrete dam wall: black floodwater boils over a half-submerged crimson `MARK V` gauge stencil; above it under the searchlight beam, bare wet concrete with no sixth mark. |
| **06** | `29.500–34.467` | `149` | `amber_oxide_reel.cube` | Macro push-in + reel rotation | Macro on the left slate desk: brushed-aluminum `10.5"` magnetic tape reels turning beside a glowing `2600K` amber VU meter and an upright chrome omnidirectional room microphone. |
| **07** | `34.467–38.233` | `113` | `vault_slate_4300k.cube` | Slow architectural pull-back *(Wall-Frame)* | **Signature Wall-Frame (`stills/wall_frame_mark_six_clean.png`):** Dead-symmetrical architectural study of three brass storm lanterns glowing in `2600K` pools before three empty steel chairs, framed by wet brutalist granite piers and `6500K` rain-streaked glass. |
| **08** | `38.233–44.300` | `182` | `surge_breach_7000k.cube` | Push-in through rain-lashed glass | Looking IN from outside the rain-drenched armored window under the `7000K` searchlight: past the three silhouetted empty chairs, stark white industrial letters **`MARK SIX`** are stenciled across the interior back granite wall. |
| **09** | `44.300–52.333` | `241` | `amber_oxide_reel.cube` | Drift left + shear-bolt flash at `50.45s` | Low-angle close-up on the riveted steel hydraulic shear bolts clamping the bowed armored glass as hairline fractures spider across the thick pane against black river pressure and warm amber reflections. |
| **10** | `52.333–60.000` | `230` | `vault_slate_4300k.cube` | Slow final pull-back + rising floor surge | Wide final tableau of empty Vault Six as dark silver-cyan floodwater surges across the stone floor around the legs of the three empty chairs while a single amber storm lamp reflects in the rising water. |
