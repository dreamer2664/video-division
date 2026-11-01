# Rook + Nib — presenter rig and motion register

## Character decisions

**Rook** is an original chest-up explainer: broad apricot face, close-cut plum hair with a brass barrette, asymmetrical heavy brows, freckles, a jade work jacket and persimmon scarf. The nose/cheek planes, clipped hair silhouette, palette and warm-to-cool lab set are new design choices; no reference frame, audio, script or model was reused. His eyebrows, mouth and eyes are deliberately oversized for phone viewing. He has an authored idle loop (breath/bob, micro-turn, staggered blink), audio-envelope-driven jaw, and cue-triggered nod, open-palm, point and shrug.

**Nib** is a silent sidekick: a mint battery-bug with a dark LED face, amber pixel eyes, two contact feet and a curling orange charging lead. It is not a red/spiky blob and has no dialogue or mouth. Its squash/bob, shiver, peek, squint and recoil make the reaction beats; current label chips are timed to its reactions.

## Blender rig conventions

`presenter_rig.blend` is built by `build_rig.py` using Blender 4.3+ and saved with the named controls below. The proof renderer's Rook/Nib silhouettes are drawn with the same design system; the `.blend` remains the editable 3D character source.

- **Rook:** `root → torso → neck → head → jaw`; left/right chains are `arm.L → forearm.L → hand.L` and `arm.R → forearm.R → hand.R`.
- **Nib:** `root → shell → tail`, plus `feet.L` and `feet.R`.
- Mesh islands are weighted to these control bones. Treat the names and axes as the public rig contract; add controls rather than renaming existing ones.
- Scene rate and frame range come from `proof/cues.json`. `build_rig.py` keys the audio-following jaw from the committed VO envelope, reusable idle/blink life, and action keys from the same motion cue records used by the proof renderer.
- Blender scene renderer is Workbench with flat material bands for a quick, portable cel-ish preview. `rig-preview.png` is a headless first-frame check, not a claim that the proof MP4 was rendered in Blender.

## Voice-first / data-first pipeline

1. Write `proof/script.txt` and synthesize the narration **before** making animation. The actual ElevenLabs clip and character-alignment response are retained as `proof/voice.mp3` and `proof/alignment-raw.json`; no secret is needed for a rerender.
2. `build_cues.py` verifies exact text identity against the provider's aligned characters, derives word start/end times, then partitions sentences into 2–5 word beats. `proof/cues.json` also contains status states, label chips, screenshot interval and motion events; each is anchored to a phrase in the recorded voice rather than a guessed duration.
3. `build_rig.py` and `proof/render_proof.py` both read that cue sheet. The latter uses FFmpeg-decoded VO amplitude for the 2D proof's mouth-open envelope; no sound is synthesized by the picture renderer.
4. `proof/assemble.py` two-pass normalizes the mux to −16 LUFS and −1.5 dBTP, 48 kHz AAC. The screen insert is a generated schematic, visibly marked illustrative—not a measurement or a real phone capture.

From the repo root, reproduce with `videos/team-a/vox-presenter-register/render.sh`. Runtime dependencies: Blender 4.3+, FFmpeg/ffprobe (libx264), Python 3, Pillow, NumPy. Rendering uses committed narration/alignment and does not call external services. To revoice, request fresh alignment for the new exact script first, then rebuild cues and animate; never keep these timings after changing the words.

## Scope and gate note

Manager A's assignment explicitly asked for a 1080×1920, 20–30 s presenter-led register proof. That is what this branch demonstrates (23 s). The checked-in `DIRECTIVE-2026-11-01-house-look.md` separately rejects portrait/vector samples for the current 60 s house-look acceptance gate. This asset is therefore a requested format-system proof, **not** a claim of acceptance under that gate. The reference was studied as requested but is not a source asset or creative template here.
