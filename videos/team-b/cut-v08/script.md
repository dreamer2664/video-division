# The Monitor Knows — cut v08

**Format:** vertical 9:16 animated rule-horror short; 60 seconds, 30 fps. Entire picture is procedural flat-vector art. No footage, reference frames, or reference audio are used.

**Premise / stake:** At 2:13 a parent listens to a nursery monitor. Its voice accurately narrates the sleeping child's movements, then describes the parent in the reflection on the dark monitor glass. The voice's count includes a sound that never occurs. The parent must decide whether to trust the device protecting the child or unplug the thing that is watching them.

## Narration script

At two thirteen a.m. The parent checks the monitor. The baby sleeps. Count what you hear. One: the radiator ticks. The parent hears it. Two: the crib groans. Heard that too. Two sounds happened. The monitor reports three. Three: the latch turns. The door stays shut. The baby's left hand opens. One finger curls. She turns to the lens. Now it names the parent. Their thumb covers the glass. The parent stands outside. Lens faces her. **[1.25-second pause]** But the voice isn't inside. It stands by the reflection. On this side of glass. Not the child's side. Parent reaches for the plug. The monitor goes quiet.

## Timed shot list / captions

Hard cuts every 2.4 seconds. Each shot is a slow eased 1.00→1.06 push-in with one animated detail (light, waveform, breath, cursor, or reflection). Caption phrases are the complete story beats; a proportional karaoke tint advances through each phrase over its measured speech cue. It is not exact word sync: the build has no word-level forced aligner or per-word timestamps. Narration is segmented to the cue grid so caption windows can be checked against each synthesized segment. A 1.25-second bed-only pause precedes the 76% turn. The segment timeline is committed as `project/voice_cues.csv`.

| Shot | Time | Picture / one moving detail | Caption (2–5 words) | Narration segment |
|---:|:---:|---|---|---|
| 01 | 00:00–00:02.4 | Nursery feed; tiny clock numerals change once | `2:13 A.M. NURSERY` | At two thirteen a.m. |
| 02 | 00:02.4–00:04.8 | Monitor on dresser; green audio meter breathes | `PARENT CHECKS MONITOR` | The parent checks the monitor. |
| 03 | 00:04.8–00:07.2 | Baby under amber pool; blanket lifts subtly | `BABY SLEEPS` | The baby sleeps. |
| 04 | 00:07.2–00:09.6 | Monitor overlay; one rule line appears | `YOU COUNT WHAT YOU HEAR` | Count what you hear. |
| 05 | 00:09.6–00:12 | Radiator grille; one amber tick pulses | `ONE: RADIATOR TICKS` | One: the radiator ticks. |
| 06 | 00:12–00:14.4 | Audio waveform peaks once | `PARENT HEARS IT` | The parent hears it. |
| 07 | 00:14.4–00:16.8 | Crib rail; one slight wooden tremor | `TWO: CRIB GROANS` | Two: the crib groans. |
| 08 | 00:16.8–00:19.2 | Two short waveform peaks settle | `HEARD THAT, TOO` | Heard that too. |
| 09 | 00:19.2–00:21.6 | Counter holds at two; third notch appears | `TWO SOUNDS HAPPENED` | Two sounds happened. |
| 10 | 00:21.6–00:24 | Monitor waveform adds a third notch | `MONITOR REPORTS THREE` | The monitor reports three. |
| 11 | 00:24–00:26.4 | Door latch moves; door panel stays still | `THREE: LATCH TURNS` | Three: the latch turns. |
| 12 | 00:26.4–00:28.8 | Closed door; one light wedge at latch | `DOOR STAYS SHUT` | The door stays shut. |
| 13 | 00:28.8–00:31.2 | Baby's left hand; fingers unfold | `BABY'S HAND OPENS` | The baby's left hand opens. |
| 14 | 00:31.2–00:33.6 | One finger curls against blanket | `ONE FINGER CURLS` | One finger curls. |
| 15 | 00:33.6–00:36 | Baby's face turns toward camera | `SHE TURNS TO LENS` | She turns to the lens. |
| 16 | 00:36–00:38.4 | Dark monitor glass; reflection begins to form | `NOW IT NAMES THE PARENT` | Now it names the parent. |
| 17 | 00:38.4–00:40.8 | Reflected thumb drifts over lens highlight | `THEIR THUMB COVERS GLASS` | Their thumb covers the glass. |
| 18 | 00:40.8–00:43.2 | Split view: sleeping child / parent outside | `PARENT STANDS OUTSIDE` | The parent stands outside. |
| 19 | 00:43.2–00:45.6 | Lens remains on child; waveform recedes, then pauses | `LENS FACES THE CHILD` | Lens faces her. **[pause after this line]** |
| 20 | 00:45.6–00:48.0 | Reflection occupies screen; red pulse begins; caption bridges cut by 2 frames | `VOICE ISN'T INSIDE` (through 00:48.0667) | But the voice isn't inside (ends 00:48.050125). |
| 21 | 00:48.0–00:50.4 | Parent silhouette resolves beside the glass | `BESIDE THE REFLECTION` (from 00:48.0667) | It stands by the reflection. |
| 22 | 00:50.4–00:52.8 | Lens boundary glows; parent side turns amber | `ON THIS SIDE OF GLASS` | On this side of glass. |
| 23 | 00:52.8–00:55.2 | Child remains still; blue boundary stays in room | `NOT THE CHILD'S SIDE` | Not the child's side. |
| 24 | 00:55.2–00:57.6 | Parent reaches toward plug; one tiny spark | `REACH FOR THE PLUG` | Parent reaches for the plug. |
| 25 | 00:57.6–01:00 | Waveform collapses; post-line hook: `HALL MIC: LIVE` | `THE MONITOR GOES QUIET` | The monitor goes quiet. |

## Picture and typography direction

Palette: deep navy `#0B1020`, blue-black `#0E1526`, lamp amber `#F5C542`, caption amber `#F5D14E`, threat red `#E2453C`, monitor green `#7CF29C`, white `#F5F4EE`. Flat vectors, smooth radial lamp glow, strong vignette, restrained generated night-vision grain. Keep lower-third captions in the central safe area, condensed sans, white body with amber karaoke word emphasis; the reveal/threat beat switches to red. No photo textures, no drawn or generated hands, no stock assets.

The separate karaoke cues and narration segments will be measured and listed in QA. Voice clips use the same cue grid; gaps are filled by the original score/room tone. The final spoken phrase is followed by quiet and a small visual-only sequel hook.
