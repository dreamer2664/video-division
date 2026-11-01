# REFERENCE — "How people are making those viral 'What If' videos" (@vibecodingiseasy)

Source: https://vm.tiktok.com/ZGdXNFAE3/ · 1080×1920 · 30 fps · **135.63 s** · **4,069 frames** ·
HEVC + AAC.
Every frame was extracted (240 px wide, `frames/`, attached as a Release asset `frames-tutorial.zip`)
and read in five contact sheets at 0.5 s intervals (`sheet_1..5.jpg`). This document is the analysis.

---

## 1. What the video actually is

A **meta-tutorial**: a cartoon presenter explains, step by step, how to make the viral "What If"
vertical videos — and the video you are watching is made by the method it describes. It is a recipe
being handed over on camera.

**The recipe it teaches (its own four rules, stated in the captions):**
1. **The question comes first** — open with the question, not the setup.
2. **One number that ticks** — a single counter that moves the whole time.
3. **Short captions** — a few words per beat, every few seconds.
4. **Each step is worse than the last** — the escalation must be monotonically bad.

**Its two-step process:**
- **Step 1 — copy the recipe, not the video.** Watch three viral ones and spot what they all do. Do not
  copy a film; copy the structure.
- **Step 2 — pick a "what if" with a number that moves.** Its example: a fall from 1,048 ft versus
  39 ft, a clock running out. Then: *"ask it what really happens, second by second. Use real science
  and write short captions."*

**Why real science matters**, per the video: the comments will check. Real numbers attract arguments,
and arguments are views — it shows view counts rising 493,348 → 1,115,881 → 1,204,331 while people
argue about whether the physics is right. Its own closing joke makes the point: asked "what if I never
cleaned my room again?", the counter climbs 3 → 9 → 29 → 59 → 96 → 141 → 191 → 247 → 308 → 375 → 412
items and the presenter answers *"that's not a what-if, that's a documentary."* The recipe only works
when the number can actually move under real physics.

**The production pipeline it demonstrates:**
- **Voice first, video second.** It says this is the tip most people skip: the presenter hates their own
  voice, so on ElevenLabs they paste each caption, pick a deep voice and download — free plan.
- Then each caption is tuned to its actual voice line.
- Then **Claude Code** ($20/month Pro plan), an empty folder named `what-if-video`, the voice mp3 files
  dropped in, the captions pasted, and a plain-language instruction: *"build this as a 3D video, tall
  like a phone, with a counter and these captions."* It builds a **web page** so you can watch it in the
  app before rendering.
- **The mistake everybody makes:** rendering the whole video at once is slow — 2 %, 13 %, 9 %, ten
  minutes, and then you spot a problem and have to start again. Its fix: render one still per caption
  first, fix those, then export the video file. "Round 1, round 2, and a few fixes. Even this one."

---

## 2. The format as executed (what to copy at the craft level)

**Two characters.**
- **Presenter**: a stylised 3D cartoon male avatar — teal/dark-green sweater, pale skin, dark hair,
  heavy expressive brows, animated mouth and eyes, gesturing hands. Framed chest-up, centred, in the
  lower-middle of the frame. Simple cel-ish shading, soft studio light, no uncanny realism. He carries
  every argument.
- **Sidekick**: a **spiky red blob** with two eyes and stick arms, standing on a red pole/tube. It has
  no voice; it appears to take a label or a reaction, and it is where the *jokes* land. It is cheap to
  draw and it does the comic timing.

**Set**: a rail/tube lattice behind, sunset sky gradient, warm floor — abstract, low-detail, always the
same. Cheap, consistent, never distracting.

**Captions**: white heavy sans, dark outline, centred in the middle band, **2–5 words per beat**,
replaced on the voice. Yellow highlight boxes for the recurring labels — `STEP 1`, `STEP 2`,
`THE RECIPE`, `MISTAKE`, `ROUND 1 / ROUND 2`. A **STATUS** block in the corner shows which step is live
(`STEP 1 · COPY THE RECIPE · QUESTION FIRST`), so a viewer who arrives mid-video is never lost.

**Screenshots**: real UI captures — Claude, Claude Code, ElevenLabs, generated video players, satellite
images — inserted full-bleed or as a phone/desktop frame, always with a caption over or beside them.
They are the *proof*; the characters are the *commentary*.

**Motion**: the presenter is animated continuously (blinks, head turns, hand gestures) even on long
screenshot holds. Cuts every 1–3 s. Numbers tick with a counter overlay. Red X marks appear over wrong
examples; arrows and circles annotate screenshots.

**Sound**: one narrator, mid-register, fast and conversational, no music bed competing — the music is
low and rhythmic under the speech. The red blob's beats get small comic stings.

---

## 3. Why this is useful to us specifically

It answers three things this division has been losing time on:
1. **Voice first, then picture.** We have been doing the opposite, which is why re-timing captions has
   cost us renders. Build the voice, lock the caption beats to it, then render.
2. **Render stills, not videos, while iterating.** One still per caption, fix those, then export. That
   is the fix for our repeated "re-render because of one bad frame" problem.
3. **A structure that survives muted autoplay**: one ticking number and short captions. Our films have
   been atmospheric but slow; this is the opposite trade — legible in two seconds, no sound needed.

---

## 4. What we will and will not take

**Take**: the presenter-plus-sidekick format, the status label, the caption discipline, the
number-that-ticks rule, the voice-first pipeline, the stills-before-video rendering loop.

**Do not take**: the specific "What If" premise (that is somebody else's format), the tutorial's own
script, its avatar design, or its characters. We are borrowing craft, not content. Any film we make in
this register gets its own subject and its own two characters.

**Asset provenance**: the source video is retained for study only. Nothing from its frames, audio or
script is reused in a deliverable.
