# SCRIPT — "What if I never slept again?"

Presenter-led explainer, first film of the register. Written to `docs/RECIPE.md`.
Premise (chosen, defended in `docs/PREMISE_ENGINE.md` §11): a single counter — **hours awake** — ticks
continuously through the film. Every claim is real science with a cited source.

**Format:** 1080×1920 portrait, 30 fps, 75 s target (within 60–90 s).
**Counter:** 0 → 75 hours awake, 1 hour per film second (acceleration stated: 1 film s = 1 real h).
**Pipeline (voice first):** narration is generated before animation; caption beats lock to the
synthesiser's word boundaries. Planned timings below; final beats snap to ElevenLabs `with-timestamps`
word boundaries at production. Draft voice uses local `edge-tts` + `vocal_chain.py` (zero cost); locked
hero narration uses `eleven_multilingual_v2`, stability ≈ 0.35.

**Characters:** presenter (carries the argument) + sidekick (spiky red blob, lands the jokes). Borrowed
craft only — new subject, new characters.

---

## Beat sheet (9 beats)

| # | Beat | Time (s) | Counter (h) | Caption (2–5 w) | Voice line (spoken) | Escalation label |
|---|------|----------|-------------|-----------------|---------------------|------------------|
| 1 | **Hook** — question first | 0–5 | 0→5 | What if I never slept? | "What if I never slept again?" | baseline |
| 2 | **Promise** | 5–24 | 5→24 | I stayed awake for you | "I stayed awake for you. Hour by hour, one number that never stops." | baseline |
| 3 | **Demonstration / Step one** | 24–36 | 24→36 | Legally drunk at 24 | "At twenty-four hours awake, your judgment matches a zero-point-one-zero blood-alcohol level. You're legally drunk." | legally drunk (~0.10% BAC) |
| 4 | **Step two** | 36–48 | 36→48 | Microsleeps start now | "At thirty-six hours, your brain forces microsleeps — involuntary seconds of blackout with your eyes open." | microsleeps begin |
| 5 | **The mistake** | 48–72 | 48→72 | Hallucinations begin | "You think one night won't matter. That's the mistake. By forty-eight hours, hallucinations and perceptual distortions set in. Reality wavers." | hallucinations begin |
| 6 | **Payoff** | 72–75 | 72→75 | Seventy-two hours awake | "Seventy-two hours awake. Psychosis territory. The verified record is two hundred sixty-four hours." | psychosis territory |
| 7 | **The joke** | 75–78 | 75 | That's a documentary. | "That's not a what-if. That's a documentary." | — |

**Note:** beats 3–5 run long (12–24 s) because the counter must tick continuously and the situation gets worse each beat; captions hold on a single 2–5 word phrase while the voice carries the detail. This matches the recipe (counter never pauses; captions change every few seconds). Cut every 1–3 s; presenter animated continuously on holds.

---

## Voice lines (separated, in speaking order)

1. "What if I never slept again?"
2. "I stayed awake for you. Hour by hour, one number that never stops."
3. "At twenty-four hours awake, your judgment matches a zero-point-one-zero blood-alcohol level. You're legally drunk."
4. "At thirty-six hours, your brain forces microsleeps — involuntary seconds of blackout with your eyes open."
5. "You think one night won't matter. That's the mistake. By forty-eight hours, hallucinations and perceptual distortions set in. Reality wavers."
6. "Seventy-two hours awake. Psychosis territory. The verified record is two hundred sixty-four hours."
7. "That's not a what-if. That's a documentary."

Total narration ≈ 160 words (~65–70 s at conversational pace with pauses), fits the 75 s film.

---

## Caption beats (locked to voice word boundaries, voice first)

Planned beats (final start/end snap to ElevenLabs word timestamps):

| Caption | Planned start | Planned end | Counter at start | Counter at end |
|---|---|---|---|---|
| What if I never slept? | 0.0 | 5.0 | 0 h | 5 h |
| I stayed awake for you | 5.0 | 24.0 | 5 h | 24 h |
| Legally drunk at 24 | 24.0 | 36.0 | 24 h | 36 h |
| Microsleeps start now | 36.0 | 48.0 | 36 h | 48 h |
| Hallucinations begin | 48.0 | 72.0 | 48 h | 72 h |
| Seventy-two hours awake | 72.0 | 75.0 | 72 h | 75 h |
| That's a documentary. | 75.0 | 78.0 | 75 h | 75 h |

---

## Counter arithmetic (verified against cue_sheet.json)

`C(t) = t` hours (t in seconds), 1 h per film second. Named frames (30 fps):
- f = 0 (0.0 s) → 0 h
- f = 150 (5.0 s) → 5 h
- f = 720 (24.0 s) → 24 h  ← legally drunk
- f = 1080 (36.0 s) → 36 h  ← microsleeps
- f = 1440 (48.0 s) → 48 h  ← hallucinations
- f = 2160 (72.0 s) → 72 h  ← psychosis territory
- f = 2249 (74.97 s) → ~75 h

---

## Sources (real science)

1. Cleveland Clinic / NIOSH — 24 h awake ≈ 0.10% BAC impairment (above legal driving limit).
2. Sleep-deprivation stage timeline — 24 h judgment/memory/coordination degraded; 36–48 h microsleeps;
   48–72 h hallucinations/perceptual distortions; 72+ h psychosis-like symptoms.
3. Randy Gardner — 264 h (11 days) verified sleep-deprivation record, 1964 (observed by W. Dement).

---

## What is weak

- Counter runs at 36× real time (1 film s = 1 real h); acceleration is stated but is a filmic convention.
- Beat 5 holds one caption for 24 s; relies on the voice and counter to carry interest.
- Full-film caption beats not yet locked to real ElevenLabs word boundaries (done for the 15 s proof only).
