#!/usr/bin/env python3
"""
House Look Optical Motion, 500T Halation Bloom & Parallax Storm Compositor (`look/house_motion.py`).

Memory-lean (< 240 MB RAM) streaming shot renderer for 1920x1080 @ 30 fps CFR:
  - Trilinear 33x33x33 .cube 3D LUT evaluation
  - Photochemical 500T red-amber halation bloom (dual-sigma emulsion back-scatter on bright practicals)
  - Sub-pixel continuous camera moves (BICUBIC Image.Transform.EXTENT -> zero integer-pixel judder, zero freezedetect)
  - Multi-plane parallax rain (far wash + near fast streaks + vertical oculus/window-masked rain) + drifting storm mist
  - Temporal film grain via ffmpeg `noise=alls=4:allf=t+u`
"""

import math
import subprocess
from typing import Callable, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W_DEFAULT = 1920
H_DEFAULT = 1080
FPS_DEFAULT = 30


def load_cube_lut(path: str) -> np.ndarray:
    """Load an Adobe/Resolve .cube 3D LUT into an (N, N, N, 3) float32 lookup tensor indexed [R, G, B]."""
    rows = []
    size = 33
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("TITLE") or s.startswith("DOMAIN"):
                continue
            if s.startswith("LUT_3D_SIZE"):
                size = int(s.split()[1])
                continue
            parts = s.split()
            if len(parts) == 3:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
    arr = np.array(rows, dtype=np.float32).reshape((size, size, size, 3))
    return np.transpose(arr, (2, 1, 0, 3)).copy()


