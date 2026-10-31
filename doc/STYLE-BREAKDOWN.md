# STYLE BREAKDOWN — the "phone horror / rule horror" vertical short

Derived from the three references by inspecting their frames individually, not by sampling.

## 1. Frame and composition
- **1080×1920, 9:16, 30 fps.** Composed for a phone held in one hand.
- Safe margins: keep every caption inside the middle 84 % — TikTok's UI eats the top and bottom.
- Composition tools used by all three: (a) centred object on a dark field, (b) **split screen**
  (phone UI on one side, room on the other), (c) top-down or straight-on "elevation" views —
  flat, diagrammatic, no perspective drama.

## 2. Look
- **Flat vector illustration**: simple shapes, soft radial gradients for light, painted glow,
  strong vignette. No photographs, no 3D, no textures.
- Night palette: deep navy `#0B1020` / `#0E1526`; window and lamp amber `#F5C542`; phone-screen
  green `#7CF29C`; alarm red `#E2453C`; text white and amber. Luminance stays low — nothing is
  full white except the captions.
- Barely any grain. The images are clean, high-contrast and cheap to draw — which is exactly
  why code works so well for this format.

## 3. Motion
- **Slow push-in** on stills: 1.00 → 1.06 over 3–6 s, eased. Occasionally a slow lateral drift.
- **Cut every 1.5–3 s.** No wipes or dissolves: hard cuts, sometimes a match-cut on a shape.
- Small life details: a light flickers, a notification slides in, a cursor blinks, a shadow
  moves. **One moving element per shot is enough.**
- The text is the main animation: captions arrive in **2–5 word beats**, replaced on the beat of
  the narration. Emphatic words change colour (amber → red for the threat).

## 4. Captions (the signature)
- Heavy, condensed sans-serif, **ALL CAPS or Title Case**, 60–110 px at 1080p wide.
- Colour: amber `#F5D14E` by default, white for narration, **red for the threat line**.
- Lower third (or centred over the object), with a soft dark shadow/outline so it survives any
  background.
- They carry the story: assume the viewer watches muted. A deaf viewer must be able to follow
  the plot from the captions alone.

## 5. Story grammar (the actual formula)
1. **Time and place stamp** in the first 3 s ("At 3:07 AM", "3:31 AM").
2. **A rule or constraint** stated early, second person ("Don't turn on the light", "Stay in your
   room", "Do not count out loud").
3. **Escalation** in short increments: an alert, a message, a sound, a wrong detail.
4. **A counted or numbered element** to create tension (four people in your home → three → three).
5. **Betrayal of expectation** at ~70–80 %: the thing you trusted — the phone, the parent, your
   own voice — is the threat.
6. **A choice or a last line** that lands hard ("So who do you trust: the phone, or the door?").
7. **Sequel hook**: "FROM: ME — NIGHT 2".

## 6. Audio
- **Deep male narrator**, slow, ≈120–140 wpm, low register, close-mic, almost whispered.
  Long pause before the twist line. Never cheerful, never "announcer".
- **Music**: ominous drone (low sine/saw + slow filter sweep), sparse sub-bass hits on story
  beats, a clock tick or heartbeat pulse. Mixed **8–12 dB under** the voice.
- **SFX**: phone buzz, notification, message send, floor creak, footstep, muffled breathing,
  distant thunder. Short, dry, close.
- Loudness −16 LUFS integrated, true peak ≤ −1 dBTP.

## 7. What makes the format look cheap (avoid)
PowerPoint transitions · stock footage · AI images with warped hands · a cheerful narrator ·
captions that lag the voice · music louder than the voice · more than two typefaces ·
flashing white frames · text touching the screen edge · a "thanks for watching" ending.

## 8. Replication recipe that works on a 2 GB sandbox
Python (Pillow / cairo / numpy) draws frames at 1080×1920 → pipe raw frames into FFmpeg →
narration from a TTS engine → music and SFX synthesised with numpy (or FFmpeg `sine` /
`anoisesrc`) → mix with `amix` + `loudnorm`. Deterministic, re-runnable, no editor required.
This format is illustration + typography + timing, and all three are code.

## 9. Speech: choosing a voice engine (decide yourself, do not ask)
Quality order that has been verified to work in this sandbox class:
1. `edge-tts` (pip, network) — neural voices; e.g. `en-US-GuyNeural`, `en-US-ChristopherNeural`,
   `en-GB-RyanNeural`. Best quality per byte. Slow the rate with `--rate=-12%`, drop pitch
   with `--pitch=-4Hz`.
2. `piper` (local ONNX, ~60 MB model) — good, offline, deterministic. Use if `edge-tts` fails.
3. `espeak-ng` — robotic. **Only** as an absolute last resort, and say so in `QA.md`.

Pick ONE voice for the whole piece, keep it across the series, and record the choice and your
reason in `QA.md` under a `## Voice decision` heading. **Never ask a human which voice is
better** — nobody is going to answer, and the job stalls.
