# `MARK FIVE` (`grade-v06` — Wave 3, Two-Voice Dialogue Escalation in the *KELVIN / MARK* Line)

- **Creator:** `grade` (Team B — Colour, Cinematography & Visual Finish)
- **Format:** `1920×1080` (`16:9` landscape), `30 fps` CFR, `60.000 s` (`1,800` frames), H.264 `yuv420p` (`+faststart`) + `48 kHz` stereo AAC (`-16.0 LUFS ± 0.5`, `TP ≤ -1.0 dBTP`)
- **Two-Voice Dialogue Spine (`133` words, `10` strictly alternating turns, `0.000 s` overlap):**
  - **Voice A — NARRATOR (`KEEPER`, Lower Spillway Tower):** `edge-tts` **`en-US-ChristopherNeural`**, `--rate=-11%`, `--pitch=-5Hz` (`F0 ≈ 101 Hz`, full-bandwidth `80 Hz – 8 kHz` close-mic baritone, panned **Left-Center `-28%`**: `L=0.88, R=0.55`).
  - **Voice B — RESPONDER (`COPPER LINE`, Field Set Caller):** `edge-tts` **`en-GB-SoniaNeural`**, `--rate=+4%`, `--pitch=+2Hz` (`F0 ≈ 198 Hz`, clipped British RP night-dispatch register passed through a `340 Hz – 3,400 Hz` Bakelite copper-handset filter with carbon-mic presence and mechanical cradle/relay clicks, panned **Right-Center `+28%`**: `L=0.55, R=0.88`).

---

## 1. Story & Dialogue Escalation

Seven minutes after the upper Blackwater lock breached in *MARK FOUR* (`2:24 AM`), the flood surge reaches the **Lower Basin Spillway Tower** three miles downstream. Inside the rain-lashed stone tower, a dead copper emergency wall telephone—disconnected since `1989`—suddenly rings.

1. **The Dead Line Rings (`0.000 s – 15.733 s`, Shots 01–02, Turns `01 [A]` → `02 [B]`):** The keeper answers the Bakelite wall handset; a calm female British voice claiming to be Basin Control orders him to confirm the water is still below **Mark Five**.
2. **The Prohibition & The Roof (`15.733 s – 35.533 s`, Shots 03–06, Turns `03 [A]` → `04 [B]` → `05 [A]` → `06 [B]`):** Outside, churning floodwater surges four inches below the red `V`. She warns him: *"Whatever you hear on the roof, do not draw the spillway pins."* Standing beneath the rain-lashed ceiling oculus (**Shot 05 — Signature Wall-Frame Image**), he asks how she knows something is walking on the roof. She tells him to follow the copper phone wire beneath his window sill.
3. **The Severed Cord & Pre-Twist Silence (`35.533 s – 42.100 s`, Shot 07, Turn `07 [A]` + `1.280 s` dead-air pause):** His lantern beam hits the wet flagstones—the copper wire is cut clean through.
4. **The Turn & Ceiling Reveal (`42.100 s – 60.000 s`, Shots 08–10, Turns `08 [B]` → `09 [A]` → `10 [B]`):** She isn't calling from Basin Control—she is standing on his roof in the storm, alligator-clipped directly onto the tower's lead-in stub. And **Mark Five** wasn't painted to measure the river: he raises his lamp to find `MARK V` stenciled across the stone ceiling above him—*"It marks how high your tower fills."*

---

## 2. Colour Architecture (Four Bespoke `33³` 3D `.cube` LUTs)

| Regime | 3D LUT File | Colour & Contrast Signature | Applied Shots |
| :--- | :--- | :--- | :--- |
| **I. Spillway Obsidian** | `luts/spillway_obsidian.cube` | Crushed basalt blacks (`#040811`), cold `5600 K` floodlit silver rain streaks, saturated crimson `V` isolation | Shots `01`, `03` |
| **II. Copper & Tungsten** | `luts/copper_bakelite.cube` | Deep Prussian night glass (`#060E1C`) split against rich `2200 K` amber lamp & warm copper highlights (`#F4B63F`) | Shots `02`, `05` *(Wall-Frame)*, `07` |
| **III. Mercury Pin-Rack** | `luts/cyan_skylight.cube` | Cold `4400 K` industrial mercury-cyan steel & wet wired skylight glass with crimson lead-seal separation | Shots `04`, `06` |
| **IV. Storm Submersion** | `luts/ceiling_flood_6800k.cube` | Stark `6800 K` ice-blue storm moonlight (`#7EB4EA`) + surgical high-contrast crimson `MARK V` ceiling stencil | Shots `08`, `09`, `10` |

