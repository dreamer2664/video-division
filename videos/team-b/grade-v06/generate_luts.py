#!/usr/bin/env python3
"""
First-party 33x33x33 3D .cube LUT generator for MARK FIVE (grade-v06).
Author: grade <grade@agency.local>

Generates four nocturnal high-contrast cinema LUTs in the KELVIN / MARK signature:
  1. spillway_obsidian.cube    — 5600K floodlit wet basalt + crimson 'V' isolation (Shots 01, 03)
  2. copper_bakelite.cube      — 2200K tungsten/copper gold vs deep Prussian storm vaults (Shots 02, 05, 07)
  3. cyan_skylight.cube        — 4400K cold mercury-cyan steel & wired skylight glass (Shots 04, 06)
  4. ceiling_flood_6800k.cube  — 6800K stark ice-blue storm moonlight + crimson 'MARK V' stencil (Shots 08, 09, 10)
"""

import os
import numpy as np


def filmic_scurve(x: np.ndarray, contrast: float = 1.38, pivot: float = 0.42, toe_crush: float = 0.033) -> np.ndarray:
    x = np.clip((x - toe_crush) / (1.0 - toe_crush), 0.0, 1.0)
    eps = 1e-6
    xp = np.clip(x, eps, 1.0 - eps)
    num = xp ** contrast
    den = num + ((1.0 - xp) ** contrast) * ((pivot / (1.0 - pivot)) ** (contrast - 1.0))
    y = num / np.maximum(den, eps)
    y = y / (1.0 + 0.08 * np.maximum(0.0, y - 0.82))
    return np.clip(y, 0.0, 1.0)


def write_cube(path: str, title: str, lut_rgb: np.ndarray) -> None:
    size = lut_rgb.shape[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'TITLE "{title}"\n')
        f.write("# Created by grade <grade@agency.local> for MARK FIVE (grade-v06)\n")
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    rv, gv, bv = lut_rgb[b, g, r]
                    f.write(f"{rv:.6f} {gv:.6f} {bv:.6f}\n")


def build_all_luts(out_dir: str) -> None:
    vals = np.linspace(0.0, 1.0, 33, dtype=np.float32)
    b0, g0, r0 = np.meshgrid(vals, vals, vals, indexing="ij")
    lum0 = 0.2126 * r0 + 0.7152 * g0 + 0.0722 * b0

    red_dom = np.clip((r0 - np.maximum(g0, b0)) * 2.7, 0.0, 1.0)
    warm_dom = np.clip((r0 - b0) * 1.85, 0.0, 1.0) * np.clip((g0 - b0 * 0.62) * 1.6, 0.0, 1.0)
    sh_w = np.clip(1.0 - lum0 * 2.1, 0.0, 1.0) ** 1.4
    hi_w = np.clip((lum0 - 0.44) / 0.56, 0.0, 1.0)

    # 1. spillway_obsidian.cube (Shots 01, 03)
    r = filmic_scurve(r0, contrast=1.40, pivot=0.43, toe_crush=0.034)
    g = filmic_scurve(g0, contrast=1.37, pivot=0.42, toe_crush=0.030)
    b = filmic_scurve(b0, contrast=1.31, pivot=0.40, toe_crush=0.022)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    sat = 0.80 + 0.45 * np.maximum(red_dom, warm_dom)
    r = lum + (r - lum) * sat - 0.026 * sh_w * (1.0 - warm_dom) + 0.072 * red_dom
    g = lum + (g - lum) * sat - 0.005 * sh_w + 0.016 * hi_w * (1.0 - warm_dom)
    b = lum + (b - lum) * sat + 0.036 * sh_w * (1.0 - warm_dom) + 0.050 * hi_w * (1.0 - warm_dom)
    write_cube(os.path.join(out_dir, "spillway_obsidian.cube"), "GRADE_V06_SPILLWAY_OBSIDIAN", np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0))

    # 2. copper_bakelite.cube (Shots 02, 05 [Wall-Frame], 07)
    r = filmic_scurve(r0, contrast=1.43, pivot=0.42, toe_crush=0.034)
    g = filmic_scurve(g0, contrast=1.39, pivot=0.42, toe_crush=0.032)
    b = filmic_scurve(b0, contrast=1.34, pivot=0.41, toe_crush=0.024)
    cool_mask = 1.0 - np.clip(warm_dom * 1.38, 0.0, 1.0)
    r = r - 0.032 * sh_w * cool_mask + 0.088 * warm_dom * (0.42 + 0.58 * hi_w)
    g = g + 0.009 * sh_w * cool_mask + 0.038 * warm_dom * (0.32 + 0.68 * hi_w) + 0.022 * hi_w * cool_mask
    b = b + 0.048 * sh_w * cool_mask + 0.052 * hi_w * cool_mask - 0.046 * warm_dom
    write_cube(os.path.join(out_dir, "copper_bakelite.cube"), "GRADE_V06_COPPER_BAKELITE", np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0))

    # 3. cyan_skylight.cube (Shots 04, 06)
    r = filmic_scurve(r0, contrast=1.41, pivot=0.44, toe_crush=0.036)
    g = filmic_scurve(g0, contrast=1.37, pivot=0.41, toe_crush=0.028)
    b = filmic_scurve(b0, contrast=1.34, pivot=0.40, toe_crush=0.024)
    non_red = 1.0 - np.clip(red_dom * 1.65, 0.0, 1.0)
    r = r - 0.036 * non_red * (0.5 + 0.5 * sh_w) + 0.088 * red_dom
    g = g + 0.026 * non_red * (0.4 + 0.6 * hi_w) - 0.018 * red_dom
    b = b + 0.042 * non_red * (0.5 + 0.5 * hi_w) - 0.022 * red_dom
    write_cube(os.path.join(out_dir, "cyan_skylight.cube"), "GRADE_V06_CYAN_SKYLIGHT", np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0))

    # 4. ceiling_flood_6800k.cube (Shots 08, 09, 10)
    r = filmic_scurve(r0, contrast=1.44, pivot=0.43, toe_crush=0.035)
    g = filmic_scurve(g0, contrast=1.40, pivot=0.42, toe_crush=0.031)
    b = filmic_scurve(b0, contrast=1.32, pivot=0.39, toe_crush=0.020)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    keep_acc = np.clip(np.maximum(red_dom * 1.45, warm_dom * 0.88), 0.0, 1.0)
    r = (lum * 0.87 + r * 0.13) * (1.0 - keep_acc) + (r + 0.082 * red_dom) * keep_acc
    g = (lum * 0.96 + g * 0.04) * (1.0 - keep_acc) + g * keep_acc
    b = (lum * 1.15 + b * 0.10 + 0.032 * sh_w) * (1.0 - keep_acc) + b * keep_acc
    write_cube(os.path.join(out_dir, "ceiling_flood_6800k.cube"), "GRADE_V06_CEILING_FLOOD_6800K", np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0))


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")
    build_all_luts(target)
    print(f"Generated 4 33x33x33 .cube LUTs in {target}")
