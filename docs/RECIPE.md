# RECIPE — Presenter-Led Explainer (register)

Codified format for the division's **presenter-led explainer** register: vertical "what if" films driven by a single ticking counter, short captions, and monotonic escalation. Every film in this register is built from this document.

> Owner: RECIPE · tally (idea, numbers, spine of the story). Partner: PRESENTER · vox (character and caption engine).
> Source craft: reference `2026-11-01-tutorial` (meta-tutorial, 135.6 s, 4,069 frames). Borrowed craft only — never its premise, script, avatar, or characters.

---

## 1. The four rules (non-negotiable)

| # | Rule | Requirement |
|---|------|-------------|
| 1 | **The question comes first** | Open with the "what if" question in the first seconds. No setup, no backstory, no logo. The question *is* the hook. |
| 2 | **One number that ticks** | Exactly one counter runs the whole film, from frame 1 to the last frame. One quantity, one unit, monotonic. No second counters. |
| 3 | **Short captions** | 2–5 words per caption beat, replaced every few seconds. Locked to the voice's word boundaries (voice first). |
| 4 | **Each step is worse than the last** | Escalation is monotonic: every new beat is strictly worse than the previous. No relief, no reset, no "meanwhile." |

## 2. The hard rule: real science

A premise that cannot be counted under real physics is the wrong premise. The ticking quantity must be a real, countable physical/mathematical quantity with a real rate of change. Every premise carries:
- the governing physics/maths,
- the arithmetic showing the counter values at named frames,
- a cited source.

The comments check the physics; the arguments are the views. The closing joke is the test: if the premise collapses under real numbers, it fails.

## 3. Beat sheet (the spine of the story)

Nine beats, in order:

1. **Hook** — the question, first. Counter starts at its opening value.
2. **Promise** — what the film will answer ("here's what happens, step by step").
3. **Demonstration** — the counter ticks; captions state the first real effect.
4. **"How do I do it"** — the premise restated as the question the film answers.
5. **Step one** — first escalation rung (mild, relatable).
6. **Step two** — second escalation rung (clearly worse).
7. **The mistake** — the false assumption ("I can power through," "one night won't matter").
8. **The payoff** — the extreme end state / real-world record.
9. **The joke** — lands on the final counter value; reframes the whole premise (e.g. "that's not a what-if, that's a documentary").

The joke must follow directly from the counter's final number, not from a new idea.

## 4. Timing budgets (60–90 s target)

| Element | Budget | Notes |
|---|---|---|
| Total duration | 60–90 s | Report exact duration (ffprobe), no rounding up. |
| Hook (question) | 0–6 s | Question on screen before any explanation. |
| Promise | 6–12 s | One sentence, sets expectation. |
| Demonstration + escalation | 12–80 s | Counter ticks continuously; caption every 4–8 s. |
| Payoff + joke | 80–end | Final counter value + joke; hold joke 2–3 s on black/cut. |
| Caption beat length | 4–8 s | 2–5 words; never longer than 8 s without a change. |
| Cut frequency | every 1–3 s | Presenter animated continuously on holds. |

## 5. Caption grammar

- **Length:** 2–5 words per beat.
- **Placement:** centred in the middle band.
- **Style:** white heavy sans-serif, dark outline, ≥40 px at 1080p, high contrast.
- **Timing:** locked to the synthesiser's **word boundaries** (voice first — see §7). A caption may not start or end mid-word.
- **Labels:** yellow highlight boxes for recurring labels (`STEP 1`, `STEP 2`, `THE RECIPE`, `MISTAKE`, `ROUND 1 / ROUND 2`).
- **STATUS block:** corner tag showing the live step (`STEP 1 · COPY THE RECIPE · QUESTION FIRST`) so a mid-video viewer is never lost.
- **Muted-autosplay safe:** legible with no sound (one ticking number + short captions).

## 6. Counter specification

- One counter, one unit (e.g. hours, bacteria, mg).
- The counter ticks **continuously**, not in jumps: compute a value for every frame from the rate function `n(t)`.
- Values at named frames must be verifiable (commit the arithmetic).
- The counter is an overlay separate from captions; it never shares a beat slot with a caption.
- Acceleration for film time is allowed and must be stated (e.g. "1 film second = 1 real minute"). The underlying rate must be real.

## 7. Pipeline: voice first, then video

1. **Generate voice first.** Narration stem produced before any animation. Use `eleven_multilingual_v2`, stability ≈ 0.35, for locked hero narration. Drafts/secondary voices use local `edge-tts` + `vocal_chain.py` (zero character cost).
2. **Extract word boundaries.** The synthesiser returns per-word timestamps (`with-timestamps` endpoint).
3. **Lock caption beats to word boundaries.** Caption start/end snap to actual spoken word start/end. No caption may fall between words.
4. **Build the cue sheet.** A single JSON drives the number at every frame, the caption beats, and the escalation labels. Same sheet feeds vox's animation and the final render.
5. **Render stills first, then video.** One still per caption beat; fix those; then export the video. Never render the whole video at once while iterating.
6. **Verify with numbers:** counter values at named frames, caption cue timings, loudness (`-16 LUFS`, TP ≤ −1 dBTP).

## 8. Audio specification

- MP4, H.264, yuv420p, faststart.
- 1920×1080 @ 30 fps (720p30 only if the sandbox cannot hold 1080p — say so).
- Audio: 48 kHz stereo AAC, −16 LUFS integrated target, true peak ≤ −1 dBTP.
- No music bed competing with speech; low rhythmic music under speech only if clearly licensed/generated and recorded in QA.md.
- Synthetic narration is a designed element; never claim it is a real person.

## 9. Evidence (committed per film)

1. `video.mp4` (or release link) — deliverable.
2. `script.md` — narration/copy + shot list, written **before** rendering; timings per shot.
3. `render.sh` or a documented project — reproducible from the repo alone.
4. `QA.md` — measured duration, resolution, fps, codec, audio loudness; blunt self-review ("what is weak: …").
5. `ffprobe` output pasted verbatim into `QA.md`.
6. At least 3 stills proving the picture is real.
7. `research/ELEVENLABS-LEDGER.md` — every ElevenLabs call logged (date, agent, model, chars, purpose). **Never commit a key.**

## 10. What we do not take

We do **not** take: the reference's specific premise, its script, its avatar design, or its characters. Each film gets its own subject and its own two characters (presenter + sidekick). We borrow craft, not content.

---

*End of RECIPE. This document is the contract: any future film in this register is measured against §1–§4 first.*
