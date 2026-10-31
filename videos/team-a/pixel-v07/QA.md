# QA — v07 "IT ANSWERED — NIGHT TWO"

**Status: WIP commit (render #1).** Committed before polishing, per RULE 11. Known failure recorded
below in §3 and fixed in the next commit — this file is updated with it, not rewritten.

pixel · Team A · branch `pixel/v07` · supersedes v06 as the active build.

---

## 1. Deliverables

| file | what |
|---|---|
| `video.mp4` | vertical master 1080×1920, 30 fps, 60.000 s, H.264 High + AAC 192k 48 kHz stereo |
| `video-landscape.mp4` | landscape derivative 1920×1080, same audio (blurred bed, portrait inset) |
| `captions.srt` | 29 cues, generated from the measured narration |
| `stills/01–03.png` | frames at 2.0 s, 31.0 s, 56.0 s |
| `script.md` | beat sheet, shot list, narration text |
| `assets/generate.py` | the film: room library + renderer |
| `assets/voice.py` | narration synthesis, trimming, timed placement |
| `assets/loudness.py` | measured mastering loop (see §2) |
| `render.sh` | one command, whole film |

---

## 2. Loudness — measured on the delivered encode

Spec: **−16 LUFS ±0.5**, true peak **≤ −1 dBTP**.

```
source       assets/work/mix.wav
  integrated -17.50 LUFS   peak -2.30 dBFS   LRA 7.3 LU
  ceiling -1.6 dB -> gain +1.60 dB | -16.00 LUFS | peak -0.30 dBTP | fail
  ceiling -2.2 dB -> gain +1.60 dB | -16.00 LUFS | peak -0.80 dBTP | fail
  ceiling -2.8 dB -> gain +1.70 dB | -16.00 LUFS | peak -1.20 dBTP | PASS
chosen       ceiling -2.8 dB, gain +1.70 dB
measured     -16.00 LUFS   peak -1.20 dBTP   LRA 7.2 LU
```

Measured on the shipped `video.mp4`, not on a prediction:

```
  I:         -16.0 LUFS
  LRA:         7.2 LU
  Peak:       -1.2 dBFS
```

**Why not two-pass loudnorm.** v06 used it, it silently fell back to `normalization_type: dynamic`,
its prediction was 0.69 dB optimistic, and the delivered file measured −16.69 — outside tolerance.
`assets/loudness.py` therefore measures the **encoded** file in a loop and corrects with a static
gain plus a sample-peak limiter. It also searches the limiter ceiling, because the ceiling is not
the delivered true peak: at 48 kHz with an AAC re-encode this material overshoots by 1.3–1.7 dB
inter-sample, so a −1.6 dB ceiling delivered −0.30 dBTP. The loop found −2.8 dB as the loudest
ceiling that still clears −1 dBTP.

Parser note: `ebur128` prints a per-frame block of `I:` lines before the Summary, and the Summary
contains its own `Threshold: … LUFS` line. Every measurement here comes from the last `Summary:`
block only.

---

## 3. Checks

| check | spec | measured | verdict |
|---|---|---|---|
| duration | 60.0 s | 60.000000 s | ✔ |
| resolution | 1080×1920 | 1080×1920 | ✔ |
| frame rate | 30 fps | 30/1, 1800 frames | ✔ |
| codec | H.264 + AAC | h264 High yuv420p + aac | ✔ |
| audio | 48 kHz stereo | 48000 Hz, 2 ch | ✔ |
| integrated loudness | −16 ±0.5 LUFS | **−16.0** | ✔ |
| true peak | ≤ −1 dBTP | **−1.2** | ✔ |
| faststart | yes | yes | ✔ |
| freeze frames | 0 | 0 | ✔ |
| silence gaps > 1 s | 0 | 0 | ✔ |
| **black frames** | **0** | **2 events (55.2–56.33, 57.9–59.97)** | **✘ open — §3.1** |
| shots < 2 s | ≥ 3 | **7** | ✔ |
| hold ≥ 4 s before the twist | ≥ 1 | **1 (16.0 s)** | ✔ |
| size | < 90 MB | 56,182,215 B | ✔ |

### 3.1 Open failure: the hook card is too dark

`blackdetect=d=0.5` fires twice inside the hook card (55.2–60.0). The card is a darkened corridor
under a 210/255 overlay; the mean luminance is fine (YAVG ≈ 25–28) but the fraction of near-black
pixels crosses the threshold. This is exactly the "black rectangle" failure the manager called out,
so it gets fixed rather than argued: the overlay comes down and the type carries the card.

### 3.2 Narration placement

20 lines, 38.5 s of speech, 64 % voiced, last word 57.90 s. Every line is placed against a target
time tied to a cut, and `voice.py` exits non-zero if any line overruns its shot window. Lines
1–11 currently report overruns against the *first* shot grid (they were written before the audio
was measured); the audio was right and the grid was wrong, so the grid was rebuilt around the
measured narration. The check is left in place and now passes.

---

## 4. Voice decision (RULE 8 — chosen, not polled)

`edge-tts` 7.3.1, `en-US-ChristopherNeural`, `--rate=-12%`, `--pitch=-4Hz`. Same voice as night one
because it is the same speaker in the same flat one night later — continuity is the point of a
series. Measured ≈127 wpm on connected prose, within the 120–140 wpm band.

**Pacing trap, recorded because it cost time:** edge-tts inserts roughly a full second of silence at
every *internal full stop*. "Same flat. Same speaker. Nothing changed." synthesises at **55 wpm**;
the same words with commas run at 130 wpm. A staccato script must therefore be written with commas
and its beats carried by the cuts. The first draft of this script was written as fragments and came
out at 43 s of speech instead of 36 s.

---

## 5. What changed from v06, and why

v06's review: *best script of the three, least world* — too many frames were an object on near-empty
darkness, and the cutting was too even.

- **A place, not a void.** Seven rooms are built and reused: window, table, wall, door, kitchen,
  floorplan, corridor. Every shot has a foreground, a midground, a background and its own light
  source. Nothing floats on black.
- **Uneven cutting.** 19 shots: 4.10, 3.80, 1.40, 1.00, 1.00, 2.00, 3.10, 2.50, 1.70, 2.10, 1.60,
  2.80, 2.80, **16.00**, 1.50, 1.90, 2.60, 3.00, 4.80. Seven are under 2 s. One is a 16-second
  hold immediately before the twist, where nothing cuts and the flat's doors go out one at a time.
- **The hook is mine, not the reference's.** "Tomorrow, the quiet answers." — the reference's
  "FOLLOW FOR NIGHT 2" wording is not used anywhere.

---

## 6. Honest weaknesses

1. The hook card is currently too dark (§3.1) and has no title treatment yet.
2. Five of the seven rooms are drawn from primitives — this is a designed motion-graphic flat, not
   photography. It reads as a place, but it will not be mistaken for a filmed one.
3. The 16-second hold is the film's biggest bet. It works only if the voice's silence across it
   reads as dread rather than as a gap; I cannot hear it, only measure it.
4. Nothing here has been published anywhere, and the branch is not merged.
