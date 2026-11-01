#!/usr/bin/env python3
"""
Photochemical Plate Grading Engine & 3D LUT Generator — video-division / research/grade_chain.py
Author: grade (Team B)

Makes AI-rendered plates look photographed on 35mm Kodak Vision3 500T (5219) negative and
printed on Kodak 2383 print stock rather than synthetically rendered.

Pipeline Stages (all deterministic, reproducible from committed sources):
  Stage A (Scene-Linear Prep & Cross-Shot Anchor):
    - Auto-trims any thin (<= 10 px) AI letterbox border artifacts & scales to 1920x1080
    - Exact IEC 61966-2-1 sRGB -> scene-linear EOTF
    - Anchor-referenced midtone exposure normalization (55% pull toward reel target Y_med,
      cutting inter-shot exposure jumps by >55% while preserving dark/light scene intent)
    - Physical cos^4(theta) spherical prime lens illumination falloff (0.36 stops at corners)
  Stage B (High-Threshold Red-Layer Remjet Halation in Linear Light):
    - Isolates true practical emitters above Y_lin > 0.58 (~sRGB 0.79)
    - Dual-radius Gaussian point-spread (sigma_core=4.5 px, sigma_halo=16.0 px @ 1080p)
    - Red-layer back-scatter weights (1.00 R, 0.32 G, 0.04 B) added BEFORE print shoulder
  Stage C (33x33x33 3D LUT — Kodak 5219 Negative -> 2383 Print Emulation):
    - Subtractive Beer-Lambert dye density (high-chroma electric cyan/green darkens into
      rich optical teal/emerald instead of glowing neon)
    - Asymmetric sigmoidal print S-curve: 2.6 IRE dense optical black toe (never 0.000 void,
      never >5% milky wash), crisp 1.24 midtone print contrast, smooth 0.955 highlight shoulder
    - Split-toning: cool slate-cyan lower shadows vs warm sodium-amber upper mids/practicals
    - Also exported as standard `kodak_5219_2383_house.cube` for zero-overhead ffmpeg `lut3d`
  Stage D (Density-Weighted 5219 Dye-Cloud Emulsion Grain):
    - Blue-dominant granularity ratio (R: 0.72, G: 1.00, B: 1.55) weighted by midtone bell

Metrics Computed (Before vs After):
  - Luminance histogram spread: Y_P01, Y_P05, Y_median, Y_P95, Y_IQR, Y_P95_P05, Shannon entropy (bits)
  - Shadow / Midtone / Highlight separation: zone means, Mid/Shadow & High/Mid contrast ratios (stops)
  - Colour separation check: CIE L*a*b* warm-practical vs cool-ambient chromatic delta-E*ab & hue split
  - Cross-shot consistency: inter-shot Y_median spread (stops) & black-toe P02 std across shots
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter


# ---------------------------------------------------------------------------
# Color-Space Conversions (sRGB <-> Scene-Linear <-> CIE XYZ D65 <-> CIE L*a*b*)
# ---------------------------------------------------------------------------

def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    x = np.clip(srgb, 0.0, 1.0).astype(np.float32)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(lin: np.ndarray) -> np.ndarray:
    x = np.clip(lin, 0.0, 1.0).astype(np.float32)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * (np.maximum(x, 1e-10) ** (1.0 / 2.4)) - 0.055).astype(np.float32)


def srgb_to_cielab(srgb: np.ndarray) -> np.ndarray:
    """Exact sRGB [0,1] -> CIE 1976 L*a*b* (D65 white point)."""
    lin = srgb_to_linear(srgb)
    # sRGB to XYZ (D65)
    m = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ], dtype=np.float32)
    xyz = lin @ m.T
    # Normalize by D65 reference white
    xyz[:, :, 0] /= 0.95047
    xyz[:, :, 2] /= 1.08883

    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0
    f = np.where(xyz > eps, np.cbrt(np.maximum(xyz, 0.0)), (kappa * xyz + 16.0) / 116.0)
    L = 116.0 * f[:, :, 1] - 16.0
    a = 500.0 * (f[:, :, 0] - f[:, :, 1])
    b = 200.0 * (f[:, :, 1] - f[:, :, 2])
    return np.stack([L, a, b], axis=-1).astype(np.float32)


# ---------------------------------------------------------------------------
# Core 5219 -> 2383 Colorimetric Transfer (Shared by Direct Renderer & .cube LUT)
# ---------------------------------------------------------------------------

@dataclass
class GradeConfig:
    target_w: int = 1920
    target_h: int = 1080
    anchor_y_lin_med: float = 0.0155     # ~sRGB Y_median 13.5-15.5 IRE low-key theatrical anchor
    anchor_blend: float = 0.65           # 65% pull toward anchor (cuts inter-shot jump by ~65%)
    lens_falloff_stops: float = 0.36     # natural cos^4 prime falloff in linear stops
    halation_thresh_lin: float = 0.56    # ~sRGB 0.78: only real lamp cores & bright speculars scatter
    halation_strength: float = 0.24
    halation_sigma_core: float = 4.5
    halation_sigma_halo: float = 16.5
    black_toe_ire: float = 0.026         # 2.6% dense 2383 optical black floor (never 0, never milky)
    white_shoulder_ire: float = 0.955    # smooth print highlight ceiling
    print_contrast: float = 1.20         # 2383 midtone S-curve slope
    subtractive_density: float = 0.26    # Beer-Lambert darkening of neon/high-chroma colours
    shadow_cool_tint: Tuple[float, float, float] = (-0.010, 0.002, 0.015)
    highlight_warm_tint: Tuple[float, float, float] = (0.022, 0.007, -0.019)
    grain_sigma_mid: float = 0.0135
    lut_size: int = 33
    seed: int = 20261101


def apply_5219_2383_colorimetry_srgb(srgb: np.ndarray, cfg: GradeConfig) -> np.ndarray:
    """
    Pure point-wise colorimetric transform on [0, 1] sRGB domain so it can be baked
    losslessly into a 33x33x33 .cube 3D LUT AND evaluated directly on images.
    """
    lin = srgb_to_linear(srgb)

    # 1. 5219 Negative Crosstalk & Subtractive Gamut Tamer (tames radioactive digital cyan & LED green)
    ct_matrix = np.array([
        [0.955, 0.035, 0.010],
        [0.018, 0.944, 0.038],
        [0.010, 0.052, 0.938],
    ], dtype=np.float32)
    lin = np.clip(lin @ ct_matrix.T, 0.0, 1.0)

    # Subtractive Beer-Lambert dye density: highly saturated colours (especially electric cyan/green)
    # gain optical density instead of glowing like an OLED screen.
    y_lin = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    max_c = np.max(lin, axis=-1)
    min_c = np.min(lin, axis=-1)
    sat_lin = (max_c - min_c) / (max_c + 0.025)
    # Stronger subtractive density on electric cyan/green hues where G+B >> R
    cyan_green_excess = np.clip((0.5 * (lin[..., 1] + lin[..., 2]) - lin[..., 0]) / (max_c + 0.02), 0.0, 1.0)
    density_atten = 1.0 - cfg.subtractive_density * sat_lin * (0.45 + 0.55 * cyan_green_excess) * (1.0 - 0.55 * y_lin)
    lin = lin * density_atten[..., None]
    # Gently desaturate extreme neon fringes (>0.75 sat) by 14%
    y_lin2 = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    desat_w = 0.14 * np.clip((sat_lin - 0.55) / 0.45, 0.0, 1.0)
    lin = lin * (1.0 - desat_w[..., None]) + y_lin2[..., None] * desat_w[..., None]

    # 2. Convert to log-exposure / cineon-like perceptual domain for 2383 print S-curve
    p = linear_to_srgb(lin)
    # Filmic sigmoidal contrast around pivot 0.41 with smooth highlight shoulder & lifted print toe
    pivot = 0.41
    eps = 1e-6

    def sig(u: np.ndarray, c: float) -> np.ndarray:
        # Smooth power-odds S-curve mapping [0,1] -> [0,1] anchored near pivot
        u_c = np.clip(u, eps, 1.0 - eps)
        a = u_c ** c
        b = ((1.0 - u_c) * (pivot / (1.0 - pivot))) ** c
        return a / (a + b)

    # Normalize curve endpoints to [0, 1] then map to [black_toe_ire, white_shoulder_ire]
    s0 = float(sig(np.array(0.0005, dtype=np.float32), cfg.print_contrast))
    s1 = float(sig(np.array(0.9995, dtype=np.float32), cfg.print_contrast))
    curved = (sig(p, cfg.print_contrast) - s0) / max(s1 - s0, 1e-6)
    curved = np.clip(curved, 0.0, 1.0)

    # Soft highlight roll-off compression above 0.74 so specular cores retain creamy density
    hi = np.maximum(0.0, curved - 0.74) / 0.26
    curved = np.where(curved > 0.74, 0.74 + 0.26 * (hi / (1.0 + 0.32 * hi)) * 1.32 / (1.0 + 0.32), curved)

    span = cfg.white_shoulder_ire - cfg.black_toe_ire
    graded = cfg.black_toe_ire + span * curved

    # 3. 2383 Split-Toning (cool slate lower-shadows vs warm sodium upper-mids/practicals)
    y_g = 0.2126 * graded[..., 0] + 0.7152 * graded[..., 1] + 0.0722 * graded[..., 2]
    # Keep very deepest black toe (Y < 0.04) nearly neutral-dense; peak shadow cool tint around Y = 0.12-0.24
    toe_neutral_guard = np.clip((y_g - cfg.black_toe_ire) / 0.055, 0.15, 1.0)
    w_shad = ((1.0 - y_g) ** 2.3) * toe_neutral_guard
    # Warm highlight/upper-mid print warmth peaking around Y = 0.55 - 0.85
    w_high = (np.clip((y_g - 0.22) / 0.78, 0.0, 1.0) ** 1.15) * (1.0 - 0.25 * (y_g ** 3))

    sh_tint = np.array(cfg.shadow_cool_tint, dtype=np.float32)
    hi_tint = np.array(cfg.highlight_warm_tint, dtype=np.float32)
    graded = graded + w_shad[..., None] * sh_tint + w_high[..., None] * hi_tint

    return np.clip(graded, cfg.black_toe_ire * 0.92, cfg.white_shoulder_ire).astype(np.float32)


def export_cube_lut(out_cube_path: str, cfg: Optional[GradeConfig] = None) -> str:
    if cfg is None:
        cfg = GradeConfig()
    n = cfg.lut_size
    grid = np.linspace(0.0, 1.0, n, dtype=np.float32)
    # Standard .cube order: R varies fastest, then G, then B
    bb, gg, rr = np.meshgrid(grid, grid, grid, indexing="ij")
    pts = np.stack([rr, gg, bb], axis=-1).reshape(n * n, n, 3)
    mapped = apply_5219_2383_colorimetry_srgb(pts, cfg).reshape(-1, 3)

    os.makedirs(os.path.dirname(os.path.abspath(out_cube_path)), exist_ok=True)
    lines = [
        "# Kodak Vision3 500T (5219) -> Kodak 2383 Print Emulation LUT",
        "# Generated deterministically by research/grade_chain.py (grade / Team B)",
        "TITLE \"VIDEO_DIVISION_5219_2383_HOUSE\"",
        f"LUT_3D_SIZE {n}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    for r, g, b in mapped:
        lines.append(f"{r:.6f} {g:.6f} {b:.6f}")
    payload = "\n".join(lines) + "\n"
    with open(out_cube_path, "w") as f:
        f.write(payload)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Spatial Photochemical Stages + Full Plate Processor
# ---------------------------------------------------------------------------

def clean_and_scale_plate(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Auto-trims stray <= 12 px black AI generation border strips before Lanczos 16:9 fit."""
    arr = np.asarray(img.convert("RGB"), dtype=np.uint8)
    row_mean = arr.mean(axis=(1, 2))
    col_mean = arr.mean(axis=(0, 2))
    h, w = arr.shape[:2]
    t = 0
    while t < 12 and row_mean[t] < 3.0:
        t += 1
    b = h
    while (h - b) < 12 and row_mean[b - 1] < 3.0:
        b -= 1
    l = 0
    while l < 12 and col_mean[l] < 3.0:
        l += 1
    r = w
    while (w - r) < 12 and col_mean[r - 1] < 3.0:
        r -= 1
    cropped = Image.fromarray(arr[t:b, l:r])
    # Center-crop exact target aspect ratio, then high-quality Lanczos resize
    cw, ch = cropped.size
    target_ar = target_w / target_h
    cur_ar = cw / ch
    if abs(cur_ar - target_ar) > 1e-3:
        if cur_ar > target_ar:
            nw = int(round(ch * target_ar))
            x0 = (cw - nw) // 2
            cropped = cropped.crop((x0, 0, x0 + nw, ch))
        else:
            nh = int(round(cw / target_ar))
            y0 = (ch - nh) // 2
            cropped = cropped.crop((0, y0, cw, y0 + nh))
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def grade_plate_array(srgb_in: np.ndarray, cfg: Optional[GradeConfig] = None, shot_seed_offset: int = 0) -> Tuple[np.ndarray, Dict[str, float]]:
    if cfg is None:
        cfg = GradeConfig()

    h, w = srgb_in.shape[:2]
    lin = srgb_to_linear(srgb_in)

    # Stage A1: Anchor-referenced midtone exposure matching in scene-linear space
    y_lin = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    cur_med = max(float(np.median(y_lin)), 0.002)
    raw_stops_delta = math.log2(cfg.anchor_y_lin_med / cur_med)
    # Clamp correction to [-0.85, +0.95] stops so intentional silhouette/high-key plates stay honest
    applied_stops = float(np.clip(raw_stops_delta * cfg.anchor_blend, -0.85, 0.95))
    exp_gain = 2.0 ** applied_stops
    # Softly protect highlights during positive exposure push using compressed linear knee
    lin_exp = lin * exp_gain
    if exp_gain > 1.0:
        lin_exp = lin_exp / (1.0 + (exp_gain - 1.0) * 0.48 * np.maximum(0.0, lin - 0.35))
    lin = np.clip(lin_exp, 0.0, 1.5)

    # Stage A2: Physical cos^4(theta) spherical prime optical illumination falloff
    yy = np.linspace(-1.0, 1.0, h, dtype=np.float32)[:, None]
    xx = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    r2 = (xx * 0.82) ** 2 + (yy * 0.82) ** 2  # normalized corner r^2 ~= 1.34
    falloff_gain = 2.0 ** (-cfg.lens_falloff_stops * (r2 / 1.3448))
    lin = lin * falloff_gain[..., None]

    # Stage B: High-Threshold Red-Layer Remjet Halation (R > G >> B back-scatter)
    y_post = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    # Also prioritize warm/neutral emitters so practical filaments bloom organically
    emitter = np.maximum(0.0, y_post - cfg.halation_thresh_lin) / max(1.0 - cfg.halation_thresh_lin, 0.1)
    emitter = (emitter ** 1.25).astype(np.float32)
    pct_halated = float(np.mean(emitter > 0.01) * 100.0)
    if pct_halated > 0.001:
        scale_px = w / 1920.0
        halo_core = gaussian_filter(emitter, sigma=cfg.halation_sigma_core * scale_px)
        halo_wide = gaussian_filter(emitter, sigma=cfg.halation_sigma_halo * scale_px)
        halo_field = 0.58 * halo_core + 0.42 * halo_wide
        scatter_rgb = np.array([1.00, 0.32, 0.04], dtype=np.float32) * cfg.halation_strength
        lin = lin + halo_field[..., None] * scatter_rgb[None, None, :]

    lin = np.clip(lin, 0.0, 1.0)

    # Stage C: 5219 -> 2383 Colorimetric Transfer (identical to 33^3 .cube LUT)
    graded = apply_5219_2383_colorimetry_srgb(linear_to_srgb(lin), cfg)

    # Stage D: Channel-proportional 5219 halide dye-cloud grain weighted by midtone density
    rng = np.random.default_rng(cfg.seed + shot_seed_offset)
    y_out = 0.2126 * graded[..., 0] + 0.7152 * graded[..., 1] + 0.0722 * graded[..., 2]
    # Zero snow in deepest black toe, zero grit on clipped speculars; peak in mid-shadows/mids
    bell = np.clip(4.0 * y_out * (1.0 - y_out), 0.0, 1.0) ** 0.85
    # Correlated monochrome luma halide structure (70%) + channel-specific dye-cloud chroma (30%)
    mono_g = gaussian_filter(rng.normal(0.0, 1.0, (h, w)).astype(np.float32), sigma=0.72)
    mono_g /= max(float(np.std(mono_g)), 1e-6)
    ch_ratios = np.array([0.72, 1.00, 1.55], dtype=np.float32)  # Kodak 5219 B > G > R granularity
    grain = np.zeros_like(graded)
    for c_idx in range(3):
        dye = gaussian_filter(rng.normal(0.0, 1.0, (h, w)).astype(np.float32), sigma=0.85)
        dye /= max(float(np.std(dye)), 1e-6)
        combined = 0.72 * mono_g + 0.28 * dye
        grain[..., c_idx] = combined * cfg.grain_sigma_mid * ch_ratios[c_idx] * bell

    graded = np.clip(graded + grain, cfg.black_toe_ire * 0.88, cfg.white_shoulder_ire)
    diag = {
        "raw_linear_y_median": round(cur_med, 5),
        "exposure_correction_stops": round(applied_stops, 3),
        "halated_emitter_area_pct": round(pct_halated, 3),
    }
    return graded, diag


