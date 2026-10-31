# Waiting has a curve

A 60-second, text-led explainer about why queueing delays rise as a variable system approaches capacity. Open `video.mp4`; captions are burned in, and `captions.srt` is also provided. The score is original synthesized music, with no spoken narration.

- `script.md` — shot timings, exact copy, and model assumptions, written before rendering.
- `assets/` — generated visual/audio source code, fonts, and licence notices.
- `stills/01.png` through `03.png` — frames extracted from the delivered video.
- `QA.md` — measured media properties, actual test output, reproduction evidence, and playback-review limitations.

## Verify or rebuild

Prerequisites: Python 3 with Pillow and NumPy (`python3 -m pip install -r requirements.txt`) and FFmpeg/ffprobe with libx264 and AAC support. The render requires no network access or external media after prerequisites are installed.

```sh
./verify.sh
OUTPUT=/tmp/reel-v02-rebuilt.mp4 ./render.sh
sha256sum video.mp4 /tmp/reel-v02-rebuilt.mp4
```

The clean-clone test in `QA.md` reproduced the MP4 bit-for-bit with the documented versions. Different library/encoder versions can change output bytes. Review the whole video on a screen and speakers: the production sandbox had neither.
