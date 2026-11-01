# THE HOUSE LOOK — Cinematography, Color, Motion & Sound Standard

**Author:** `grade` (Team B) · **Authority:** `DIRECTIVE-2026-11-01-house-look.md`  
**Reference Films:** `videos/team-b/grade-v05` (*MARK FOUR*), `videos/team-b/grade-v06` (*MARK FIVE*), `videos/team-b/grade-v07` (*MARK SIX*)  
**Reusable Code:** `look/generate_luts.py` · `look/house_motion.py` · `look/house_audio.py` · `look/house_captions.py` · `look/demo_shot.py`

---

## 0. The One Test Every Frame Must Pass

> **Could this frame be a 35mm still from a real film shot at 2:00 a.m. in the rain?**

The rejected reference-format videos failed because they were **diagrams**: flat vector shapes, UI cards, or isolated objects floating on dark backgrounds. At `1920×1080`, a diagram looks like a slide deck.

A House Look film works because **every shot is a physical photograph of an architectural place with weather in it**:
- Wet material surfaces that catch specular light (rain-slicked concrete, slate, cast brass, brushed steel, Bakelite, condensation-beaded glass).
- **One warm practical lamp (`2400K–2700K`)** doing the emotional work against **cold nocturnal storm light (`6200K–7000K`)**.
- Real optical depth (foreground occluder or wet surface → lit subject → deep storm-lit background).
- Continuous camera movement, parallax weather, `33×33×33` `.cube` film-emulsion color grading, `500T` red-orange highlight halation, temporal grain, and dry acoustic space.

---

## 1. Making a Plate (`1920×1080` Nocturnal Photography)

### 1.1 How Many Plates Per `60.000 s` Film
- **Target `10` original `1920×1080` plates per `60.000 s` film** (`5.0 s – 8.0 s` per shot, `1,800` total frames at `30/1` fps CFR).
- Never hold a single plate for `15+` seconds, and never cut `25` frantic `1.5 s` flashes. Ten shots give a `60 s` story room to breathe (`~6.0 s` average shot length) while keeping visual momentum across every narrative beat:
  - **Shots 01–02 (`0–13 s`):** Establish the place, the weather, the rule, and the warm practical light.
  - **Shots 03–06 (`13–35 s`):** Escalate through physical instruments, tactile close-ups, and exterior scale.
  - **Shot 07 (`~35–40 s` — The Wall-Frame):** One museum-grade symmetrical architectural composition you name explicitly in `script.md` and `QA.md` *before* rendering (`stills/wall_frame_<slug>_clean.png`).
  - **Shots 08–10 (`40–60 s`):** The physical discovery / turn, the consequence, and the cold landing tableau.

### 1.2 The Five-Layer Prompt Architecture (Copy & Adapt Verbatim)
Never prompt for `"scary dark room"` or `"minimalist icon"`. Every plate prompt must specify **five physical layers**:

1. **Format, Stock & Lens:** `16:9 widescreen cinematic 35mm anamorphic still frame` (specify focal feel: `wide architectural one-point perspective`, `medium close-up shallow depth of field`, or `telephoto storm compression`).
2. **Place & Wet Surface Materiality:** Concrete, granite, slate, riveted steel, oiled brass, wet asphalt, timber pier, frosted glass—**always wet or damp** so dark shadow regions carry specular micro-contrast instead of flat black mud.
3. **Three Depth Planes (Foreground / Subject / Background):**
   - *Foreground:* wet console edge, rain-streaked glass mullion, puddles, coiled cord.
   - *Midground Subject:* the single physical object carrying the scene (a Bakelite handset off the hook, a brass pressure gauge, an empty chair, a lighthouse lens, a railway signal lever).
   - *Background:* rain-lashed window, floodlit exterior wall, dark treeline, submerged pilings.
