# v08 render project

`../render.sh` is the full build command. Requirements: FFmpeg with libx264/AAC; Python 3; packages in `requirements.txt`; the DejaVu Sans Condensed fonts at `/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf` and `DejaVuSansCondensed.ttf`. In a clean environment: `python3 -m pip install -r project/requirements.txt`, then `FFMPEG=/path/to/ffmpeg ./render.sh`.

The committed `../assets/narration.wav` is the 60-second, mono 24 kHz, frame-aligned neural narration stem. It makes the default build reproducible offline. `voice.py` can regenerate it from `voice_lines.txt` using Edge TTS; it writes temporary MP3 beat clips only under `/tmp/cut-v08-build/voice-clips`, time-aligns them to `voice_cues.csv`, and never stores intermediates in the repo. Exact voice identity/settings and the measured effective speaking rate are documented in `../QA.md`.

`sound.py` synthesizes an original 48 kHz stereo drone and the two real, narrated nursery sounds. The nonexistent latch sound is deliberately not played. `render.py` draws all 25 vector shots and karaoke captions procedurally, applies an eased 1.00→1.06 push-in, and pipes RGB frames directly into FFmpeg. `render.sh` stores picture and score intermediates in `/tmp/cut-v08-build`, muxes the vertical 1080×1920 master and creates a blurred-letterbox 1920×1080 derivative, then extracts three master stills. No reference video, image, frame, or audio is a production input.

If Edge TTS/network regeneration is unavailable, the committed narration stem remains usable. If it is lost, try the voice order in `QA.md`: edge-tts first, Piper local ONNX second; eSpeak NG only as a clearly disclosed last resort. The TTS stem is not a sample or a voice clone; ChristopherNeural is a designed synthetic narration choice.