def apply_lut_trilinear(img01: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Evaluate a 3D LUT via exact trilinear interpolation on an [H, W, 3] float32 image in [0, 1]."""
    n = lut.shape[0] - 1
    scaled = np.clip(img01, 0.0, 1.0) * np.float32(n)
    idx0 = np.clip(np.floor(scaled).astype(np.int32), 0, n - 1)
    idx1 = idx0 + 1
    fr = (scaled - idx0).astype(np.float32)

    r0, g0, b0 = idx0[:, :, 0], idx0[:, :, 1], idx0[:, :, 2]
    r1, g1, b1 = idx1[:, :, 0], idx1[:, :, 1], idx1[:, :, 2]
    dr, dg, db = fr[:, :, 0:1], fr[:, :, 1:2], fr[:, :, 2:3]

    c00 = lut[r0, g0, b0] * (1.0 - dr) + lut[r1, g0, b0] * dr
    c01 = lut[r0, g0, b1] * (1.0 - dr) + lut[r1, g0, b1] * dr
    c10 = lut[r0, g1, b0] * (1.0 - dr) + lut[r1, g1, b0] * dr
    c11 = lut[r0, g1, b1] * (1.0 - dr) + lut[r1, g1, b1] * dr

    c0 = c00 * (1.0 - dg) + c10 * dg
    c1 = c01 * (1.0 - dg) + c11 * dg
    return np.clip(c0 * (1.0 - db) + c1 * db, 0.0, 1.0).astype(np.float32)


def apply_halation_bloom(
    img01: np.ndarray,
    threshold: float = 0.72,
    strength: float = 0.22,
    tint_rgb: tuple[float, float, float] = (1.00, 0.38, 0.08),
) -> np.ndarray:
    """
    Simulate 35mm tungsten negative halation (red-orange back-scatter off the film base around bright
    practical lamps and specular highlights). Runs once per plate before per-frame camera motion so RAM
    and CPU stay minimal.
    """
    luma = 0.2126 * img01[:, :, 0] + 0.7152 * img01[:, :, 1] + 0.0722 * img01[:, :, 2]
    hi = np.clip((luma - threshold) / max(1.0 - threshold, 1e-4), 0.0, 1.0) ** 1.35
    hi_u8 = Image.fromarray((hi * 255.0 + 0.5).astype(np.uint8))

    tight = np.array(hi_u8.filter(ImageFilter.GaussianBlur(radius=6.5)), dtype=np.float32) / 255.0
    wide = np.array(hi_u8.filter(ImageFilter.GaussianBlur(radius=24.0)), dtype=np.float32) / 255.0
    scatter = (0.62 * tight + 0.38 * wide) * np.float32(strength)

    tint = np.array(tint_rgb, dtype=np.float32)[None, None, :]
    bloom = np.clip(scatter[:, :, None] * tint, 0.0, 0.65)
    # Screen blend preserves highlight roll-off without hard clipping
    return np.clip(1.0 - (1.0 - img01) * (1.0 - bloom), 0.0, 1.0).astype(np.float32)


def build_rain_tile(
    seed: int = 801,
    density: float = 0.00055,
    length: int = 48,
    angle_deg: float = 13.0,
    blur_r: float = 0.75,
    tw: int = 2240,
    th: int = 1360,
) -> np.ndarray:
    """Build a seamless wraparound float32 rain-streak tile for zero-seam parallax scrolling."""
    rng = np.random.default_rng(seed)
    canvas = Image.new("L", (tw, th), 0)
    draw = ImageDraw.Draw(canvas)
    rad = math.radians(angle_deg)
    dx = math.sin(rad) * length
    dy = math.cos(rad) * length
    for _ in range(int(tw * th * density)):
        x0 = rng.uniform(-80, tw + 80)
        y0 = rng.uniform(-80, th + 80)
        bright = int(rng.uniform(95, 245))
        width = 1 if rng.random() < 0.78 else 2
        for ox in (-tw, 0, tw):
            for oy in (-th, 0, th):
                sx, sy = x0 + ox, y0 + oy
                if -length <= sx <= tw + length and -length <= sy <= th + length:
                    draw.line([(sx, sy), (sx + dx, sy + dy)], fill=bright, width=width)
    if blur_r > 0:
        canvas = canvas.filter(ImageFilter.GaussianBlur(blur_r))
    return np.array(canvas, dtype=np.float32) / 255.0


def build_mist_tile(seed: int = 905, tw: int = 2240, th: int = 1360) -> np.ndarray:
    """Build a soft, low-frequency wind-blown storm spray/mist veil for atmospheric depth."""
    rng = np.random.default_rng(seed)
    coarse = rng.uniform(0.0, 1.0, (th // 32, tw // 32)).astype(np.float32)
    pil_m = Image.fromarray((coarse * 255.0).astype(np.uint8)).resize((tw, th), Image.Resampling.BICUBIC)
    pil_m = pil_m.filter(ImageFilter.GaussianBlur(radius=36.0))
    arr = np.array(pil_m, dtype=np.float32) / 255.0
    arr = np.clip((arr - 0.42) * 1.9, 0.0, 1.0)
    return arr


def render_moving_shot_clip(
    plate_rgb01: np.ndarray,
    lut: np.ndarray,
    out_clip_mp4: str,
    n_frames: int,
    start_frame_global: int = 0,
    fps: int = FPS_DEFAULT,
    zoom_start: float = 1.000,
    zoom_end: float = 1.074,
    pan_x_start: float = 0.000,
    pan_x_end: float = 0.006,
    pan_y_start: float = 0.006,
    pan_y_end: float = -0.006,
    halation_strength: float = 0.22,
    rain_amount: float = 0.24,
    mist_amount: float = 0.08,
    rain_far: Optional[np.ndarray] = None,
    rain_near: Optional[np.ndarray] = None,
    mist_tile: Optional[np.ndarray] = None,
    rain_mask: Optional[np.ndarray] = None,
    frame_hook: Optional[Callable[[np.ndarray, int, float], np.ndarray]] = None,
    crf: int = 20,
) -> None:
    """
    Grade a 1920x1080 plate through `lut` + 500T halation, animate continuous sub-pixel camera motion +
    3-layer storm weather, run optional `frame_hook(frame, global_frame_idx, time_sec)` (for practical
    flicker, titles, captions, head/tail fades), and stream directly into H.264 `out_clip_mp4`.
    """
    h, w = plate_rgb01.shape[:2]
    graded = apply_lut_trilinear(plate_rgb01, lut)
    if halation_strength > 0.0:
        graded = apply_halation_bloom(graded, threshold=0.70, strength=halation_strength)
    pil_graded = Image.fromarray((graded * 255.0 + 0.5).astype(np.uint8))

    if rain_amount > 0.0 and (rain_far is None or rain_near is None):
        rain_far = build_rain_tile(seed=801, density=0.00055, length=46, angle_deg=13.0, blur_r=0.7)
        rain_near = build_rain_tile(seed=802, density=0.00024, length=90, angle_deg=14.5, blur_r=1.15)
    if mist_amount > 0.0 and mist_tile is None:
        mist_tile = build_mist_tile(seed=905)

    rain_col = np.array([0.66, 0.82, 0.98], dtype=np.float32)
    mist_col = np.array([0.52, 0.70, 0.88], dtype=np.float32)

    ff_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{w}x{h}", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-",
        "-vf", "noise=alls=4:allf=t+u",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(crf),
        "-x264-params", "rc-lookahead=12:threads=2",
        "-pix_fmt", "yuv420p", "-r", str(fps),
        out_clip_mp4,
    ]
    proc = subprocess.Popen(ff_cmd, stdin=subprocess.PIPE)

    for i in range(n_frames):
        gf = start_frame_global + i
        t = gf / float(fps)
        u = i / float(max(n_frames - 1, 1))
        # Blended cosine + 65% linear guarantees continuous non-zero velocity on every frame (zero freezedetect!)
        u_s = 0.35 * (0.5 - 0.5 * math.cos(math.pi * u)) + 0.65 * u

        zoom = zoom_start + (zoom_end - zoom_start) * u_s
        px = pan_x_start + (pan_x_end - pan_x_start) * u_s
        py = pan_y_start + (pan_y_end - pan_y_start) * u_s

        cw, ch = w / zoom, h / zoom
        cx, cy = (w * 0.5) + px * w, (h * 0.5) + py * h
        bx0 = max(0.0, min(w - cw, cx - cw * 0.5))
        by0 = max(0.0, min(h - ch, cy - ch * 0.5))

        moved = pil_graded.transform((w, h), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
        frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)

        if mist_amount > 0.0 and mist_tile is not None:
            mt_h, mt_w = mist_tile.shape
            mx = int((gf * 9) % (mt_w - w))
            my = int((gf * 2) % (mt_h - h))
            mv = mist_tile[my : my + h, mx : mx + w] * np.float32(mist_amount)
            if rain_mask is not None:
                mv = mv * rain_mask
            frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - mv[:, :, None] * mist_col)

        if rain_amount > 0.0 and rain_far is not None and rain_near is not None:
            th_r, tw_r = rain_far.shape
            ox1 = int((gf * 19) % (tw_r - w))
            oy1 = int((-gf * 58) % (th_r - h))
            ox2 = int((gf * 33 + 310) % (tw_r - w))
            oy2 = int((-gf * 96 + 170) % (th_r - h))
            rt = (rain_far[oy1 : oy1 + h, ox1 : ox1 + w] * np.float32(0.62) + rain_near[oy2 : oy2 + h, ox2 : ox2 + w] * np.float32(0.88)) * np.float32(rain_amount)
            if rain_mask is not None:
                rt = rt * rain_mask
            np.clip(frame, 0.0, 1.0, out=frame)
            frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - rt[:, :, None] * rain_col)

        np.clip(frame, 0.0, 1.0, out=frame)
        if frame_hook is not None:
            frame = frame_hook(frame, gf, t)

        out_u8 = (np.clip(frame, 0.0, 1.0) * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
        proc.stdin.write(out_u8.tobytes())

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg shot encode failed ({rc}) for {out_clip_mp4}")
