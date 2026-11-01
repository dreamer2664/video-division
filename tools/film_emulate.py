#!/usr/bin/env python3
"""Small, deterministic film-emulation treatment for stills or selected video frames.

Usage: python3 tools/film_emulate.py input.mp4 --times 8.5,27,46 --outdir research/film_emulation
Requires OpenCV (cv2) and NumPy. No video is re-encoded; output is a set of PNG frames.
The look is an adjustable creative approximation, not a calibrated stock or photochemical model.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import cv2
import numpy as np


def srgb_to_linear(x):
    x = np.asarray(x, dtype=np.float32) / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    x = np.clip(x, 0, 1)
    y = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    return np.clip(np.rint(y * 255), 0, 255).astype(np.uint8)


def _remap(img, dx, dy):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(img, xx + dx.astype(np.float32), yy + dy.astype(np.float32),
                     cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)


def emulate(rgb: np.ndarray, seed: int = 0, strength: float = 1.0) -> np.ndarray:
    """Apply luminance grain, halation, CA, weave, vignette, distortion, and lifted blacks."""
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected an RGB image with three channels")
    h, w = rgb.shape[:2]
    original = srgb_to_linear(rgb)
    y, x = np.mgrid[-1:1:complex(h), -1:1:complex(w)].astype(np.float32)
    r2 = x*x + y*y

    # Slight radial barrel distortion plus subpixel red/blue lateral separation.
    k = -0.010 * strength
    base_dx = x * r2 * k * (w / 2)
    base_dy = y * r2 * k * (h / 2)
    red = _remap(original[:, :, 0], base_dx + x * r2 * 0.35 * strength,
                 base_dy + y * r2 * 0.35 * strength)
    green = _remap(original[:, :, 1], base_dx, base_dy)
    blue = _remap(original[:, :, 2], base_dx - x * r2 * 0.35 * strength,
                  base_dy - y * r2 * 0.35 * strength)
    img = np.stack([red, green, blue], axis=2)

    # Highlight halation: diffuse bright-energy mask with a restrained warm/red bias.
    lum = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]
    mask = np.maximum(lum - 0.72, 0) ** 1.35
    sigma = max(2.0, min(h, w) * 0.012)
    halo = cv2.GaussianBlur(mask, (0, 0), sigmaX=sigma, sigmaY=sigma)
    img[:, :, 0] += halo * 0.17 * strength
    img[:, :, 1] += halo * 0.055 * strength
    img[:, :, 2] += halo * 0.018 * strength

    # Luminance-dependent fine grain: dim areas retain subtle grain, highlights get more.
    rng = np.random.default_rng(seed)
    lum = np.clip(0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2], 0, 1)
    grain_sigma = (0.006 + 0.014 * np.sqrt(lum)) * strength
    noise = rng.normal(0, 1, (h, w)).astype(np.float32) * grain_sigma
    img += noise[:, :, None]

    # Gentle center falloff and a small black-level lift.
    vignette = np.clip(1.0 - 0.10 * strength * (r2 / 2.0), 0.82, 1.0)
    img *= vignette[:, :, None]
    img = 0.006 * strength + img * (1.0 - 0.006 * strength)

    # Deterministic subpixel gate weave from seed; half-pixel range, reflective borders.
    wrng = np.random.default_rng(seed + 991)
    shift_x, shift_y = wrng.uniform(-0.45, 0.45, size=2) * strength
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32) + np.float32(shift_x),
                         np.arange(h, dtype=np.float32) + np.float32(shift_y))
    img = cv2.remap(img, xx.astype(np.float32), yy.astype(np.float32), cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT101)
    return linear_to_srgb(img)


def _metrics(rgb: np.ndarray) -> dict:
    """Repeatable image proxies; not ground-truth film measurements."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    y = lab[:, :, 0].astype(np.float32) / 255.0
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    # Remove broad scene structure, then estimate fine residual noise and clumping.
    low = cv2.GaussianBlur(gray, (0, 0), 1.2)
    residual = gray - low
    residual = residual - np.mean(residual)
    std = float(np.std(residual))
    denom = float(np.sum(residual * residual)) + 1e-12
    corr_x = float(np.sum(residual[:, :-1] * residual[:, 1:]) / denom)
    corr_y = float(np.sum(residual[:-1, :] * residual[1:, :]) / denom)
    # Local radial falloff around the brightest connected highlight cores. This is a
    # content-dependent 10%-above-local-background radius, not a calibrated optics test.
    threshold = float(np.quantile(y, 0.998))
    nlab, labels, stats, _ = cv2.connectedComponentsWithStats((y >= threshold).astype(np.uint8), 8)
    widths = []
    for lab in range(1, nlab):
        if stats[lab, cv2.CC_STAT_AREA] < 3:
            continue
        x0, y0, bw, bh, _area = stats[lab]
        pad = 36
        xa, xb = max(0, x0-pad), min(y.shape[1], x0+bw+pad)
        ya, yb = max(0, y0-pad), min(y.shape[0], y0+bh+pad)
        local_core = labels[ya:yb, xa:xb] == lab
        distance = cv2.distanceTransform((~local_core).astype(np.uint8), cv2.DIST_L2, 3)
        patch = y[ya:yb, xa:xb]
        profile = np.array([np.mean(patch[(distance >= r) & (distance < r+1)])
                            if np.any((distance >= r) & (distance < r+1)) else np.nan
                            for r in range(0, 31)])
        baseline_vals = patch[(distance >= 28) & (distance <= 35)]
        if len(baseline_vals) == 0 or np.all(np.isnan(profile[2:8])):
            continue
        baseline = float(np.mean(baseline_vals))
        peak_vals = profile[1:5][~np.isnan(profile[1:5])]
        if not len(peak_vals):
            continue
        peak = float(np.mean(peak_vals))
        cutoff = baseline + max(0.004, 0.10 * (peak - baseline))
        above = [r for r in range(1, 28) if not np.isnan(profile[r]) and profile[r] > cutoff]
        if above and peak > baseline + 0.004:
            widths.append(float(max(above)))
    bloom_width = float(np.median(widths)) if widths else 0.0
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad = cv2.magnitude(gx, gy)
    edge = grad >= np.quantile(grad, 0.85)
    acutance = float(np.mean(grad[edge])) if np.any(edge) else 0.0
    p05, p95 = np.quantile(y, [0.05, 0.95])
    return {"grain_residual_sd_8bit": std * 255,
            "grain_adjacent_correlation_x": corr_x, "grain_adjacent_correlation_y": corr_y,
            "highlight_bloom_width_px_heuristic": bloom_width,
            "edge_acutance_sobel_mean": acutance,
            "luma_histogram_p95_minus_p05": float((p95-p05)*255),
            "luma_histogram_sd_8bit": float(np.std(y)*255)}


