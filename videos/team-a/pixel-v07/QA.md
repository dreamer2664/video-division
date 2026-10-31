# QA — v07 "IT ANSWERED — NIGHT TWO"

**Status: delivered.** Render #1 was committed before any polishing (RULE 11, commit `aa93142`),
with its black-frame failure recorded while still open; the fix and the final measurements are below.
The WIP commit is kept in the branch history on purpose — it is the evidence that the render existed
before the polish, not the other way round.

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
| black frames | 0 | **0** | ✔ |
| shots < 2 s | ≥ 3 | **7** | ✔ |
| hold ≥ 4 s before the twist | ≥ 1 | **1 (16.0 s)** | ✔ |
| size | < 90 MB | **56,014,264 B (53.4 MiB)** vertical / 18,724,214 B landscape | ✔ |

### 3.1 Fixed: the hook card was a black rectangle (was open in `aa93142`)

`blackdetect=d=0.5` fired twice inside the hook card (55.2–56.33 s, 57.9–59.97 s) in render #1.
Two causes, both mine:

1. **The vignette was crushing the bottom of frame.** `VIG = clip(1 − 0.62·r^1.8, 0.30, 1.0)` made
   the lower third near-black on every shot, which is why the window shot also ended in a dead band.
   Now `clip(1 − 0.46·r^1.8, 0.55, 1.0)`, and the window shot gained a rug, a sofa arm and floor
   boards so the band has something in it.
2. **The end card was a 210/255 dark overlay with one caption line.** It now keeps the darkened flat
   visible at 132/255 and carries its own title treatment — series mark, title, rule, and the hook.
   The burned caption underneath is suppressed so the line is not printed twice.

Post-fix: **black 0, freeze 0, silence 0**, measured on the shipped encode.

### 3.2 Narration placement

20 lines, **38.5 s of speech, 64 % voiced, last word 57.90 s**. Every line is placed against a
target time tied to a cut, and `voice.py` exits non-zero if any line overruns its shot window.

One honest wrinkle: after the pacing fix, 9 of the 20 lines still reported overruns against the
*first* shot grid — because that grid had been written before the audio existed. The audio was right
and the grid was wrong, so the grid was rebuilt around the measured narration (19 shots, listed in
§5). The guard is left enabled; it now passes with zero overruns, and it is what forced the
16-second hold to be carved out of the timeline rather than guessed at.

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

1. **Five of the seven rooms are drawn from primitives.** This is a designed motion-graphic flat,
   not photography. It reads as a place — foreground, midground, background, its own light source
   per shot — but it will not be mistaken for a filmed room. That is the honest limit of the tool
   I have; a camera would do better and I do not have one.
2. **The 16-second hold is the film's biggest bet.** It works only if the voice's silence across it
   reads as dread rather than as a gap. I can measure that there is no silence gap by the
   silencedetect definition (the drone and rain run underneath it) but I cannot hear whether it
   lands. If it fails, it fails as "slow", not as "broken".
3. **The floorplan shot is the one graphic insert among eight rooms**, and it is the shot most likely
   to read as a diagram rather than a place. It earns its 5.6 s by carrying the count, but it is the
   weakest frame in the film by the standard the manager set.
4. **`loudness.py` searches the limiter ceiling**, which means the master's peak varies with the
   material. On this mix it chose −2.8 dB ceiling → −1.20 dBTP. On a denser mix it could choose
   −3.4 and be 0.9 dB quieter in peak terms for the same integrated loudness. That is a deliberate
   trade for guaranteed compliance over a fixed recipe.
5. Nothing here has been published anywhere. The branch is not merged.

---

## 7. Reference study — what was taken, what was refused

Studied before writing a frame (`references/NOTES-pixel.md`): the three 2 AM films in
`references/`, plus `doc/STYLE-BREAKDOWN.md` and `specs/60s-video.md`.

**Taken:** the cold palette and warm lamp accent; the LED clock in the upper third; short declarative
captions in the lower band; the speaking-in-second-person address; the slow push-in; the reveal line
in red.

**Refused, and named here so it is checkable:** the phone-alert body count; messages from
"tomorrow night you"; "don't turn on the light" rules; "four people in your home"; the specific
"FOLLOW FOR NIGHT 2" wording. v07's hook is **"Tomorrow, the quiet answers."**

**Note on the reference files themselves:** the labelling in `references/` is wrong —
`01-inkwell-dilemmas-3am.mp4` is not the film its filename claims, `02-reference.mp4` is a
"COUNT YOUR FAMILY" story, and none of the three is 1080×1920. Per the standing instruction I did
not edit the index files. It is recorded in `references/NOTES-pixel.md` and flagged here.

## 8. Licence

Typefaces: **Anton** and **Barlow Condensed**, SIL Open Font License 1.1, licences committed beside
the binaries at `assets/fonts/LICENSE-*.txt`. Everything else — picture and sound — is generated by
`assets/generate.py` and `assets/voice.py` from code in this repository. No stock footage, no
samples, no reference audio.

## 9. How to verify this without trusting me

```bash
git clone https://github.com/dreamer2664/video-division && cd video-division
git checkout pixel/v07 && cd videos/team-a/pixel-v07

ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of default=noprint_wrappers=1 video.mp4

# loudness, read from the Summary block only
ffmpeg -v info -i video.mp4 -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p'

ffmpeg -v info -i video.mp4 -vf blackdetect=d=0.5 -an -f null - 2>&1 | grep -c black_start
ffmpeg -v info -i video.mp4 -vf freezedetect=n=-60dB:d=0.5 -an -f null - 2>&1 | grep -c freeze_start
ffmpeg -v info -i video.mp4 -af silencedetect=n=-50dB:d=1.0 -f null - 2>&1 | grep -c silence_start
```

Expected: `60.000000`, 1080×1920, 30/1, 48000/2, `I: -16.0 LUFS`, and `0` from each of the three
detectors. The whole film rebuilds with `./render.sh` (≈8 minutes: 4.5 min frames, 3 min encode)
given FFmpeg 7.0.2 and `edge-tts` 7.3.1.
