#!/usr/bin/env python3
"""
Generate deterministic 1080p30 slow-motion optical & atmospheric overlay clips
for FFmpeg `blend` compositing in KELVIN (grade-v04):
  1. ov_rain_slow.mp4     - multi-plane diagonal slow-motion rain streaks
  2. ov_mist_drift.mp4    - rolling multi-octave coastal sea fog & rising vapour
  3. ov_warm_halation.mp4 - breathing warm tungsten/sodium optical bloom & flare
  4. ov_water_shimmer.mp4 - slow-motion water specular ripples & bokeh glints
Memory footprint: < 180 MB RSS (synthesizes smoothly at 480x270 / 640x360 and upscales with bicubic/gblur in FFmpeg).
"""
import os
import subprocess
import sys
import numpy as np


FPS = 30
DUR = 6.8
FRAMES = int(round(FPS * DUR))  # 204 frames -> covers max 6.5s shot


def encode_rgb_frames(out_path, w, h, frame_iter):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS),
        "-i", "pipe:0",
        "-vf", "scale=1920:1080:flags=bicubic,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
        out_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for frame in frame_iter:
        proc.stdin.write(frame.astype(np.uint8).tobytes())
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"FFmpeg failed encoding {out_path}")


def gen_rain_slow(rng, w=640, h=360):
    """Multi-depth slow-motion diagonal rain streaks (120fps-captured feel)."""
    n_drops = 260
    x0 = rng.uniform(-0.2, 1.2, n_drops)
    y0 = rng.uniform(0.0, 1.0, n_drops)
    speed = rng.uniform(0.22, 0.58, n_drops)  # slow-motion fall speed
    length = rng.uniform(0.035, 0.11, n_drops)
    bright = rng.uniform(55.0, 185.0, n_drops)
    wind = 0.16  # slight coastal wind slant

    for f in range(FRAMES):
        t = f / FPS
        canvas = np.zeros((h, w), dtype=np.float32)
        yc = (y0 + speed * t) % 1.15 - 0.08
        xc = (x0 + wind * speed * t) % 1.20 - 0.10
        # Draw soft anti-aliased motion-blurred streaks along 10 sub-samples
        for s in np.linspace(0.0, 1.0, 10):
            ys = ((yc - s * length) * h).astype(np.int32)
            xs = ((xc - s * length * wind) * w).astype(np.int32)
            valid = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
            taper = np.sin(np.pi * s)
            np.add.at(canvas, (ys[valid], xs[valid]), bright[valid] * taper * 0.28)

        canvas = np.clip(canvas, 0.0, 255.0)
        # Cool-silver slight tint for rain highlights
        rgb = np.stack([canvas * 0.90, canvas * 0.96, canvas * 1.0], axis=-1)
        yield np.clip(rgb, 0, 255)


def gen_mist_drift(rng, w=320, h=180):
    """Smooth rolling coastal sea mist using summed drifting spatial harmonics."""
    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, h, dtype=np.float32),
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        indexing="ij",
    )
    # 7 octave waves with slow phase drift
    waves = []
    for _ in range(7):
        kx = rng.uniform(1.2, 5.5) * np.pi * rng.choice([-1.0, 1.0])
        ky = rng.uniform(1.0, 4.2) * np.pi * rng.choice([-1.0, 1.0])
        vx = rng.uniform(0.18, 0.55)
        vy = rng.uniform(-0.15, 0.15)
        ph = rng.uniform(0, 2 * np.pi)
        amp = rng.uniform(0.12, 0.28)
        waves.append((kx, ky, vx, vy, ph, amp))

    # Concentrate mist gently toward horizon / middle-lower band
    vert_env = 0.35 + 0.65 * np.exp(-((yy - 0.58) ** 2) / (2 * 0.28 ** 2))

    for f in range(FRAMES):
        t = f / FPS
        field = np.zeros((h, w), dtype=np.float32)
        for kx, ky, vx, vy, ph, amp in waves:
            field += amp * np.sin(kx * xx + ky * yy - vx * t + vy * t + ph)
        norm = np.clip(0.5 + 0.5 * field, 0.0, 1.0) ** 1.6
        val = norm * vert_env * 150.0
        rgb = np.stack([val * 0.93, val * 0.97, val * 1.0], axis=-1)
        yield np.clip(rgb, 0, 255)


