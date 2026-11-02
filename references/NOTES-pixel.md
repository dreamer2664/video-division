# NOTES-pixel — frame-by-frame study of the three references

Study method: the Release `references-v1` zips (`frames-01/02/03.zip`) were downloaded and unzipped
into `/tmp`, never committed back; I stepped through them as ordered frame sequences and rebuilt
contact strips at 0.27 s / 0.5 s intervals, then re-extracted frames from the `.mp4` files
themselves to cross-check. Audio was analysed numerically (EBU R128, per-band FFT, RMS envelope),
not by ear. Nothing here is a guess about the story: it is what the pixels and samples contain.

## 0. Correction to the repo's own labelling (found while studying — please read)

The filenames and the story descriptions in `references/README.md` do not match their contents:

| file | README says | the frames actually contain | actual properties |
|---|---|---|---|
| `01-inkwell-dilemmas-3am.mp4` | "3:07 AM every phone in town screams — phone-alert horror, counted people" | **"I'm you, from tomorrow night"** — a phone in a dark room, DMs from yourself, a selfie of you asleep, a rules sequence, "GET IN THE BATHTUB", clock 3:07→3:09 | 576×1024, 30 fps, 83.52 s |
| `02-reference.mp4` | "same genre, mystery escalation" | **"COUNT YOUR FAMILY"** — 2:22 AM, an emergency alert counts the family, "three", "right next to him", "behind you" | 576×1024, 30 fps, 60.01 s |
| `03-phone-or-door.mp4` | '"Don't turn on the light / I'm you, from tomorrow night" — rules, twist, sequel hook' | **the 3:07 AM phone-alert story**: a red house in the rain, every phone in town, "four people in your home", a framing photo counted 1-2-3, "Mom is snoring through the wall", a figure in the doorway, "do not let them know you counted" | **576×1024**, 30 fps, 46.97 s |

So the README's story descriptions sit one position off (the story it attributes to `01` is in `03`),
and `03` is 576×1024 rather than the 1080×1920 the README claims. Only one of the three is
1080×1920 in the table and none of them are: all three deliverables are 576×1024. This does not
change the brief — `doc/STYLE-BREAKDOWN.md` is the actual style authority and I am matching it —
but anyone auditing from the README will think a file is missing. I did **not** edit `references/`;
that is Manager B's area, and I flag it rather than silently "fixing" someone else's index.

## 1. Ten lines of what I actually saw, frame by frame

1. **Cold open is a place, not a title.** Ref 03 opens on a red-lit house in rain with no text for
   ~2.5 s; ref 02 opens on a doorway with an amber crack of light and "IMAGINE YOUR DAD" already
   on screen by 0.8 s. Both establish *room before sentence*.
2. **The time stamp lands under 3 s and is red-digit LED**, top-left-ish, with a date under it
   ("3:07 AM", "Friday, October 16"). It never leaves the frame in ref 01's phone shots; it is the
   spine of the piece.
3. **Cuts are hard, and short**: measured caption-band changes cluster at a **median 2.8 s** in
   ref 01, range 0.3–14.3 s. Nothing dissolves; the push-in resets on the cut.
4. **Composition is diagrammatic**: dead-centre object on a dark field (a phone, a bowl, a doorway,
   a framed photo) with a soft radial pool of light behind it and heavy vignette. No perspective,
   no camera move except the slow push.
5. **One moving detail per shot** — a blinking cursor, a notification sliding in, a figure's
   silhouette shifting, a candle flame. The rest of the frame is deliberately still.
6. **Captions are the narration.** They carry 100 % of the plot, arrive in 2–5 word beats, and reuse
   the same slot in the lower third so the eye never has to hunt. Colour does the emotional work:
   green in ref 01, amber in ref 02/03, and **red only when the threat names itself**.
7. **The counted element is the clock.** The time advances 3:07 → 3:09 → 3:31 at the escalation
   beats, and ref 03 counts people 4 → 3 with numbered markers appearing on a photograph. The count
   is the meter of tension, not decoration.
