#!/usr/bin/env python3
"""
First-party 33x33x33 3D .cube LUT generator for MARK FOUR (grade-v05).
Author: grade <grade@agency.local>
Licence: First-party original code & colour transforms created in-repo by grade.

Generates four high-contrast nocturnal cinema LUTs pushing the KELVIN signature further:
  1. blackwater_slate.cube   — 5600K floodlit obsidian slate + crimson IV accent (Shots 01, 02, 03)
  2. amber_ledger.cube       — 2200K tungsten/lantern gold vs deep Prussian storm night (Shots 04, 07, 08)
  3. mercury_stillness.cube  — 4300K cold cyan-emerald vapour + surgical red datum isolation (Shots 05, 06)
  4. sluice_breach.cube      — 6800K stark ice-blue storm moonlight + crimson breach contrast (Shots 09, 10, 11)
"""

import os
import numpy as np


def filmic_scurve(x: np.ndarray, contrast: float = 1.32, pivot: float = 0.42, toe_crush: float = 0.035) -> np.ndarray:
    """High-contrast Kodak 5219-inspired S-curve with deep obsidian toe and smooth highlight shoulder."""
    x = np.clip((x - toe_crush) / (1.0 - toe_crush), 0.0, 1.0)
    eps = 1e-6
    xp = np.clip(x, eps, 1.0 - eps)
    # Logistic / power S-curve around pivot
    num = (xp ** contrast)
    den = num + ((1.0 - xp) ** contrast) * ((pivot / (1.0 - pivot)) ** (contrast - 1.0))
    y = num / np.maximum(den, eps)
    # Gentle highlight roll-off above 0.82
    y = y / (1.0 + 0.08 * np.maximum(0.0, y - 0.82))
    return np.clip(y, 0.0, 1.0)


def write_cube(path: str, title: str, lut_rgb: np.ndarray) -> None:
    size = lut_rgb.shape[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'TITLE "{title}"\n')
        f.write("# Created by grade <grade@agency.local> for MARK FOUR (grade-v05)\n")
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        # .cube standard order: R fastest, then G, then B
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv, gv, bv = lut_rgb[b, g, r]
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")


def make_grid(size: int = 33):
    vals = np.linspace(0.0, 1.0, size, dtype=np.float32)
    b, g, r = np.meshgrid(vals, vals, vals, indexing="ij")
    return r, g, b