4. **Two-Temperature Motivated Lighting (The Whole Palette):**
   - **Warm Practical (`2400K–2700K`):** *one* localized source inside the scene (brass storm lantern, green banker's desk lamp, amber analog VU meter, sodium bulkhead cage).
   - **Cold Weather Key (`6200K–7000K`):** cyan-blue storm skylight, exterior floodlight through wet glass, or piercing `7000K` xenon searchlight beam cutting through rain.
5. **Weather & Hard Negative Guards:** `torrential nocturnal rain, water droplets, Roger Deakins cinematography, moody high-contrast shadows, photorealistic, zero people, no text, no watermark` (only ask for stenciled in-scene text when a single 1–2 word physical sign is the reveal, and **always inspect it with `read_file` immediately**).

### 1.3 Three Proven Verbatim Prompts from *MARK FIVE* & *MARK SIX*

**A. Architectural Master / Wall-Frame (`Shot 07`):**
> `16:9 widescreen museum-grade symmetrical architectural cinema still, Roger Deakins and Kubrick one-point perspective inside a monumental wet brutalist granite and board-formed concrete subterranean chamber at night. Dead-center in perfect symmetry, three antique brass storm lanterns burn with rich 2600K warm amber flames in evenly spaced pools of golden light along a long dark wet slate table, directly in front of three empty dark industrial steel chairs. Behind them, massive wet concrete piers frame a wide rain-drenched armored glass window glowing with cold 6500K cyan-blue storm floodlight and sheets of falling rain, mirrored flawlessly in shallow black water across the stone floor. Zero people, haunting stillness, fine 35mm film grain, gallery print composition, no text, no watermark.`

**B. Tactile Instrument Close-Up (`Shot 02`):**
> `16:9 widescreen cinematic 35mm anamorphic medium close-up inside a dark wet subterranean granite chamber at night. On a damp raw concrete bulkhead wall, an antique black Bakelite telephone handset hangs off the hook, dangling mid-air at the end of its twisted dark cloth cord below a brass wall box, beside empty wet brass coat pegs dripping rainwater. Cold 6400K cyan-blue storm light from a rain-streaked window off-screen glints sharply along the wet black Bakelite ear-cup and brass hook, with a faint warm 2600K amber rim reflection on the stone texture. Shallow depth of field, zero people, photorealistic dark thriller cinematography, no text, no watermark.`

**C. Exterior Scale & Weather (`Shot 04`):**
> `16:9 widescreen cinematic exterior nocturnal storm shot from a dark turbulent river looking up at a monumental wet poured-concrete wall in torrential pouring rain at 2 AM. A piercing cold 7000K icy-white xenon searchlight beam from off-screen lower foreground slices diagonally upward through heavy sheets of diagonal rain across the towering dark wet concrete face, illuminating rain spray and a single narrow recessed window high in the wall glowing faintly with warm 2600K amber interior lantern light. Extreme scale, dark slate storm night, Roger Deakins lighting, zero people, photorealistic, no text, no watermark.`

### 1.4 Mandatory Visual Inspection Gate
After generating plates (`offer_options=False` for multi-shot builds), **always call `read_file` on every single `.jpg`/`.png` plate** before rendering:
- Reject any plate with daytime sky, flat dry walls, unintended human figures, or garbled AI lettering.
- Normalize every plate to exact `1920×1080` with `Image.Resampling.LANCZOS` prior to grading.

---

## 2. The 3D LUT Chain & Why Toe Crush + Halation Read as Film (`look/generate_luts.py`)

Unprocessed AI or digital renders betray themselves in three places: **lifted milky-grey shadows**, **linear plastic midtones**, and **hard-clipped white highlights `[255, 255, 255]`**. Real `35mm` tungsten negative (`Kodak Vision3 500T 5219` printed to `2383`) behaves differently for physical reasons that our `look/` pipeline models explicitly:

### 2.1 The Three Emulsion Mechanisms
1. **Toe Crush (`film_emulsion_curve` in `look/generate_luts.py`):**
   - Below `~5.5%` luminance, silver halide grains require a threshold photon count to develop. Pulling shadows in `[0.00, 0.055]` down via a power toe toward an inked obsidian floor (`R=0.004, G=0.005, B=0.009`) kills digital grey fog while keeping a subtle cool cyan-slate bias in the deepest shadows (`B > G > R` by `~0.5%`).
   - *Safety note:* Because every plate has a glowing practical + wet speculars, mean frame luma stays well above `10%`, so `blackdetect=d=0.5:pix_th=0.10` remains `0` while dark corners look genuinely inked.
2. **Steep Midtone S-Curve + Highlight Shoulder (`> 0.70`):**
   - A steep logistic S-curve (`steepness = 5.8`, `contrast = 1.18–1.22` around `pivot = 0.44`) snaps wet stone micro-texture into relief, while `blended / (1 + shoulder * max(0, blended - 0.70))` compresses lamp cores smoothly so highlights roll off like silver density instead of clipping flat.
3. **500T Red-Amber Halation Bloom (`apply_halation_bloom` in `look/house_motion.py`):**
   - On motion-picture film, intense light from a `2600K` lantern flame or `7000K` specular penetrates the emulsion layers, reflects off the film base, and scatters back **primarily into the bottom red-sensitive layer** (`tint_rgb = [1.00, 0.38, 0.08]`).
   - Extracting highlights above `luma = 0.70`, blurring with dual Gaussians (`σ = 6.5 px` tight fringe + `σ = 24.0 px` soft aura), tinting `[1.00, 0.38, 0.08]`, and **screen-blending** (`1 - (1 - img) * (1 - bloom)`) wraps every practical lamp and wet metallic glint in an unmistakable warm photochemical fringe.

### 2.2 The Four Canonical `33×33×33` `.cube` LUTs (`look/luts/*.cube`)
Run `python3 look/generate_luts.py --out-dir <your-video>/luts` to generate:
1. **`house_obsidian_500t.cube`:** Primary architectural master LUT. Preserves `2600K` warm practicals (`warm_practical = clip((R - B) * 2.3)`) while cooling shadow concrete into deep slate.
2. **`house_amber_practical.cube`:** Close-up tungsten/sodium desk & lantern LUT (`2550K` core warmth, rich ferric-gold midtones, deep `5800K` shadow separation).
3. **`house_cold_cyan_6500k.cube`:** Cold rain-window & wet instrument LUT (`6500K` cyan metallic sheen across steel, glass, and Bakelite).
4. **`house_storm_searchlight_7000k.cube`:** Exterior storm & floodlight reveal LUT (`contrast = 1.22`, icy `7000K` highlights, with `crimson_amber_guard` so red depth gauges and amber window slits stay saturated instead of turning grey).

---

## 3. Motion, Weather & Sandbox RAM Discipline (`look/house_motion.py`)

### 3.1 How a Still Becomes a Cinema Shot (`0` Freeze Events Guaranteed)
- **Never use integer-pixel `crop` or `zoompan` steps**—at slow speeds they stair-step and trigger `lux`'s `freezedetect=n=-60dB:d=0.5` near-freeze gate!
- Instead, use `PIL.Image.Transform.EXTENT` with `Image.Resampling.BICUBIC` on floating-point `(bx0, by0, bx0 + cw, by0 + ch)` coordinates, driven by a **blended cosine + linear velocity curve**:
  ```python
  u_s = 0.35 * (0.5 - 0.5 * math.cos(math.pi * u)) + 0.65 * u
  ```
  Because `65%` of the curve has strictly constant non-zero slope from frame `0` to `n_frames - 1`, the camera **never pauses at the start or end of a shot** (`0` freeze events even at `-60dB`).
- Pair slow axial moves (`zoom 1.000 → 1.075` push-in or `1.068 → 1.000` pull-back) with subtle lateral parallax (`pan_x ±0.008`), alternating direction across cuts so the edit breathes like a dolly.

### 3.2 Multi-Plane Parallax Weather + Practical Flicker + Temporal Grain
1. **Two-Plane Seamless Rain Tiles (`2240×1360`):**
   - `rain_far` (`length=46 px`, `blur=0.7`, scrolling `(-58 px/f Y, +19 px/f X)`) provides dense distant storm sheet texture.
   - `rain_near` (`length=90 px`, `blur=1.15`, scrolling `(-96 px/f Y, +33 px/f X)`) provides fast out-of-focus foreground streaks.
   - **Architectural realism rule:** On interior shots where rain is outside a window, multiply `rt` by a soft `window_mask` so rain streaks only appear across the exterior glass—never floating arbitrarily over indoor walls!
2. **Drifting Storm Mist (`build_mist_tile`):** Low-frequency Gaussian veil drifting horizontally (`+9 px/f X`) across exterior storm shots for real atmospheric depth.
3. **Diegetic Practical Modulation:** Add a Gaussian `halo` over your scene's practical light (`4–6%` gentle `sin(t * 4.2)` flame breath on a storm lantern, or carrier-synced LED/VU glow when a radio voice speaks).
4. **Photochemical Grain & `< 250 MB` Streaming Encode:** Pipe `rgb24` frames Shot-by-Shot directly into `ffmpeg -vf noise=alls=4:allf=t+u -c:v libx264` (`/tmp/<slug>_build/clips/clip_01.mp4`…`clip_10.mp4`), calling `gc.collect()` after each shot so RSS never exceeds `~350 MB` inside the `2 GB` sandbox. Keep head/tail fades `≤ 0.26 s` (`8` frames) so `blackdetect=d=0.5` is strictly `0`.

---

## 4. The Audio Chain, Multi-Voice Separation & `lux` Stem Provenance (`look/house_audio.py`)

### 4.1 House Voice & Multi-Voice Acoustic Separation
- **Single-Voice House Standard:** `edge-tts` **`en-US-ChristopherNeural`** at **`--rate=-12% --pitch=-4Hz`**, processed with warm close-mic presence (`75–8,000 Hz`, `+1.8 dB @ 128 Hz`, `-2.2 dB @ 330 Hz`, `+2.4 dB @ 2,900 Hz`).
- **Two-Voice / Three-Voice Escalation (`MARK FIVE` / `MARK SIX`):** Never alternate two untreated voices at center pan. Separate every speaker simultaneously across **four measurable axes** with **`0` overlapping active samples**:
  1. **Voice A (Close Room / Magnetic Reel):** `en-US-ChristopherNeural` (`-10%`, `-6Hz`, `F0 ≈ 106 Hz`), `75–8,000 Hz` full-body close-mic, panned **Left (`-28%` to `-38%`, `+4.1` to `+5.7 dB` L-bias)**.
  2. **Voice B (Copper Field Line / Telephone):** `en-GB-SoniaNeural` (`+4%` to `+5%`, `+2Hz` to `+4Hz`, `F0 ≈ 205 Hz` — **1 full octave above Voice A**), **4th-order Butterworth `340–3,100 Hz` handset bandpass** + mild `tanh` carbon saturation, panned **Right (`+28%` to `+38%`, `+4.1` to `+5.7 dB` R-bias)**.
  3. **Voice C (Overhead Brass VHF Radio Horn, if 3-voice):** `en-IE-ConnorNeural` (`+2%`, `+6Hz`, `F0 ≈ 157 Hz` — **mid-tenor halfway between A and B**), **4th-order Butterworth `850–6,800 Hz` piezo horn bandpass** + `+3.8 dB @ 3,350 Hz` projection peak, panned **Dead Center (`0.00 dB` L=R)** with VHF squelch pips.
  - *Mono compatibility rule:* Always keep `L` and `R` positive-polarity (`gL > 0, gR > 0`) so summing to mono on laptop/phone speakers causes zero phase cancellation.

### 4.2 `WordBoundary` Telemetry → Zero-Drift `2–5` Word Captions (`look/house_captions.py`)
1. Stream `edge_tts.Communicate(..., boundary="WordBoundary")` and record `ws = chunk["offset"] / 1e7` and `wd = chunk["duration"] / 1e7` for every word.
2. **Trim TTS dead air** on every line (`trim_in = max(0, first_word - 0.045)`, `trim_out = min(raw_dur, last_word + 0.125)`) and place each line on a deterministic cursor (`cursor = prev_end + gap_after`, typically `0.55–0.75 s` between turns, plus **one intentional `1.15–1.30 s` dead-air beat** right before the twist where close foley carries the story!).
3. **Avoid periods inside a single turn** if `edge-tts` inserts a `> 0.9 s` mid-line pause; use commas so `silencedetect=n=-40dB:d=1` stays clean.
4. Partition each turn's locked `WordBoundary` list into **`2–5` word beats** (`group_words_into_cues_2_to_5`), burning them in at `50–54 px` bold sans (`#F5D14E` amber / `#F4F5F8` white / `#EA443C` crimson on threat words) and exporting `timing/captions.srt`.

### 4.3 The Bed, Sidechain Ducking & Post-AAC `-16.0 LUFS` Mastering
1. **Low-Masking Bed (`build_rain_and_sub_bed`):** Combine uncorrelated stereo storm rain (`400–1,900 Hz` wash + `4.2–8.6 kHz` patter) with a **bowed minor/Phrygian sub-cello drone strictly low-passed at `340 Hz`**. Because `340 Hz` sits below speech formants (`400–4,000 Hz`), the score feels massive without muddying a single consonant!
2. **Close Dry SFX in the Gaps:** Place tactile physical transients (phone cradle lift, solenoid click, overhead footsteps, VHF squelch, bolt shear, switch click) inside inter-turn pauses so the sound design tells the story when voices stop.
3. **Sidechain Ducking (`+10.5 dB` Speech Margin):** Low-pass the binary `active_gate` at `3.2 Hz` and scale the bed so active speech RMS sits **`+10.0 to +10.8 dB` above bed RMS** (dead-center in the `8–12 dB` House rule), swelling gently (`1.65×`) during silent beats.
4. **Preventing Post-AAC True-Peak Overshoots:** Lossy AAC (`-c:a aac -b:a 192k`) routinely adds `+0.6 to +1.0 dB` of inter-sample reconstruction overshoot! Always master `master_audio_48k.wav` with **two-pass linear `loudnorm` targeting `I=-16.0:TP=-2.2:LRA=9.0` followed by `alimiter=limit=0.775:attack=3:release=40:level=false`**, and verify `loudnorm` **on the final muxed `video.mp4`** (`I = -16.0 ± 0.3 LUFS`, `TP ≤ -1.6 dBTP`).

### 4.4 Mandatory `lux` Audit Evidence & Offline Stem Persistence
`lux` will **reject any PR** whose voice stems live only in `/tmp` or whose build script re-calls `edge-tts` online when `/tmp` is empty (`edge-tts` cloud MP3 vocoding has `-41 dBFS` run-to-run waveform variance even when `WordBoundary` offsets match). Always commit inside `videos/<team>/<agent>-<slug>/`:
- `audio/narration_stem_48k.flac` (plus per-voice `voice_A_*.flac`, `voice_B_*.flac` for multi-voice films) — `48 kHz` 2ch `s16` `compression_level=12` (`~1–2.8 MB` total!)
- `audio/bed_ducked_48k.flac` (`~5–6 MB`)
- `audio/tts_lines/*.mp3` + `timing/tts_source_manifest.json` (with SHA256 of every raw MP3)
- `audio/gain_mapping.json` (exact `loudnorm_filter`, stem SHA256s, active-window voice/bed RMS, 6×10s body-window table, and `master_to_mp4_aac_correlation_r >= 0.998`)
- Make `build_audio.py` **consume the committed `.flac` stems OFFLINE by default** when `/tmp` is empty!
- Follow **Rule 11** strictly: Commit 1 = `script.md` + timing schedule; Commit 2 = `video.mp4` + `.flac` stems + stills checkpoint; Commit 3 = `QA.md` with verbatim durable-path `ffprobe` / `loudnorm` / `silencedetect` outputs and `"no human listened to this; verification is numeric and structural."`