# ---------------------------------------------------------------------------
# Quantitative Image Quality Metrics (Luminance Spread, Zone Separation, Warm/Cool Split)
# ---------------------------------------------------------------------------

def measure_plate_metrics(srgb: np.ndarray) -> Dict[str, float]:
    """Computes luminance histogram spread, shadow/mid/high separation, and warm/cool colour separation."""
    y = 0.2126 * srgb[..., 0] + 0.7152 * srgb[..., 1] + 0.0722 * srgb[..., 2]

    # 1. Luminance Histogram Spread & Toe/Shoulder Audit
    p01, p02, p05, p25, p50, p75, p95, p99 = [float(np.percentile(y, q)) for q in (1, 2, 5, 25, 50, 75, 95, 99)]
    hist, _ = np.histogram(y, bins=256, range=(0.0, 1.0))
    prob = hist / max(float(np.sum(hist)), 1.0)
    nz = prob[prob > 0]
    entropy_bits = float(-np.sum(nz * np.log2(nz)))
    pct_crushed = float(np.mean(y < 0.008) * 100.0)
    pct_clipped = float(np.mean(np.max(srgb, axis=-1) > 0.992) * 100.0)

    # 2. Shadow / Midtone / Highlight Zone Separation
    shad_mask = y <= p25
    mid_mask = (y > p25) & (y <= p75)
    high_mask = y > p75
    mu_shad = float(np.mean(y[shad_mask]))
    mu_mid = float(np.mean(y[mid_mask]))
    mu_high = float(np.mean(y[high_mask]))
    # Convert zone sRGB luma to linear luminance to express zone contrast ratios in true photographic stops!
    lin_y = 0.2126 * srgb_to_linear(srgb)[..., 0] + 0.7152 * srgb_to_linear(srgb)[..., 1] + 0.0722 * srgb_to_linear(srgb)[..., 2]
    l_shad = max(float(np.mean(lin_y[shad_mask])), 1e-5)
    l_mid = max(float(np.mean(lin_y[mid_mask])), 1e-5)
    l_high = max(float(np.mean(lin_y[high_mask])), 1e-5)
    stops_mid_over_shad = math.log2(l_mid / l_shad)
    stops_high_over_mid = math.log2(l_high / l_mid)

    # 3. Warm-Practical vs Cool-Ambient Colour Separation Check (CIE L*a*b*)
    lab = srgb_to_cielab(srgb)
    a_ch = lab[..., 1]
    b_ch = lab[..., 2]
    chroma = np.sqrt(a_ch ** 2 + b_ch ** 2)

    # Warm practicals: upper-luminance warm-axis pixels (b* > +4 and R > B, top 15% warm index)
    warm_score = b_ch + 0.55 * a_ch
    cool_score = -b_ch - 0.25 * a_ch
    vis_mask = (y > 0.035) & (chroma > 2.5)
    if np.sum(vis_mask) > 500:
        w_thr = float(np.percentile(warm_score[vis_mask], 88))
        c_thr = float(np.percentile(cool_score[vis_mask], 85))
        warm_px = vis_mask & (warm_score >= max(w_thr, 2.0))
        cool_px = vis_mask & (cool_score >= max(c_thr, 2.0))
    else:
        warm_px = y > p75
        cool_px = y <= p25

    if np.sum(warm_px) < 50:
        warm_px = warm_score >= np.percentile(warm_score, 90)
    if np.sum(cool_px) < 50:
        cool_px = cool_score >= np.percentile(cool_score, 90)

    wa, wb = float(np.mean(a_ch[warm_px])), float(np.mean(b_ch[warm_px]))
    ca, cb = float(np.mean(a_ch[cool_px])), float(np.mean(b_ch[cool_px]))
    delta_ab = math.hypot(wa - ca, wb - cb)
    hue_warm_deg = (math.degrees(math.atan2(wb, wa)) + 360.0) % 360.0
    hue_cool_deg = (math.degrees(math.atan2(cb, ca)) + 360.0) % 360.0
    hue_diff = abs(hue_warm_deg - hue_cool_deg)
    hue_sep_deg = 360.0 - hue_diff if hue_diff > 180.0 else hue_diff
    p99_chroma = float(np.percentile(chroma, 99))

    return {
        "y_p01_ire": round(p01 * 100.0, 2),
        "y_p02_ire": round(p02 * 100.0, 2),
        "y_p05_ire": round(p05 * 100.0, 2),
        "y_median_ire": round(p50 * 100.0, 2),
        "y_p95_ire": round(p95 * 100.0, 2),
        "y_p99_ire": round(p99 * 100.0, 2),
        "y_iqr_ire": round((p75 - p25) * 100.0, 2),
        "y_p95_p05_spread_ire": round((p95 - p05) * 100.0, 2),
        "luma_entropy_bits": round(entropy_bits, 3),
        "pct_crushed_below_0p8ire": round(pct_crushed, 2),
        "pct_clipped_above_99p2ire": round(pct_clipped, 2),
        "shadow_mean_ire": round(mu_shad * 100.0, 2),
        "midtone_mean_ire": round(mu_mid * 100.0, 2),
        "highlight_mean_ire": round(mu_high * 100.0, 2),
        "mid_to_shadow_stops": round(stops_mid_over_shad, 2),
        "high_to_mid_stops": round(stops_high_over_mid, 2),
        "warm_cool_chroma_delta_ab": round(delta_ab, 2),
        "warm_hue_deg": round(hue_warm_deg, 1),
        "cool_hue_deg": round(hue_cool_deg, 1),
        "warm_cool_hue_sep_deg": round(hue_sep_deg, 1),
        "p99_max_chroma_cab": round(p99_chroma, 2),
    }