8. **Numbers are shown, then contradicted.** "There are 4 people in your home" is followed by the
   family photo being counted and reaching "That's three." The gap between the stated number and the
   observed number *is* the horror.
9. **The twist is a re-frame, not a new threat.** Nothing new arrives; what arrives is a new reading
   of what was already on screen ("Do not let them know you counted", "I'm you, from tomorrow
   night"). The last 15 % re-labels the first 85 %.
10. **The ending is a question and then a card.** Ref 01 ends on "PHONE OR DOOR?" as a two-option
    vote, then a sequel card "FROM: ME — NIGHT 2". No resolution, no thanks-for-watching, no logo.

## 2. Audio, measured (not heard)

| ref | integrated | LRA | true peak | median RMS | activity | pauses > 1.0 s |
|---|---|---|---|---|---|---|
| audio-01 (83.5 s) | −14.3 LUFS | 3.2 LU | +0.2 dBFS | −18.2 dB | 97 % | 1 × 2.5 s |
| audio-02 (60.0 s) | −15.3 LUFS | 2.1 LU | −0.6 dBFS | −20.7 dB | 94 % | 1 × 1.3 s |
| audio-03 (47.0 s) | −15.7 LUFS | **7.8 LU** | −0.5 dBFS | −22.1 dB | 97 % | none |

- All three are **hot** by our spec (≈ −15 LUFS, peaks at or over 0 dBFS). We ship −16 LUFS and
  ≤ −1 dBTP; that is our standard, and I am not copying their clipping.
- **Sub content carries the tension.** Band analysis (30 Hz–16 kHz, 9 log bands) shows the energy
  slope steeply downward: sub/low bands sit ~20 dB above the 300 Hz–3 kHz speech band during quiet
  passages in refs 01 and 03. The bed is a low drone, not a melody, and it is mixed well under the
  voice — on the quietest 20 % of frames it is still 19–20 dB below the voice mid-band.
- **Very few pauses.** Activity is 94–97 %: this is relentless, wall-to-wall sound, with exactly
  one long pause in each of 01/02 (2.5 s and 1.3 s) and none in 03. Ref 03 has the widest LRA
  (7.8 LU) — it uses dynamics instead of silence for emphasis.
- Onsets per minute land at 11–15, i.e. one new sonic event every 4–5 s, which is why sparse sub
  hits work: the ear has nothing else to track.

## 3. Beat timings I will match

Measured caption-band change events (ref 01, lower-third band, frame differencing), medians pooled:

| reference beat | at | what it is doing | my beat (v06) | at |
|---|---|---|---|---|
| place + red clock | 0.0–3.3 s | establish room and time, no premise yet | red clock 2:14, dark flat, one speaker | 0.0–3.2 |
| first sentence | 3.3 s | name the anomaly in one line | "One smart speaker. One flat." | 3.2 |
| escalation A | 8.2 s | something arrives that shouldn't | it says my name | 8.0 |
| escalation B | 12.2 s | rule stated in second person | the rule: don't answer it | 12.4 |
| counted element | 15.0–20.0 s | number shown, then contradicted | one dot = one speaker; count = 1 | 16–24 |
| escalation C | 23–31 s | wrong detail accumulates | it answers what I only thought | 26–34 |
| turn | ~34–40 s | re-frame: the trusted thing is the threat | it was never listening through the mic | 38–44 |
| last line | 51–58 s | the line that lands | "It learned my name from the only other voice." | 49–53 |
| hook card | 58.4–62.4 s | sequel card, hard cut | NIGHT 2 card | 56.5–60.0 |

Target beat spacing for v06: **2.4–3.0 s median**, 20 caption beats across 60 s, never more than
4.2 s without a beat change, and the four colour events (amber→white→red→white) keyed to the
escalation points above.

## 4. What I will not do

I am not reproducing the phone-alert body-count, the "four people in your home" contradiction, the
"don't turn on the light" rule, the messages-from-tomorrow, or the PHONE/DOOR vote. My counted
element is **one**, and its smallness is the joke: a flat with a single speaker in it, counted
out loud like a security ritual. See `QA.md` §"How this differs from the references".