def gen_warm_halation(rng, w=320, h=180):
    """Breathing warm amber/tungsten optical bloom & subtle horizontal anamorphic streak."""
    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, h, dtype=np.float32),
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        indexing="ij",
    )
    for f in range(FRAMES):
        t = f / FPS
        cx = 0.52 + 0.04 * np.sin(t * 0.65)
        cy = 0.36 + 0.02 * np.cos(t * 0.50)
        pulse = 0.78 + 0.22 * np.sin(t * 1.35)
        glow = np.exp(-(((xx - cx) / 0.28) ** 2 + ((yy - cy) / 0.22) ** 2)) * pulse
        anamorphic = np.exp(-(((yy - cy) / 0.035) ** 2)) * np.exp(-(((xx - cx) / 0.55) ** 2)) * 0.42 * pulse
        lum = np.clip((glow + anamorphic) * 165.0, 0.0, 255.0)
        rgb = np.stack([lum * 1.0, lum * 0.66, lum * 0.24], axis=-1)
        yield np.clip(rgb, 0, 255)


def gen_water_shimmer(rng, w=480, h=270):
    """Slow-motion lower-half water caustic ripples & soft floating bokeh glints."""
    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, h, dtype=np.float32),
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        indexing="ij",
    )
    water_mask = np.clip((yy - 0.42) / 0.25, 0.0, 1.0) ** 1.3
    for f in range(FRAMES):
        t = f / FPS
        # Perspective-compressed horizontal ripples
        depth = np.maximum(yy - 0.35, 0.06)
        r1 = np.sin((yy / depth) * 26.0 - t * 2.1 + np.sin(xx * 9.0 + t * 0.7) * 1.8)
        r2 = np.cos(xx * 22.0 * depth + yy * 34.0 - t * 1.5)
        caustic = np.clip(0.5 + 0.5 * (0.65 * r1 + 0.35 * r2), 0.0, 1.0) ** 3.2
        val = caustic * water_mask * 155.0
        rgb = np.stack([val * 0.94, val * 0.97, val * 1.0], axis=-1)
        yield np.clip(rgb, 0, 255)


def gen_wipe_matte(rng, w=480, h=270):
    """Smooth diagonal colourist wipe matte (0 -> 255) for Shot 07 live grade transformation."""
    yy, xx = np.meshgrid(
        np.linspace(0.0, 1.0, h, dtype=np.float32),
        np.linspace(0.0, 1.0, w, dtype=np.float32),
        indexing="ij",
    )
    diag = 0.85 * xx + 0.15 * yy
    for f in range(FRAMES):
        t = f / FPS
        # Sweeps smoothly across frame between t=0.55s and t=3.65s
        prog = (t - 0.55) / 2.65
        alpha = np.clip((prog - diag * 0.42) / 0.22, 0.0, 1.0)
        alpha = alpha * alpha * (3.0 - 2.0 * alpha) * 255.0
        rgb = np.stack([alpha, alpha, alpha], axis=-1)
        yield rgb


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/grade_v04_build/overlays"
    rng = np.random.default_rng(20261031)
    jobs = [
        ("ov_rain_slow.mp4", 640, 360, gen_rain_slow),
        ("ov_mist_drift.mp4", 320, 180, gen_mist_drift),
        ("ov_warm_halation.mp4", 320, 180, gen_warm_halation),
        ("ov_water_shimmer.mp4", 480, 270, gen_water_shimmer),
        ("ov_wipe_matte.mp4", 480, 270, gen_wipe_matte),
    ]
    for fname, w, h, fn in jobs:
        out_path = os.path.join(out_dir, fname)
        encode_rgb_frames(out_path, w, h, fn(rng, w, h))
        print(f"Generated overlay: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
