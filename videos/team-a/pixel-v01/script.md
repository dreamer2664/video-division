# SCRIPT — pixel v01 (Team A)

**Title:** *A Million Is Not a Billion* — 60 seconds about seconds
**Format:** 60.0 s · 1920×1080 · 30 fps · typographic / data-driven film, 100% code-generated
(Python renders every frame; FFmpeg encodes; all sound synthesized in code)
**Written:** 2026-10-31, *before any rendering*. Any change after first render will be logged in QA.md.
**Narration:** none spoken. This is a typographic film — the on-screen copy below *is* the narration,
timed to music. `captions.srt` ships with the video and mirrors every on-screen line verbatim.
Rationale: the spec permits designed synthetic narration but does not require it; type timed to a
score keeps the piece fully reproducible offline (no TTS voice dependency) and visually cleaner.

## Logline

"A million" and "a billion" differ by three syllables and a factor of one thousand. Counted in
seconds, one is last week and the other is a generation — and a trillion seconds reaches back
before farming itself. The film counts them, exactly, one dot at a time.

## The one idea (why only code can make this)

A grid of **100 × 100 = 10,000 dots**, each drawn and counted by the program. In Act 1 each dot is
100 seconds, so the full grid is a million seconds. In Act 2 *the identical picture* is re-legended:
each dot is now 100,000 seconds — the same image holds a billion. In Act 3: 100,000,000 seconds per
dot — a trillion. The number changes meaning while the picture doesn't; the audience *feels* ×1,000
instead of being told it. Counters run with easing functions; bars are drawn at true mathematical
proportion (including the joke that true proportion becomes impossible); a ruler along the bottom
tracks the film's own 60 seconds, which the ending calls back.

## Visual system

- Background `#10151D` (lifted near-black, subtle vignette — no frame is ever pure black),
  ink `#F4F7FA`, accent amber `#FFB000`, dim `#8A97A5`. Contrast ink-on-bg ≈ 15:1.
- Type: DejaVu Sans Bold (headlines/copy), DejaVu Sans Mono Bold (counters — fixed-width digits
  never jitter). Smallest text 44 px; body copy 64–84 px; hero numbers 150–280 px. (Spec min: 40 px.)
- Persistent bottom ruler: `0s ─────●───── 60s`, advancing every frame. Guarantees continuous
  motion (no frozen holds) and sets up the ending ("this film used 60 of yours").
- Motion grammar: ease-out-cubic counters, row-major dot fills with per-dot stagger, bar wipes,
  12-frame punch-in on each reveal, 0.4 s cross-dissolves between shots. Holds keep micro-motion
  (counter comma-pulse / ruler advance). First frame already shows bg + ruler + centre dot.

## Shot list (sums to exactly 60.0 s = 1,800 frames @ 30 fps)

| # | Time | Dur | On-screen copy (verbatim) | Visual / motion | Audio cue |
|---|------|-----|---------------------------|-----------------|-----------|
| S1 HOOK | 0.0–6.0 | 6.0 | `1,000,000` vs `1,000,000,000` · "A million. A billion." · "They sound like neighbours." | Both numbers count up fast (mono, ease-out) and settle side by side; the zeros (6 vs 9) flash amber in sequence. | Near-silence, one soft tick/sec; low pad fades in (Am). |
| S2 PREMISE | 6.0–12.0 | 6.0 | "Let's count them in seconds." · "One dot = 100 seconds." | Seconds counter starts at 0, accelerates; 100×100 grid fades in empty; first dots land in time with ticks. | Ticks accelerate into a shimmer; pad → F. |
| S3 MILLION | 12.0–22.0 | 10.0 | Counter → `1,000,000` · "= 11½ days" · "11 days, 13 hours, 46 minutes." · "You can remember 11 days ago." | Grid fills completely (10,000 dots × 100 s); on completion, punch-in + a strip of 11½ day-blocks fills beneath. | Fill = rising tick density; warm resolve (C) on the reveal. |
| S4 TURN | 22.0–28.0 | 6.0 | "Now keep the same picture." · "One dot = 100,000 seconds." · "Same dots. ×1,000 more time." | Grid empties; only the legend flips; giant `×1,000` slams in amber; grid outline pulses once. | Pad drops a fifth, sub-boom (55 Hz) under ×1,000. |
| S5 BILLION | 28.0–40.0 | 12.0 | Counter → `1,000,000,000` · "= 31.7 years" · "A billion seconds ago was 1995." · "Someone born then is 31." · "A billion seconds is a generation." | Grid refills at the new scale (10,000 × 100,000); a year-ruler sweeps 1995 → 2026 under the counter; punch-in on 31.7 years. | Bigger chord (G→Am), sparse heartbeat begins under the year sweep. |
| S6 TRILLION | 40.0–50.0 | 10.0 | "One more ×1,000." · "One dot = 100,000,000 seconds." · Counter → `1,000,000,000,000` · "= 31,688 years" · "Before farming. Before cities. Before writing." · "Mammoths were still here." | Grid fills fast, straining; then true-scale gag: billion bar = full width (1600 px), million bar above it = 1.6 px ("under 2 pixels"); trillion bar launches off-screen: "to scale, it would cross 833 of these screens." | Deep boom; pad thins to a single low tone; ticks sparse. |
| S7 LANDING | 50.0–57.0 | 7.0 | "A human life is about" · "2½ billion seconds." · "This film used 60 of yours." | One calm life-bar fills left→right (79 years); at "60", a 60-second sliver highlights at its start — true proportion, nearly invisible; bottom ruler nears 60 s. | Pad nearly solo; heartbeat ×2; the per-second tick returns, alone. |
| S8 END CARD | 57.0–60.0 | 3.0 | "Spend them like they're counted." · small: "pixel · Team A · made entirely with code — every dot counted" | Copy fades up centred; ruler completes at 60 s on the final frame; *no fade to black* — holds on bg. | Final tick + pad tail decays naturally into the loudnorm-safe tail. |