---

## 3. Two-Voice Interleaved Timeline & Master Shot List (`1,800` Frames @ `30 fps`)

All timestamps locked from real `edge-tts` `WordBoundary` synthesis prior to plate generation or rendering (`0.000 s` voice overlap):

| Turn | Speaker & Engine | Pan & Acoustic Space | Active Speech (`s`) | Gap After (`s`) | Shot(s) | Spoken Line (`133` words total) |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **01** | **Narrator (`A`)** `en-US-ChristopherNeural` (`-11%`, `-5Hz`) | `28% L` · Close-mic full-range | `0.400 – 9.929` | `0.820` | `01` (`0.00–7.00s`), `02` (`7.00–15.73s`) | *"At two twenty-four, seven minutes after the upper lock breached, the copper wall phone rings. A line dead since nineteen eighty-nine."* |
| **02** | **Responder (`B`)** `en-GB-SoniaNeural` (`+4%`, `+2Hz`) | `28% R` · `340–3400 Hz` copper handset | `10.749 – 15.388` | `0.680` | `02` (`7.00–15.73s`) | *"Lower Tower, come in. Confirm your water is still below Mark Five."* |
| **03** | **Narrator (`A`)** `en-US-ChristopherNeural` (`-11%`, `-5Hz`) | `28% L` · Close-mic full-range | `16.068 – 21.524` | `0.680` | `03` (`15.73–21.87s`) | *"I check the spillway wall outside. Four inches below the red five."* |
| **04** | **Responder (`B`)** `en-GB-SoniaNeural` (`+4%`, `+2Hz`) | `28% R` · `340–3400 Hz` copper handset | `22.204 – 26.539` | `0.620` | `04` (`21.87–26.87s`) | *"Good. Whatever you hear on the roof, do not draw the spillway pins."* |
| **05** | **Narrator (`A`)** `en-US-ChristopherNeural` (`-11%`, `-5Hz`) | `28% L` · Close-mic full-range | `27.159 – 31.126` | `0.680` | `05` (`26.87–31.47s`) **[WALL-FRAME]** | *"Wait. How do you know something is walking on the roof?"* |
| **06** | **Responder (`B`)** `en-GB-SoniaNeural` (`+4%`, `+2Hz`) | `28% R` · `340–3400 Hz` copper handset | `31.806 – 35.196` | `0.680` | `06` (`31.47–35.53s`) | *"Follow the copper telephone wire down beneath your window sill."* |
| **07** | **Narrator (`A`)** `en-US-ChristopherNeural` (`-11%`, `-5Hz`) | `28% L` · Close-mic full-range | `35.876 – 41.163` | **`1.280`** *(Pre-twist pause)* | `07` (`35.53–42.10s`) | *"My lamp hits the wet stone floor. The wire is cut clean through."* |
| **08** | **Responder (`B`)** `en-GB-SoniaNeural` (`+4%`, `+2Hz`) | `28% R` · `340–3400 Hz` copper handset | `42.443 – 50.170` | `0.780` | `08` (`42.10–47.33s`), `09` (`47.33–50.57s`) | *"I'm not calling from Basin Control. I'm on your roof, clipped to the stub. And Mark Five wasn't painted to measure the river."* |
| **09** | **Narrator (`A`)** `en-US-ChristopherNeural` (`-11%`, `-5Hz`) | `28% L` · Close-mic full-range | `50.950 – 55.886` | `0.880` | `10` (`50.57–60.00s`) | *"I raise the lamp. Mark Five is stenciled across the ceiling."* |
| **10** | **Responder (`B`)** `en-GB-SoniaNeural` (`+4%`, `+2Hz`) | `28% R` · `340–3400 Hz` copper handset | `56.766 – 58.833` | `1.167` *(Tail)* | `10` (`50.57–60.00s`) | *"It marks how high your tower fills."* |