def extract_frame(video: str, seconds: float) -> np.ndarray:
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video}")
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ok, bgr = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read frame at {seconds:.3f}s")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="video file; selected frames are decoded via OpenCV")
    ap.add_argument("--times", default="8.5,27,46", help="comma-separated extraction times in seconds")
    ap.add_argument("--outdir", default="film_emulation", help="output directory for PNG frames and JSON")
    ap.add_argument("--strength", type=float, default=1.0)
    args = ap.parse_args()
    times = [float(t.strip()) for t in args.times.split(",") if t.strip()]
    if not times or args.strength < 0:
        ap.error("provide at least one time and a non-negative strength")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, t in enumerate(times):
        before = extract_frame(args.input, t)
        after = emulate(before, seed=20261101 + i, strength=args.strength)
        before_path, after_path = outdir / f"frame-{i+1:02d}-before.png", outdir / f"frame-{i+1:02d}-after.png"
        cv2.imwrite(str(before_path), cv2.cvtColor(before, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(after_path), cv2.cvtColor(after, cv2.COLOR_RGB2BGR))
        rows.append({"frame": i+1, "source_seconds": t, "before_file": before_path.name,
                     "after_file": after_path.name, "before": _metrics(before), "after": _metrics(after)})
    manifest = {"input": Path(args.input).name, "strength": args.strength,
                "method_note": "Metrics are image-content-dependent proxies, not calibrated film-stock measurements.",
                "frames": rows}
    (outdir / "measurements.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
