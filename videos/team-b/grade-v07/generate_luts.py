#!/usr/bin/env python3
"""
Generate four 500T film-emulsion 33x33x33 .cube 3D LUTs for MARK SIX (videos/team-b/grade-v07):
  1. vault_slate_4300k.cube   - Wet subterranean granite & slate room + 2600K storm lantern negative
  2. amber_oxide_reel.cube    - Warm 2550K ferric-oxide magnetic tape & VU glow vs 5800K shadow slate
  3. copper_cord_cyan.cube    - Cold 6500K rain-window cyan sheen across Bakelite & cast-brass horn
  4. surge_breach_7000k.cube  - Piercing 7000K xenon river searchlight & glacial floodwater breach
"""

import os
import numpy as np

LUT_SIZE = 33


def film_emulsion_curve(
    x: np.ndarray,
    contrast: float = 1.18,
    pivot: float = 0.44,
    steepness: float = 5.8,
    toe_crush: float = 0.055,
    black_floor: float = 0.004,
    shoulder: float = 0.11,
) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    toe_zone = np.clip(x / max(toe_crush, 1e-4), 0.0, 1.0)
    crushed = x * (0.38 + 0.62 * (toe_zone ** 1.35))

    centered = (crushed - pivot) * contrast + pivot
    s = 1.0 / (1.0 + np.exp(-steepness * (centered - 0.47)))
    s0 = 1.0 / (1.0 + np.exp(-steepness * (-0.47)))
    s1 = 1.0 / (1.0 + np.exp(-steepness * (0.53)))
    norm = (s - s0) / (s1 - s0)
    blended = 0.48 * crushed + 0.52 * norm

    rolled = blended / (1.0 + shoulder * np.maximum(0.0, blended - 0.70))
    return np.clip(black_floor + (1.0 - black_floor) * rolled, 0.0, 1.0)


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
    b, g, r = np.meshgrid(grid, grid, grid, indexing="ij")
    rgb = np.stack([r, g, b], axis=-1).reshape(-1, 3)
    out = np.clip(fn(rgb), 0.0, 1.0)
    for row in out:
        lines.append(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def lut_vault_slate(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    warm = np.clip((r - b) * 2.3, 0.0, 1.0) * np.clip(luma * 1.6, 0.0, 1.0)
    sh = np.clip(1.0 - luma * 2.2, 0.0, 1.0)
    return np.stack([
        film_emulsion_curve(r * (0.94 + 0.13 * warm) - 0.018 * sh, 1.18, black_floor=0.004),
        film_emulsion_curve(g * (0.99 + 0.03 * warm) + 0.006 * sh, 1.17, black_floor=0.005),
        film_emulsion_curve(b * (1.07 - 0.09 * warm) + 0.026 * sh, 1.15, black_floor=0.009),
    ], axis=-1)


def lut_amber_oxide(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    hi = np.clip((luma - 0.25) * 1.65, 0.0, 1.0)
    sh = np.clip(1.0 - luma * 2.3, 0.0, 1.0)
    return np.stack([
        film_emulsion_curve(r * (1.05 + 0.11 * hi) - 0.015 * sh, 1.20, black_floor=0.004),
        film_emulsion_curve(g * (0.98 + 0.02 * hi) + 0.004 * sh, 1.18, black_floor=0.005),
        film_emulsion_curve(b * (0.93 - 0.07 * hi) + 0.025 * sh, 1.14, black_floor=0.009),
    ], axis=-1)


def lut_copper_cord_cyan(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mid = np.exp(-((luma - 0.40) / 0.27) ** 2)
    return np.stack([
        film_emulsion_curve(r * 0.91 + 0.014 * mid, 1.19, black_floor=0.004),
        film_emulsion_curve(g * 1.02 + 0.022 * mid, 1.17, black_floor=0.006),
        film_emulsion_curve(b * 1.11 + 0.034 * mid, 1.16, black_floor=0.010),
    ], axis=-1)


def lut_surge_breach_7000k(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    guard = np.clip((r - b - 0.11) * 3.2, 0.0, 1.0)
    return np.stack([
        film_emulsion_curve(r * (0.87 + 0.18 * guard), 1.22, black_floor=0.003),
        film_emulsion_curve(g * 1.01, 1.20, black_floor=0.005),
        film_emulsion_curve(b * (1.14 - 0.09 * guard) + 0.016, 1.18, black_floor=0.009),
    ], axis=-1)


def main() -> None:
    lut_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")
    write_cube(os.path.join(lut_dir, "vault_slate_4300k.cube"), "GRADE_V07_VAULT_SLATE_500T", lut_vault_slate)
    write_cube(os.path.join(lut_dir, "amber_oxide_reel.cube"), "GRADE_V07_AMBER_OXIDE_500T", lut_amber_oxide)
    write_cube(os.path.join(lut_dir, "copper_cord_cyan.cube"), "GRADE_V07_COPPER_CORD_6500K", lut_copper_cord_cyan)
    write_cube(os.path.join(lut_dir, "surge_breach_7000k.cube"), "GRADE_V07_SURGE_BREACH_7000K", lut_surge_breach_7000k)
    print(f"Generated 4 500T film-emulsion 33x33x33 .cube LUTs in {lut_dir}", flush=True)


if __name__ == "__main__":
    main()