---

## 4. Visual Shot Breakdown (`10` First-Party `1920×1080` Plates)

1. **Shot 01 (`0.000–7.000 s`, `210 f`, `spillway_obsidian.cube`):** Wide architectural night frame at `2:24 AM` of the brutalist dark granite Lower Basin Spillway Tower rising out of churning black floodwater in torrential silver-blue rain under `5600 K` floodlights, one warm `2200 K` amber watch-room window glowing near the parapet.
2. **Shot 02 (`7.000–15.733 s`, `262 f`, `copper_bakelite.cube`):** Close-up inside the rain-beaded stone tower of a weathered black Bakelite twin-bell wall telephone wired with braided copper cord; a rain-wet dark leather glove lifts the receiver off the brass hook as a warm amber line-active lamp glows against Prussian night glass.
3. **Shot 03 (`15.733–21.867 s`, `184 f`, `spillway_obsidian.cube`):** High-angle exterior close-up looking down the wet black granite spillway wall in heavy rain: boiling black river water surges four inches beneath a heavy crimson-painted iron Roman numeral **`V`** bolted into the wet stone.
4. **Shot 04 (`21.867–26.867 s`, `150 f`, `cyan_skylight.cube`):** Tight industrial close-up of massive red-painted iron spillway release levers locked inside a wet steel pin-rack with a brass padlock and stamped lead wire seal under cold `4400 K` mercury-cyan light.
5. **Shot 05 (`26.867–31.467 s`, `138 f`, `copper_bakelite.cube` — SIGNATURE WALL-FRAME IMAGE):** Symmetrical `16:9` widescreen 35mm cinema composition inside the cavernous vaulted granite cistern gallery of the Spillway Tower: silver rain falls straight through an iron-grated circular ceiling oculus onto mirror-black water below, while a solitary keeper in a wet dark oilskin coat stands dead-center on a narrow stone bridge holding a blazing `2200 K` golden storm lantern aloft toward the roof, casting a vertical column of amber reflection into the Prussian-cyan abyss.
6. **Shot 06 (`31.467–35.533 s`, `122 f`, `cyan_skylight.cube`):** Steep upward angle at the rain-lashed wired-glass skylight overhead in cold `6800 K` storm light—two dark heavy boot silhouettes stand motionless atop the streaming wet glass panes.
7. **Shot 07 (`35.533–42.100 s`, `197 f`, `copper_bakelite.cube`):** High-contrast macro where a warm `2200 K` lantern beam illuminates the wet stone wall beneath the window sill down to shallow black floodwater pooling over flagstones—revealing the braided copper phone cable severed clean through, raw copper strands glinting above dark ripples.
8. **Shot 08 (`42.100–47.333 s`, `157 f`, `ceiling_flood_6800k.cube`):** Exterior rooftop close-up in torrential `6800 K` ice-blue storm rain: a weatherproof olive-and-brass field-telephone box sits on the wet stone parapet beside two bright copper alligator clips biting directly onto the tower's severed external lead-in wire stub.
9. **Shot 09 (`47.333–50.567 s`, `97 f`, `ceiling_flood_6800k.cube`):** Haunting wide `6800 K` storm frame of the isolated stone Spillway Tower half-swallowed by rising black reservoir water in driving rain, a lone dark rain-hooded figure standing on the roof edge beside the skylight.
10. **Shot 10 (`50.567–60.000 s`, `283 f`, `ceiling_flood_6800k.cube`):** Low-angle interior reveal tilting up the wet granite tower wall to the vaulted stone ceiling beside the dripping iron roof hatch: warm `2200 K` lantern light hits a stark weathered crimson **`MARK V`** stenciled across the high ceiling stone—then dims out on `56.75 s` into cold `6800 K` blue storm light as the responder delivers the final line.
