#!/usr/bin/env python3
"""
Generate four bespoke 33x33x33 .cube 3D LUTs for MARK SIX (videos/team-b/grade-v07):
  1. vault_slate_4300k.cube   - Wet subterranean granite & slate room + 2600K storm lantern split
  2. amber_oxide_reel.cube    - Warm 2550K ferric-oxide magnetic tape & VU glow vs 5800K shadow slate
  3. copper_cord_cyan.cube    - Cold 6400K rain-window cyan sheen across Bakelite & cast-brass horn
  4. surge_breach_7000k.cube  - Piercing 7000K xenon river searchlight & glacial floodwater breach
"""

import os
import numpy as np

LUT_SIZE = 33


def filmic_curve(x: np.ndarray, contrast: float, toe: float, shoulder: float) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    centered = (x - 0.44) * contrast + 0.44
    s = 1.0 / (1.0 + np.exp(-5.4 * (centered - 0.48)))
    s0 = 1.0 / (1.0 + np.exp(-5.4 * (-0.48)))
    s1 = 1.0 / (1.0 + np.exp(-5.4 * (0.52)))
    norm = (s - s0) / (s1 - s0)
    blended = 0.60 * x + 0.40 * norm
    compressed = blended / (1.0 + shoulder * np.maximum(0.0, blended - 0.72))
    lifted = toe + (1.0 - toe) * compressed
    return np.clip(lifted, 0.0, 1.0)


def write_cube(filepath: str, title: str, fn) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    grid = np.linspace(0.0, 1.0, LUT_SIZE, dtype=np.float32)
    lines = [
        f'TITLE "{title}"',
        f"LUT_3D_SIZE {LUT_SIZE}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]
    # Adobe/FFmpeg .cube order: R fastest, then G, then B
    b, g, r = np.meshgrid(grid, grid, grid, indexing="ij")
    rgb = np.stack([r, g, b], axis=-1).reshape(-1, 3)
    out = np.clip(fn(rgb), 0.0, 1.0)
    for row in out:
        lines.append(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}")
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")


def lut_vault_slate(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    warm_mask = np.clip((r - b) * 2.2, 0.0, 1.0) * np.clip(luma * 1.5, 0.0, 1.0)
    sh_mask = np.clip(1.0 - luma * 1.9, 0.0, 1.0)

    r_o = filmic_curve(r * (0.95 + 0.11 * warm_mask) - 0.015 * sh_mask, 1.12, 0.012, 0.08)
    g_o = filmic_curve(g * (0.99 + 0.03 * warm_mask) + 0.008 * sh_mask, 1.11, 0.014, 0.08)
    b_o = filmic_curve(b * (1.06 - 0.08 * warm_mask) + 0.028 * sh_mask, 1.10, 0.018, 0.07)
    return np.stack([r_o, g_o, b_o], axis=-1)


def lut_amber_oxide(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    hi = np.clip((luma - 0.28) * 1.6, 0.0, 1.0)
    sh = np.clip(1.0 - luma * 2.1, 0.0, 1.0)

    r_o = filmic_curve(r * (1.04 + 0.10 * hi) - 0.012 * sh, 1.15, 0.011, 0.09)
    g_o = filmic_curve(g * (0.98 + 0.02 * hi) + 0.004 * sh, 1.13, 0.013, 0.09)
    b_o = filmic_curve(b * (0.94 - 0.06 * hi) + 0.026 * sh, 1.10, 0.017, 0.08)
    return np.stack([r_o, g_o, b_o], axis=-1)


def lut_copper_cord_cyan(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mid = np.exp(-((luma - 0.42) / 0.28) ** 2)

    r_o = filmic_curve(r * 0.92 + 0.015 * mid, 1.14, 0.011, 0.08)
    g_o = filmic_curve(g * 1.02 + 0.022 * mid, 1.13, 0.014, 0.08)
    b_o = filmic_curve(b * 1.10 + 0.032 * mid, 1.12, 0.019, 0.07)
    return np.stack([r_o, g_o, b_o], axis=-1)


def lut_surge_breach_7000k(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    amber_keep = np.clip((r - b - 0.12) * 3.0, 0.0, 1.0)

    r_o = filmic_curve(r * (0.88 + 0.16 * amber_keep), 1.18, 0.010, 0.09)
    g_o = filmic_curve(g * 1.01, 1.16, 0.013, 0.08)
    b_o = filmic_curve(b * (1.13 - 0.08 * amber_keep) + 0.018, 1.15, 0.018, 0.07)
    return np.stack([r_o, g_o, b_o], axis=-1)


def main() -> None:
    lut_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")
    write_cube(os.path.join(lut_dir, "vault_slate_4300k.cube"), "GRADE_V07_VAULT_SLATE_4300K", lut_vault_slate)
    write_cube(os.path.join(lut_dir, "amber_oxide_reel.cube"), "GRADE_V07_AMBER_OXIDE_REEL", lut_amber_oxide)
    write_cube(os.path.join(lut_dir, "copper_cord_cyan.cube"), "GRADE_V07_COPPER_CORD_CYAN", lut_copper_cord_cyan)
    write_cube(os.path.join(lut_dir, "surge_breach_7000k.cube"), "GRADE_V07_SURGE_BREACH_7000K", lut_surge_breach_7000k)
    print(f"Generated 4 bespoke 33x33x33 .cube LUTs in {lut_dir}")


if __name__ == "__main__":
    main()
