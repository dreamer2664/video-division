#!/usr/bin/env python3
"""
House Look 3D LUT Generator (33x33x33 .cube) — Video Division Standard.

Generates the four canonical nocturnal film-emulsion curves used across grade's films:
  1. house_obsidian_500t.cube         — Master wet-stone 500T negative (tight toe crush, steep S-curve,
                                        cyan-slate shadows vs preserved 2600K practical amber)
  2. house_amber_practical.cube       — Intimate tungsten/sodium practical room (2550K lamp core, rich
                                        ferric-gold midtones, deep 5800K shadow separation)
  3. house_cold_cyan_6500k.cube       — Cold storm-window & wet metallic instrument grade (6500K cyan
                                        glints, crisp steel/Bakelite specular roll-off)
  4. house_storm_searchlight_7000k.cube — High-tension exterior floodlight / storm reveal (7000K xenon
                                        slice, crushed obsidian storm night, protected red/amber gauges)

Usage:
    python3 look/generate_luts.py --out-dir look/luts
    python3 look/generate_luts.py --out-dir videos/team-a/pixel-v08/luts
"""

import argparse
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
    """
    Photochemical negative -> print transfer curve:
      1. Toe crush: pulls muddy digital shadows (< toe_crush) down cleanly toward black_floor (0.004)
         so dark scenes read as inked cinema negative rather than lifted grey LCD haze.
      2. Steep midtone logistic S-curve around `pivot`: separates wet stone micro-texture.
      3. Highlight shoulder compression (> 0.70): rolls off bright practical lamp cores smoothly
         instead of hard-clipping at 255.
    """
    x = np.clip(x, 0.0, 1.0)

    # 1. Power-toe crush in the bottom 8% of exposure
    toe_zone = np.clip(x / max(toe_crush, 1e-4), 0.0, 1.0)
    crushed = x * (0.38 + 0.62 * (toe_zone ** 1.35))

    # 2. Steep logistic S-curve in midtones
    centered = (crushed - pivot) * contrast + pivot
    s = 1.0 / (1.0 + np.exp(-steepness * (centered - 0.47)))
    s0 = 1.0 / (1.0 + np.exp(-steepness * (-0.47)))
    s1 = 1.0 / (1.0 + np.exp(-steepness * (0.53)))
    norm = (s - s0) / (s1 - s0)
    blended = 0.48 * crushed + 0.52 * norm

    # 3. Smooth highlight shoulder roll-off
    rolled = blended / (1.0 + shoulder * np.maximum(0.0, blended - 0.70))
    out = black_floor + (1.0 - black_floor) * rolled
    return np.clip(out, 0.0, 1.0)


