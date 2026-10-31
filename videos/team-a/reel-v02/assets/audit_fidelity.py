#!/usr/bin/env python3
"""Optional sampled source/encode audit; not needed by render.sh.

Requires numpy, Pillow, OpenCV and scikit-image. Run from the delivery folder:
  python3 assets/audit_fidelity.py video.mp4
To audit the former version, run it from a checkout of the corresponding commit,
so assets/visuals.py and video.mp4 are the matching source and encoded output.
"""
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np
from skimage.metrics import structural_similarity
import visuals

video = sys.argv[1] if len(sys.argv) > 1 else 'video.mp4'
if not Path(video).is_file():
    raise SystemExit(f'Video does not exist: {video}')
psnr_scores, ssim_scores = [], []
for second in [2, 9, 16, 24, 34, 44, 52, 58]:
    source = np.asarray(visuals.frame_at(second * visuals.FPS))
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(second), '-i', video,
           '-frames:v', '1', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    decoded = np.frombuffer(raw, dtype=np.uint8).reshape(visuals.H, visuals.W, 3)
    psnr = cv2.PSNR(source, decoded)
    source_y = cv2.resize(cv2.cvtColor(source, cv2.COLOR_RGB2GRAY), (960, 540),
                          interpolation=cv2.INTER_AREA)
    decoded_y = cv2.resize(cv2.cvtColor(decoded, cv2.COLOR_RGB2GRAY), (960, 540),
                           interpolation=cv2.INTER_AREA)
    ssim = structural_similarity(source_y, decoded_y, data_range=255)
    print(f'{second:02d}s PSNR RGB={psnr:.2f} dB; luma SSIM half-res={ssim:.5f}')
    psnr_scores.append(psnr)
    ssim_scores.append(ssim)
print(f'Mean across eight sampled frames: PSNR={sum(psnr_scores)/len(psnr_scores):.2f} dB; '
      f'luma SSIM={sum(ssim_scores)/len(ssim_scores):.5f}')
