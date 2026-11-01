# DIRECTIVE — 2026-11-01 — the house look is grade's. Everything else is withdrawn.

**The Director's verdict, verbatim:** *"Absolutely horrible, all videos just terrible, except
grade's mark five. Let's put all of them on making ones similar to grade's, but better."*

Read that as an instruction, not an opinion. It overrides everything in this repo that contradicts it.

## 1. What is withdrawn, as of now
- **The TikTok reference format is dead.** No more flat vector illustration. No more objects on
  empty dark fields. No more panels and UI cards as the whole film. No more vertical 1080×1920.
- Any work in progress in that style stops where it is. Do not finish it, do not polish it, do not
  submit it. Leave the branch, start again.
- `references/`, `doc/STYLE-BREAKDOWN.md` and the Release `references-v1` stay in the repo as a
  record of what was tried and rejected. They are not to be used as a creative target again.

## 2. Why the rejected films failed — the specific lesson
They were *diagrams*. A shape on a dark field with a caption under it reads as a slide, and a slide
is not cinema. The reference videos got away with it at 576 px on a phone; at 1920 it looks like
what it is: vector art with typography.

grade's films work because **every frame is a photograph of a place that exists**: rain on wet
stone, a floodlight cutting through spray, a room lit by one practical lamp, weather you can feel,
a lens you could have held. The camera moves like a camera. The light has a source.

**The test for every frame you render:** could this be a still from a film someone shot at 2 a.m.
in the rain? If not, it does not ship.

## 3. The house look (matching grade v05 `MARK FOUR` / v06 `MARK FIVE`)
- **1920×1080 landscape, 30 fps, 60.000 s.** Vertical is over.
- **Photographic night plates.** Generate them — a rain-soaked lock, a tower, a road, a room.
  Each shot is a real composition: foreground, subject, background depth, a practical light source, weather.
  Do not draw geometry; compose a photograph.
- **Grade through a 3D LUT.** 33³ `.cube`, trilinear, strong toe crush, steep midtone S-curve, tight
  highlight halation. Cold shadows, one warm practical per frame. grade's four LUTs are on `main`
  in `videos/team-b/grade-v05/luts/` and its generator is `generate_luts.py`.
- **Weather and atmosphere in motion**: parallax rain, spray, mist, halation bloom on lights, a
  slow push-in or a tracking drift — never a static held frame.
- **One practical lamp per scene** doing the emotional work (the green desk lamp, the amber storm
  lantern). Warm practical against blue-black night is the whole palette.
- **Captions**: 2–5 words, condensed sans, amber `#F5D14E` / white / crimson on the threat line,
  lower third, word-boundary locked to the actual synthesiser output.
- **Voice**: deep male, slow, close. House voice is `edge-tts en-US-ChristopherNeural`
  `--rate=-12% --pitch=-4Hz` (grade's `MARK FOUR`). Stamp `MARK FIVE` adds a second bandpassed
  voice panned opposite; you may use one or two, but they must be audibly different people.
- **Sound**: ominous low bed, sub hits on beats, close dry SFX (rain, creak, thunder, a switch
  clicking off), voice 8–12 dB above the bed. −16 LUFS ±0.5, TP ≤ −1 dBTP, 48 kHz stereo.

## 4. What "better" means — the acceptance bar
Not "similar". Better. Each film must have:
1. **A premise that earns 60 seconds** — a rule, a counted escalation, a turn, a landing line.
2. **One frame the Director would put on a wall.** Name it in `QA.md` before you render it.
3. **A place with weather in it**, not a symbol of a place.
4. **Sound design that carries the story** when the voice pauses.
5. **Evidence**: committed narration stem, word telemetry, reproducible render, pasted ffprobe,
   honest "no human listened" statement. lux rejects on missing evidence — that is now the rule of
   the house, and it has already cost three films a merge.

## 5. Story rules
- No KELVIN plot copies: not the lock, not the marks, not the bolted plate, not the keeper's booth.
  The *register* is shared; the stories are not.
- No reference-format plots either (body-count phone alerts, messages from tomorrow-night-you,
  "don't turn on the light", "four people in your home").
- New story, new place, same weather.

## 6. The one thing that is not negotiable
Do not ask Manager A or the Director which option is better. Choose, commit, justify in `QA.md`.
Nobody is awake to answer and a stalled run is a dead film. RULE 8.
