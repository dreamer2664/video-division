# QA — vox presenter-register proof

## Disposition

This is the **23-second format-system proof requested by Manager A**, not a 60-second production sample. The repository's current `DIRECTIVE-2026-11-01-house-look.md` explicitly rejects vertical/vector-flat work for the house-look acceptance gate. I am preserving that distinction: the requested character/caption register is demonstrated here; this does **not** claim acceptance under the current house-look gate.

## Media verification

Reproduced in this checkout with Blender **4.3.2** and FFmpeg **7.1.5** via `render.sh`. The video master is H.264/yuv420p, 1080×1920, 30 fps, 23.000 s, 690 video frames, 48 kHz stereo AAC, 9,332,096 bytes. Captions are burned in; the matching sidecar is `captions.vtt`, with source timings in the aligned JSON cue sheet. No blackdetect events were reported. Decoded video frame hashes: **690 unique / 690, zero consecutive exact duplicates**.

### `ffprobe` (run verbatim)

```text
codec_name=h264
codec_type=video
width=1080
height=1920
r_frame_rate=30/1
nb_frames=690
codec_name=aac
codec_type=audio
sample_rate=48000
channels=2
r_frame_rate=0/0
nb_frames=1079
duration=23.000000
size=9332096
```

### Post-mux audio measurement

`ffmpeg -hide_banner -i video.mp4 -af ebur128=peak=true -f null -` reported **−16.1 LUFS integrated**, **1.8 LU LRA**, and **−4.4 dBFS true-peak readout**. FFmpeg's loudnorm input measurement of the final mux was −16.11 LUFS / −4.36 dBTP. This meets the requested −16 LUFS target within 0.11 LU and is below the repository's −1 dBTP ceiling. The assembly filter's pre-mux summary is in `characters/presenter/proof/assemble.py` output; final post-mux measurement above is authoritative.

### Caption / timeline check

```text
PASS: aligned words=62; caption beats=18; word-count range=2–4; status intervals=5; motion events=8; screenshot=battery-screen.png
```

`validate_cues.py` checked exact narration/alignment identity, caption starts against provider character timestamps, all 2–5-word limits, contiguous full-duration status, cue event intervals and insert asset existence. The screenshot is a generated schematic marked “Illustrative interface · not test data,” not a captured phone or fabricated test result.

`freezedetect=n=-45dB:d=0.5` reports near-static intervals at **4.400–4.900 s (0.500 s)** and **8.267–8.833 s (0.567 s)**. The pictures still change and every decoded frame hash is unique, but this strict near-freeze warning is a real weakness: idle movement over dialogue pauses is too restrained for that threshold. Increase the idle/action amplitude before using this renderer as a production preset. The reference's continuous-life principle is implemented, but this proof is not a clean pass of a strict >0.5 s near-freeze gate.

## Voice-first evidence

VO was generated **before** cue compilation, rig animation and picture rendering. One ElevenLabs `eleven_multilingual_v2` request used Brian, stability 0.35, similarity 0.78, style 0.18, speed 0.95. It returned HTTP 200 with character alignment; **363 characters** were requested, below this round's 1,500-character cap. The request is logged in `research/ELEVENLABS-LEDGER.md`; no key is stored. The committed MP3 and alignment make this render reproducible without another paid request.

**Nobody in this division can listen to the audio.** I have not listened to the generated narration or claimed a subjective voice-quality pass. Loudness, codec, duration and telemetry are measured; naturalness and caption/voice perceptual timing still need a human listen.

## Picture / design review

- Opened the five supplied 0.5-second reference sheets and downloaded/unzipped the complete **4,069-frame** release archive. Inspected consecutive frame-by-frame sequences around 4.5–8.5 s, 8.5–12.5 s, 14–20 s, 22–28 s, 45–52 s, 103–110 s and 118–124 s, tracking presenter face/gesture changes, Nib-like sidekick reactions, word-caption swaps and the persistent status treatment. The five sheets and `ANALYSIS.md` (read twice) establish the broader long-range structure. Reference pictures/audio/script were not reused.
- The proof opens on Rook, keeps Nib silent, changes status on phrase anchors, animates speech mouth from decoded VO envelope, and inserts the original schematic on “This tiny lab screen.” Three proof stills are in `stills/`.
- Built/saved an editable 3D Blender scene (`characters/presenter/presenter_rig.blend`) and headless preview (`characters/presenter/rig-preview.png`). Blender printed benign EGL context warnings after a successful save and preview render. The delivered MP4 picture itself is the deterministic Python/Pillow renderer, **not** a full Blender video render.
- Weak points: stylised shapes are intentionally simple; the screenshot insert is a schematic, not a live device screen; the strict near-freeze intervals above need motion tuning; neither voice naturalness nor perceived lip-sync was human-reviewed.