def build_all_luts(out_dir: str) -> None:
    r0, g0, b0 = make_grid(33)
    lum0 = 0.2126 * r0 + 0.7152 * g0 + 0.0722 * b0

    # Colour selectivity masks (preserve crimson warning paint & warm tungsten practicals cleanly)
    red_dom = np.clip((r0 - np.maximum(g0, b0)) * 2.6, 0.0, 1.0)
    warm_dom = np.clip((r0 - b0) * 1.8, 0.0, 1.0) * np.clip((g0 - b0 * 0.65) * 1.6, 0.0, 1.0)
    sh_w = np.clip(1.0 - lum0 * 2.1, 0.0, 1.0) ** 1.4
    hi_w = np.clip((lum0 - 0.45) / 0.55, 0.0, 1.0)

    # 1. blackwater_slate.cube (Shots 01, 02, 03)
    r = filmic_scurve(r0, contrast=1.38, pivot=0.43, toe_crush=0.032)
    g = filmic_scurve(g0, contrast=1.36, pivot=0.42, toe_crush=0.028)
    b = filmic_scurve(b0, contrast=1.30, pivot=0.40, toe_crush=0.020)
    # Desaturate neutral stone slightly while boosting steel-blue shadows & preserving crimson/amber
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sat = 0.80 + 0.42 * np.maximum(red_dom, warm_dom)
    r = lum + (r - lum) * sat
    g = lum + (g - lum) * sat
    b = lum + (b - lum) * sat
    r = r - 0.026 * sh_w * (1.0 - warm_dom) + 0.065 * red_dom
    g = g - 0.006 * sh_w + 0.015 * hi_w * (1.0 - warm_dom)
    b = b + 0.034 * sh_w * (1.0 - warm_dom) + 0.048 * hi_w * (1.0 - warm_dom)
    lut1 = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    write_cube(os.path.join(out_dir, "blackwater_slate.cube"), "GRADE_V05_BLACKWATER_SLATE", lut1)

    # 2. amber_ledger.cube (Shots 04, 07 [Poster], 08 — strong chiaroscuro Prussian vs 2200K lantern gold)
    r = filmic_scurve(r0, contrast=1.42, pivot=0.42, toe_crush=0.034)
    g = filmic_scurve(g0, contrast=1.39, pivot=0.42, toe_crush=0.032)
    b = filmic_scurve(b0, contrast=1.34, pivot=0.41, toe_crush=0.024)
    # Split-tone: Prussian-cyan shadows, rich golden-amber highlights where warm_dom is present, steel-cyan rain where cool
    cool_mask = 1.0 - np.clip(warm_dom * 1.35, 0.0, 1.0)
    r = r - 0.034 * sh_w * cool_mask + 0.085 * warm_dom * (0.4 + 0.6 * hi_w)
    g = g + 0.008 * sh_w * cool_mask + 0.038 * warm_dom * (0.3 + 0.7 * hi_w) + 0.020 * hi_w * cool_mask
    b = b + 0.046 * sh_w * cool_mask + 0.052 * hi_w * cool_mask - 0.045 * warm_dom
    lut2 = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    write_cube(os.path.join(out_dir, "amber_ledger.cube"), "GRADE_V05_AMBER_LEDGER", lut2)

    # 3. mercury_stillness.cube (Shots 05, 06 — 4300K cyan-emerald industrial dread + razor red line)
    r = filmic_scurve(r0, contrast=1.40, pivot=0.44, toe_crush=0.038)
    g = filmic_scurve(g0, contrast=1.36, pivot=0.41, toe_crush=0.028)
    b = filmic_scurve(b0, contrast=1.34, pivot=0.41, toe_crush=0.026)
    non_red = 1.0 - np.clip(red_dom * 1.6, 0.0, 1.0)
    r = r - 0.038 * non_red * (0.5 + 0.5 * sh_w) + 0.090 * red_dom
    g = g + 0.028 * non_red * (0.4 + 0.6 * hi_w) - 0.020 * red_dom
    b = b + 0.036 * non_red * (0.5 + 0.5 * hi_w) - 0.025 * red_dom
    lut3 = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    write_cube(os.path.join(out_dir, "mercury_stillness.cube"), "GRADE_V05_MERCURY_STILLNESS", lut3)

    # 4. sluice_breach.cube (Shots 09, 10, 11 — 6800K stark ice-blue storm moonlight + crimson breach)
    r = filmic_scurve(r0, contrast=1.44, pivot=0.43, toe_crush=0.036)
    g = filmic_scurve(g0, contrast=1.40, pivot=0.42, toe_crush=0.032)
    b = filmic_scurve(b0, contrast=1.32, pivot=0.39, toe_crush=0.020)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    keep_accent = np.maximum(red_dom * 1.4, warm_dom * 0.85)
    keep_accent = np.clip(keep_accent, 0.0, 1.0)
    # Desaturate into stark moonlight silver-blue except crimson/brass accents
    r = (lum * 0.88 + r * 0.12) * (1.0 - keep_accent) + (r + 0.075 * red_dom) * keep_accent
    g = (lum * 0.96 + g * 0.04) * (1.0 - keep_accent) + g * keep_accent
    b = (lum * 1.14 + b * 0.10 + 0.030 * sh_w) * (1.0 - keep_accent) + b * keep_accent
    lut4 = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    write_cube(os.path.join(out_dir, "sluice_breach.cube"), "GRADE_V05_SLUICE_BREACH", lut4)


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")
    build_all_luts(target)
    print(f"Generated 4 33x33x33 .cube LUTs in {target}")