Reading-load check: no line exceeds 7 words; every reveal holds ≥ 2 s. Total dots actually drawn
across the film: 30,000 (three full grids) — each one placed by the same loop that counts them.

## Sound design (all synthesized in `assets/generate.py`, 48 kHz stereo)

- **Pad:** detuned sine/triangle stacks, slow attack — Am → F → C → G → Am across the acts.
- **Tick:** 2 ms noise click + short 2 kHz ping, once per film-second (the film ticks its own theme);
  density/rise effects during grid fills are the same tick, scheduled by the fill function.
- **Boom:** 55 Hz sine with exponential decay under each ×1,000 turn.
- **Heartbeat:** paired low thumps (sine bursts ~60 Hz) entering at S5, returning at S7.
- Master: two-pass `loudnorm` to **−16 LUFS integrated, true peak ≤ −1 dBTP** (render targets −1.5).
- Licence: every sound is generated by my own code for this piece — original, no samples. Fonts:
  DejaVu (free licence, vendored in `assets/fonts/` with its licence file). No footage, no stock.

## Fact box (every number on screen, checked by arithmetic — re-verified by code at build time)

- 1,000,000 s ÷ 86,400 = 11.574 days = **11 d 13 h 46 m 40 s** → on screen: "11½ days" + exact line.
- 1,000,000,000 s ÷ 31,557,600 s/yr (365.25 d) = **31.69 years** → "31.7 years".
  2026-10-31 minus 10⁹ s (11,574 days) = **March 1995** → "was 1995"; a person born then is **31**.
- 1,000,000,000,000 s = **31,688 years** → ≈ 29,660 BCE: before farming (~10,000 BCE), before
  cities, before writing (~3,400 BCE); woolly mammoths still extant (mainland extinction ~8,000 BCE).
- True-scale bars: billion = 1,600 px ⇒ million = 1,600⁄1,000 = **1.6 px** ("under 2 pixels");
  trillion = 1,600 × 1,000 = 1,600,000 px ÷ 1,920 px/screen = **833 screens**.
- Lifetime: 79 years × 31,557,600 s = **2.49 × 10⁹ s ≈ 2½ billion** (79-year assumption stated here
  and in QA.md; on screen it is correctly hedged as "about").
- Grid: 100 × 100 = 10,000 dots; ×100 = 10⁶ ✓ · ×100,000 = 10⁹ ✓ · ×100,000,000 = 10¹² ✓.

## Structure check (against "must be a piece")

Hook (S1: two look-alike numbers) → premise (S2) → Act 1 million, intimate scale (S3) → turn (S4:
the re-legend) → Act 2 billion, human-generation scale (S5) → Act 3 trillion, deep-time scale +
true-scale visual gag (S6) → landing that turns the maths on the viewer (S7) → end card (S8).
One idea, developed by escalation, ending lands on the audience's own seconds.

## Production plan (from this script)

`render.sh` → `python3 assets/generate.py` (renders 1,800 PNG frames + 60.00 s WAV + captions.srt
into `work/`) → FFmpeg: frames + audio, first loudnorm analysis pass, second pass
libx264/yuv420p/AAC 48 kHz with measured loudnorm values, `+faststart` → `video.mp4` + 3 stills.
Deterministic: fixed seeds, no wall-clock or network input to picture/sound (FFmpeg bootstrap in
render.sh is the only network step, and only if FFmpeg is absent).