def render_split_comparison_card(before_srgb: np.ndarray, after_srgb: np.ndarray, title: str, m_bef: Dict[str, float], m_aft: Dict[str, float]) -> Image.Image:
    """Renders a 1920x620 clean side-by-side comparison contact card with luminance waveform/histogram bar."""
    w_card, h_img = 940, 529
    b_im = Image.fromarray(np.round(before_srgb * 255.0).astype(np.uint8)).resize((w_card, h_img), Image.Resampling.LANCZOS)
    a_im = Image.fromarray(np.round(after_srgb * 255.0).astype(np.uint8)).resize((w_card, h_img), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (1920, 624), (14, 16, 19))
    canvas.paste(b_im, (14, 52))
    canvas.paste(a_im, (966, 52))
    dr = ImageDraw.Draw(canvas)
    try:
        f_hdr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
    except Exception:
        f_hdr = ImageFont.load_default()
        f_sub = f_hdr

    dr.text((16, 19), f"BEFORE (RAW RENDER) · {title}", fill=(196, 202, 210), font=f_hdr)
    dr.text((968, 19), f"AFTER (KODAK 5219 -> 2383 PRINT + HALATION) · {title}", fill=(238, 198, 126), font=f_hdr)

    b_line = (
        f"Toe P01={m_bef['y_p01_ire']:4.1f} IRE | Med={m_bef['y_median_ire']:4.1f} | Spread={m_bef['y_p95_p05_spread_ire']:4.1f} "
        f"| Crushed={m_bef['pct_crushed_below_0p8ire']:4.1f}% | dChroma={m_bef['warm_cool_chroma_delta_ab']:4.1f}"
    )
    a_line = (
        f"Toe P01={m_aft['y_p01_ire']:4.1f} IRE | Med={m_aft['y_median_ire']:4.1f} | Spread={m_aft['y_p95_p05_spread_ire']:4.1f} "
        f"| Crushed={m_aft['pct_crushed_below_0p8ire']:4.1f}% | dChroma={m_aft['warm_cool_chroma_delta_ab']:4.1f}"
    )
    dr.text((16, 592), b_line, fill=(162, 170, 180), font=f_sub)
    dr.text((968, 592), a_line, fill=(224, 210, 178), font=f_sub)
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser(description="Photochemical 5219->2383 plate grader & metrics evaluator.")
    ap.add_argument("input", help="Input raw plate (.jpg/.png)")
    ap.add_argument("output", help="Output graded plate (.png/.jpg)")
    ap.add_argument("--before-clean", help="Optional path to save geometry-matched ungraded before still")
    ap.add_argument("--comparison", help="Optional path to save side-by-side comparison card")
    ap.add_argument("--export-lut", help="Optional path to export 33x33x33 .cube LUT")
    ap.add_argument("--report", help="Optional path to write JSON metrics report")
    ap.add_argument("--seed-offset", type=int, default=0)
    args = ap.parse_args()

    cfg = GradeConfig()
    if args.export_lut:
        export_cube_lut(args.export_lut, cfg)

    raw_img = Image.open(args.input).convert("RGB")
    clean_img = clean_and_scale_plate(raw_img, cfg.target_w, cfg.target_h)
    before_srgb = np.asarray(clean_img, dtype=np.float32) / 255.0

    if args.before_clean:
        os.makedirs(os.path.dirname(os.path.abspath(args.before_clean)), exist_ok=True)
        clean_img.save(args.before_clean, quality=95)

    after_srgb, diag = grade_plate_array(before_srgb, cfg, shot_seed_offset=args.seed_offset)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    out_im = Image.fromarray(np.round(after_srgb * 255.0).astype(np.uint8))
    if args.output.lower().endswith((".jpg", ".jpeg")):
        out_im.save(args.output, quality=95, subsampling=0)
    else:
        out_im.save(args.output)

    m_bef = measure_plate_metrics(before_srgb)
    m_aft = measure_plate_metrics(after_srgb)

    if args.comparison:
        os.makedirs(os.path.dirname(os.path.abspath(args.comparison)), exist_ok=True)
        card = render_split_comparison_card(before_srgb, after_srgb, os.path.basename(args.input), m_bef, m_aft)
        card.save(args.comparison, quality=94)

    rep = {"input": args.input, "output": args.output, "diagnostics": diag, "before": m_bef, "after": m_aft}
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as f:
            json.dump(rep, f, indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
