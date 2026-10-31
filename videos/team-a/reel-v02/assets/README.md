# Render assets

- `visuals.py`: original deterministic Pillow motion-graphics renderer by reel. It generates every frame directly; there are no image/footage downloads.
- `score.py`: original deterministic stereo electronic composition by reel, synthesized from mathematical oscillators and seeded noise. No samples, loops, recordings, or external sound libraries are used. The original visuals and composition are dedicated to the public domain under CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/).
- `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`, `DejaVuSansMono.ttf`: bundled, unmodified DejaVu fonts. Their redistribution licence and notices are in `DejaVu-LICENSE.txt`; the font files are not part of the CC0 dedication.

The script needs Python 3 with Pillow and NumPy, plus FFmpeg built with libx264 and the native AAC encoder. Tested versions are in `requirements.txt` and `QA.md`. The render uses no network or assets outside this directory.