def write_cube(filepath: str, title: str, transform_fn) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    grid = np.linspace(0.0, 1.0, LUT_SIZE, dtype=np.float32)
    lines = [
        f'TITLE "{title}"',
        f"LUT_3D_SIZE {LUT_SIZE}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
        "",
    ]
    # Standard .cube ordering: Red changes fastest, then Green, then Blue
    b, g, r = np.meshgrid(grid, grid, grid, indexing="ij")
    rgb = np.stack([r, g, b], axis=-1).reshape(-1, 3)
    mapped = np.clip(transform_fn(rgb), 0.0, 1.0)
    for row in mapped:
        lines.append(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def lut_house_obsidian_500t(rgb: np.ndarray) -> np.ndarray:
    """Master nocturnal wet-stone 500T negative: cold slate shadows + warm 2600K practical preservation."""
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    warm_practical = np.clip((r - b) * 2.3, 0.0, 1.0) * np.clip(luma * 1.6, 0.0, 1.0)
    deep_shadow = np.clip(1.0 - luma * 2.2, 0.0, 1.0)

    r_o = film_emulsion_curve(r * (0.94 + 0.13 * warm_practical) - 0.018 * deep_shadow, contrast=1.18, black_floor=0.004)
    g_o = film_emulsion_curve(g * (0.99 + 0.03 * warm_practical) + 0.006 * deep_shadow, contrast=1.17, black_floor=0.005)
    b_o = film_emulsion_curve(b * (1.07 - 0.09 * warm_practical) + 0.026 * deep_shadow, contrast=1.15, black_floor=0.009)
    return np.stack([r_o, g_o, b_o], axis=-1)


def lut_house_amber_practical(rgb: np.ndarray) -> np.ndarray:
    """Intimate tungsten/sodium practical grade (2550K lamp core vs 5800K shadow separation)."""
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    hi = np.clip((luma - 0.25) * 1.65, 0.0, 1.0)
    sh = np.clip(1.0 - luma * 2.3, 0.0, 1.0)

    r_o = film_emulsion_curve(r * (1.05 + 0.11 * hi) - 0.015 * sh, contrast=1.20, black_floor=0.004)
    g_o = film_emulsion_curve(g * (0.98 + 0.02 * hi) + 0.004 * sh, contrast=1.18, black_floor=0.005)
    b_o = film_emulsion_curve(b * (0.93 - 0.07 * hi) + 0.025 * sh, contrast=1.14, black_floor=0.009)
    return np.stack([r_o, g_o, b_o], axis=-1)


def lut_house_cold_cyan_6500k(rgb: np.ndarray) -> np.ndarray:
    """Cold 6500K rain-window & wet metallic instrument grade."""
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mid = np.exp(-((luma - 0.40) / 0.27) ** 2)

    r_o = film_emulsion_curve(r * 0.91 + 0.014 * mid, contrast=1.19, black_floor=0.004)
    g_o = film_emulsion_curve(g * 1.02 + 0.022 * mid, contrast=1.17, black_floor=0.006)
    b_o = film_emulsion_curve(b * 1.11 + 0.034 * mid, contrast=1.16, black_floor=0.010)
    return np.stack([r_o, g_o, b_o], axis=-1)


def lut_house_storm_searchlight_7000k(rgb: np.ndarray) -> np.ndarray:
    """High-tension 7000K exterior searchlight & storm floodwater grade (protects red/amber markings)."""
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    crimson_amber_guard = np.clip((r - b - 0.11) * 3.2, 0.0, 1.0)

    r_o = film_emulsion_curve(r * (0.87 + 0.18 * crimson_amber_guard), contrast=1.22, black_floor=0.003)
    g_o = film_emulsion_curve(g * 1.01, contrast=1.20, black_floor=0.005)
    b_o = film_emulsion_curve(b * (1.14 - 0.09 * crimson_amber_guard) + 0.016, contrast=1.18, black_floor=0.009)
    return np.stack([r_o, g_o, b_o], axis=-1)


HOUSE_LUTS = {
    "house_obsidian_500t": ("HOUSE_OBSIDIAN_500T", lut_house_obsidian_500t),
    "house_amber_practical": ("HOUSE_AMBER_PRACTICAL", lut_house_amber_practical),
    "house_cold_cyan_6500k": ("HOUSE_COLD_CYAN_6500K", lut_house_cold_cyan_6500k),
    "house_storm_searchlight_7000k": ("HOUSE_STORM_SEARCHLIGHT_7000K", lut_house_storm_searchlight_7000k),
}


def generate_all_luts(out_dir: str) -> list[str]:
    paths = []
    for slug, (title, fn) in HOUSE_LUTS.items():
        p = os.path.join(out_dir, f"{slug}.cube")
        write_cube(p, title, fn)
        paths.append(p)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the four Video Division House Look 33x33x33 .cube LUTs.")
    default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")
    parser.add_argument("--out-dir", default=default_dir, help="Directory to write .cube files into.")
    args = parser.parse_args()
    paths = generate_all_luts(args.out_dir)
    print(f"Generated {len(paths)} House Look 33x33x33 .cube LUTs in {args.out_dir}:")
    for p in paths:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