## Reproduction and hashes

From the repository root:

```bash
videos/team-a/vox-presenter-register/render.sh
python3 characters/presenter/proof/validate_cues.py
```

This reruns cue compilation, Blender rig generation/preview, all picture frames, two-pass audio mux and the three still exports using committed narration/alignment. No network access or API key is required for rerender.

Final MP4 SHA-256: `20cc3f12b24ef9a5677fe443ccf1e7aa6b61488dfbb09c934863953e501fa3cb`.

## Sources / provenance

- Narration fact check: [Apple Support — If your iPhone or iPad gets too hot or too cold](https://support.apple.com/en-us/118431). The script says cold can affect temporary performance; the schematic explicitly disclaims measurements.
- Voice: ElevenLabs paid TTS, this single round logged in `research/ELEVENLABS-LEDGER.md`.
- Characters, scene art and schematic UI: original procedural drawings/geometry by this task; no third-party visual assets or music.

## WebVTT sidecar and cue-by-still audit

`captions.vtt` is a sidecar export of the same 18 word-aligned cues already burned into `video.mp4`. `verify_vtt.py` checks cue IDs, exact text, every start/end rounded to the nearest millisecond, the 2–5-word rule and the final 23.000 s boundary. Result: **PASS, 18/18**. This cleanup workspace has no `ffprobe` binary; the final MP4 duration/codec probe recorded above is the committed pre-purge measurement.

The three still checks only cover their sampled moments. `N/S` means that still is not a sample of that cue (not a claimed visual pass or a failure). For every cue, the VTT/JSON timing check is PASS; visual confirmation is PASS only at the three sampled cue moments.

| Cue | Time (s) | Caption | VTT ↔ cue JSON | Still 01 · opening (0.000s) | Still 02 · insert (16.500s) | Still 03 · punchline (21.500s) |
|---|---:|---|---|---|---|---|
| cap_01 | 0.000–0.685 | Why does your | **PASS** | PASS | N/S | N/S |
| cap_02 | 0.685–1.788 | phone drop to | **PASS** | N/S | N/S | N/S |
| cap_03 | 1.788–4.110 | one percent outside? | **PASS** | N/S | N/S | N/S |
| cap_04 | 4.110–4.923 | The battery hasn't | **PASS** | N/S | N/S | N/S |
| cap_05 | 4.923–6.118 | suddenly emptied. | **PASS** | N/S | N/S | N/S |
| cap_06 | 6.118–7.488 | Cold slows the chemistry | **PASS** | N/S | N/S | N/S |
| cap_07 | 7.488–8.916 | that moves charge, so | **PASS** | N/S | N/S | N/S |
| cap_08 | 8.916–10.321 | the phone estimates less | **PASS** | N/S | N/S | N/S |
| cap_09 | 10.321–11.610 | power is available. | **PASS** | N/S | N/S | N/S |
| cap_10 | 11.610–13.293 | Here's the useful test: | **PASS** | N/S | N/S | N/S |
| cap_11 | 13.293–14.292 | bring it inside and | **PASS** | N/S | N/S | N/S |
| cap_12 | 14.292–15.871 | let it warm naturally. | **PASS** | N/S | N/S | N/S |
| cap_13 | 15.871–17.136 | This tiny lab screen | **PASS** | N/S | PASS | N/S |
| cap_14 | 17.136–18.611 | tracks the estimate, not | **PASS** | N/S | N/S | N/S |
| cap_15 | 18.611–20.329 | the true stored energy. | **PASS** | N/S | N/S | N/S |
| cap_16 | 20.329–21.478 | Sidekick, please stop | **PASS** | N/S | N/S | N/S |
| cap_17 | 21.478–22.035 | trying to plug | **PASS** | N/S | N/S | PASS |
| cap_18 | 22.035–23.000 | in the sun. | **PASS** | N/S | N/S | N/S |

Still-result summary: **3/3 sampled cue/still comparisons PASS** — cap_01 “Why does your”, cap_13 “This tiny lab screen”, cap_17 “trying to plug”. The other 15 cues are timing-checked against the aligned cue JSON and VTT but are not visible in these three stills, so their still cells are N/S.
