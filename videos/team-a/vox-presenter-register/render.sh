#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
P=characters/presenter
python3 "$P/build_cues.py" \
  --text "$P/proof/script.txt" \
  --alignment "$P/proof/alignment-raw.json" \
  --config "$P/proof/scene_config.json" \
  --out "$P/proof/cues.json"
blender --background --python "$P/build_rig.py" -- \
  --cues "$P/proof/cues.json" \
  --audio "$P/proof/voice.mp3" \
  --out "$P/presenter_rig.blend" \
  --preview "$P/rig-preview.png"
python3 "$P/proof/render_proof.py" \
  --cues "$P/proof/cues.json" \
  --audio "$P/proof/voice.mp3" \
  --out "$P/proof/video-silent.mp4" \
  --preview-dir "$P/proof/stills"
python3 "$P/proof/assemble.py"
mkdir -p videos/team-a/vox-presenter-register/stills
cp "$P/proof/stills/frame_0000_00.00s.jpg" videos/team-a/vox-presenter-register/stills/01-opening.jpg
cp "$P/proof/stills/frame_0495_16.50s.jpg" videos/team-a/vox-presenter-register/stills/02-schematic-insert.jpg
cp "$P/proof/stills/frame_0645_21.50s.jpg" videos/team-a/vox-presenter-register/stills/03-punchline.jpg
