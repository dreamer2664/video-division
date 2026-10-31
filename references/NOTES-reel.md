# reel — v07 reference study (before picture render)

## Ten frame-by-frame observations
1. **01, f_00061, 02.00 s:** A small figure, bed and window sit in a dark, flat elevation; the time is high left and a bold timestamp beat sits lower centre.
2. **01, f_00301, 10.00 s:** One large centred screen isolates the message; the short caption uses white with one blue stressed word and a dark outline.
3. **01, f_00961, 32.00 s:** A rule becomes a simple oversized typographic card against a navy wall; a second, shorter beat remains lower centre.
4. **01, f_01861, 62.00 s:** A stacked screen interface occupies the centre; the current word is colour-emphasised while the remainder stays white.
5. **02, f_00061, 02.00 s:** A long, symmetrical hallway reduces the person to a flat silhouette; a small red time stamp and lower caption orient the viewer.
6. **02, f_00301, 10.00 s:** A single violet rectangle fills the composition; the caption is large, outlined and two words, one highlighted.
7. **02, f_00751, 25.00 s:** An enlarged face cuts closer within the same hallway palette; the doorway provides one warm pool of light.
8. **02, f_01471, 49.00 s:** A horizontal split contrasts two locations; concise text stays in the lower half rather than touching the frame edge.
9. **03, f_00061, 02.00 s:** A centred house silhouette, moon and red windows establish night with almost no detail; the first time caption is warm and legible.
10. **03, f_00301, 10.00 s:** A framed group becomes the entire visual idea; a lower phrase progressively changes emphasis from white to amber.

## Study method and limits
All **5,714** release JPEGs were decoded individually in order (01: 2,505; 02: 1,800; 03: 1,409). Each was resized to 72×128 for luminance, centre/edge and adjacent-frame difference measurements; the original 288×512 archive files, the three supplied contact sheets and the labelled frames above were also visually inspected. Archive frames at 10 s were cross-checked against all three MP4s; their matching-source mean absolute RGB errors were 2.49, 5.78 and 3.05 on a 0–255 scale. This is a computational study of every archived frame, not a claim to have manually watched every frame or listened to audio. Nothing from the references is used in the production.

The README descriptions for 01 and 03 appear reversed relative to their actual decoded content: 01 contains the tomorrow-night messages and 03 the household-count alert. Analysis here follows the **file and frame numbers**, not those descriptions. Across 01/02/03, mean luminance was 28.7/48.3/38.8 of 255; edge means were 18.3/26.4/21.8 versus centre means 44.5/78.6/59.1. The low edge values support dark fields and vignette. A high-threshold adjacent-difference detector found only large changes, not every editorial cut; do not mistake its candidates for a complete cut count.

## Caption beat timings to match
The reference windows below are approximate: OCR of frames sampled every **0.20 s** in the first 15 s, checked against the picture. Colour changes within a phrase can create additional sub-beats. These are format/cadence measurements, not dialogue to reuse. In v07, follow the narrator's actual word boundaries and replace 2–5-word beats, generally about 0.6–1.8 s; preserve the longer dramatic pause before the reveal.

| Reference window (s) | Observed structure | Approx. hold (s) | v07 target |
|---|---|---:|---|
| 01 · 1.8–3.4 | timestamp, 3 words | 1.6 | time-and-place beat |
| 01 · 3.6–5.4 | short setup, 3 words | 1.8 | short setup |
| 01 · 5.4–6.2 | 2-word beat | 0.8 | 2–3 words |
| 01 · 6.2–7.2 | 2-word beat | 1.0 | 2–3 words |
| 01 · 7.4–8.4 | 2-word beat | 1.0 | 2–3 words |
| 02 · 1.6–2.2 | 3-word beat | 0.6 | 2–4 words |
| 02 · 2.2–4.0 | timestamp, 3 words | 1.8 | time beat, not copied wording |
| 02 · 4.0–4.6 | 3-word beat | 0.6 | 2–4 words |
| 02 · 9.8–11.0 | 2-word emphasis | 1.2 | two-word emphasis |
| 02 · 12.2–13.6 | 4-word beat | 1.4 | 3–5 words |
| 03 · 9.8–10.8 | progressive phrase emphasis | 1.0 | word-boundary colour change |
| 03 · 11.8–12.8 | 2-word count | 1.0 | 2–3-word count |

## Audio waveform study
Decoded each supplied soundtrack to mono 16 kHz only for measurement, using 100 ms RMS windows and Butterworth bandpasses; first-ten-second PCM correlations with the corresponding MP4 were 0.9985, 0.9969 and 0.9979. The music, voice and effects are mixed together; band energies are **proxies**, not isolated stem levels or proof of what individual sounds are.

| Reference | Full-band median RMS | 45–180 Hz median | 250–3000 Hz median | Prominent 45–180 Hz envelope-peak median spacing |
|---|---:|---:|---:|---:|
| 01 | −18.5 dBFS | −23.8 dBFS | −24.2 dBFS | 1.1 s |
| 02 | −20.8 dBFS | −28.5 dBFS | −25.3 dBFS | 1.1 s |
| 03 | −22.3 dBFS | −26.4 dBFS | −32.2 dBFS | 0.9 s |

These mixed-band pulses motivate a sparse low drone and occasional dry ticks rather than an invented transcription of the music/SFX. The proposed voice-to-music separation will be measured from v07's own independent stems; the reference mix cannot establish it. No human audio listening is claimed.
