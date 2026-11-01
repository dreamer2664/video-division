#!/usr/bin/env python3
"""
Procedural 33x33x33 .cube 3D LUT generator for MARK SEVEN (videos/team-b/grade-v08).
Implements the Division House Look 500T photochemical emulsion response:
  1. Power-toe shadow crush to obsidian black_floor = 0.004
  2. Steep logistic midtone S-curve + soft highlight shoulder roll-off
  3. Bimodal 2600K sodium/tungsten practical warmth vs 6500K-7000K storm-cyan gorge shadows
"""

import os
import numpy as np

LUT_SIZE = 33
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts")


def film_emulsion_curve(
    x: np.ndarray,
    toe_gamma: float = 1.62,
    toe_end: float = 0.20,
    slope: float = 7.4,
    pivot: float = 0.43,
    shoulder_start: float = 0.78,
    black_floor: float = 0.004,
    white_ceil: float = 0.985,
) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    s0 = 1.0 / (1.0 + np.exp(slope * pivot))
    s1 = 1.0 / (1.0 + np.exp(-slope * (1.0 - pivot)))
    sig = (1.0 / (1.0 + np.exp(-slope * (x - pivot))) - s0) / (s1 - s0)

    toe_w = np.clip(1.0 - x / max(toe_end, 1e-4), 0.0, 1.0) ** 2
    crushed = sig * (1.0 - 0.56 * toe_w) + (sig ** toe_gamma) * (0.56 * toe_w)

    hi_t = np.clip((x - shoulder_start) / max(1.0 - shoulder_start, 1e-4), 0.0, 1.0)
    rolled = crushed * (1.0 - 0.22 * (hi_t ** 1.5)) + np.sqrt(np.clip(crushed, 0.0, 1.0)) * (0.22 * (hi_t ** 1.5))
    return np.clip(black_floor + rolled * (white_ceil - black_floor), 0.0, 1.0)


def write_cube(path: str, title: str, fn) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    grid = np.linspace(0.0, 1.0, LUT_SIZE, dtype=np.float64)
    lines = [
        f'TITLE "{title}"',
        f"LUT_3D_SIZE {LUT_SIZE}",
        "DOMAIN_MIN 0.0 0.0 0.0",
        "DOMAIN_MAX 1.0 1.0 1.0",
    ]
    for b in grid:
        for g in grid:
            for r in grid:
                ro, go, bo = fn(r, g, b)
                lines.append(f"{ro:.6f} {go:.6f} {bo:.6f}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def lut_valley_obsidian_500t(r: float, g: float, b: float):
    """Shots 01, 05, 08 (Wall-Frame): Deep obsidian basalt & flooded Main Street mirror + 2600K amber practical."""
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    rc = float(film_emulsion_curve(r, toe_gamma=1.65, slope=7.5, pivot=0.43, black_floor=0.004))
    gc = float(film_emulsion_curve(g, toe_gamma=1.62, slope=7.3, pivot=0.43, black_floor=0.005))
    bc = float(film_emulsion_curve(b, toe_gamma=1.54, slope=7.0, pivot=0.42, black_floor=0.009))

    sh = (1.0 - lum) ** 1.85
    warm_src = max(0.0, r - 0.85 * b) * (lum ** 0.55)
    rc = rc * (1.0 - 0.17 * sh) + 0.14 * warm_src
    gc = gc * (1.0 + 0.02 * sh) + 0.05 * warm_src
    bc = bc * (1.0 + 0.20 * sh) + 0.025 * sh - 0.08 * warm_src

    lum2 = 0.2126 * rc + 0.7152 * gc + 0.0722 * bc
    sat = 0.88 + 0.18 * min(1.0, warm_src * 2.5)
    return (
        float(np.clip(lum2 + (rc - lum2) * sat, 0.0, 1.0)),
        float(np.clip(lum2 + (gc - lum2) * sat, 0.0, 1.0)),
        float(np.clip(lum2 + (bc - lum2) * sat, 0.0, 1.0)),
    )


def lut_gorge_cyan_6500k(r: float, g: float, b: float):
    """Shots 02, 07: Cold 6500K rail-yard & waterline rain ripples + crisp warm lantern reflection."""
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    rc = float(film_emulsion_curve(r, toe_gamma=1.66, slope=7.4, pivot=0.44, black_floor=0.004))
    gc = float(film_emulsion_curve(g, toe_gamma=1.58, slope=7.2, pivot=0.42, black_floor=0.006))
    bc = float(film_emulsion_curve(b, toe_gamma=1.50, slope=7.0, pivot=0.41, black_floor=0.011))

    sh = (1.0 - lum) ** 1.65
    warm_src = max(0.0, r - 0.88 * b) * (lum ** 0.60)
    rc = rc * (0.86 + 0.14 * lum) + 0.13 * warm_src
    gc = gc * 1.03 + 0.014 * sh + 0.05 * warm_src
    bc = bc * 1.13 + 0.028 * sh - 0.06 * warm_src

    lum2 = 0.2126 * rc + 0.7152 * gc + 0.0722 * bc
    return (
        float(np.clip(lum2 + (rc - lum2) * 0.88, 0.0, 1.0)),
        float(np.clip(lum2 + (gc - lum2) * 0.93, 0.0, 1.0)),
        float(np.clip(lum2 + (bc - lum2) * 0.98, 0.0, 1.0)),
    )


def lut_spillway_storm_7000k(r: float, g: float, b: float):
    """Shots 03, 04, 09: Exterior spillway plumes, steel truss bridge & 3-mile canyon storm mist."""
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    rc = float(film_emulsion_curve(r, toe_gamma=1.68, slope=7.6, pivot=0.43, black_floor=0.004))
    gc = float(film_emulsion_curve(g, toe_gamma=1.60, slope=7.4, pivot=0.42, black_floor=0.005))
    bc = float(film_emulsion_curve(b, toe_gamma=1.52, slope=7.2, pivot=0.41, black_floor=0.010))

    sh = (1.0 - lum) ** 1.75
    hi = lum ** 1.85
    warm_src = max(0.0, r - 0.86 * b) * (lum ** 0.55)
    rc = rc * (1.0 - 0.18 * sh) + 0.14 * warm_src
    gc = gc * (1.0 + 0.04 * hi) + 0.012 * sh + 0.05 * warm_src
    bc = bc * (1.0 + 0.14 * hi) + 0.026 * sh - 0.07 * warm_src
    return (float(np.clip(rc, 0.0, 1.0)), float(np.clip(gc, 0.0, 1.0)), float(np.clip(bc, 0.0, 1.0)))


def lut_lowgate_sodium_2600k(r: float, g: float, b: float):
    """Shots 06, 10: Evacuated brick levee stone & warm 2600K sodium harbor reflection."""
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    rc = float(film_emulsion_curve(r, toe_gamma=1.60, slope=7.3, pivot=0.42, black_floor=0.004))
    gc = float(film_emulsion_curve(g, toe_gamma=1.62, slope=7.2, pivot=0.43, black_floor=0.005))
    bc = float(film_emulsion_curve(b, toe_gamma=1.58, slope=7.0, pivot=0.44, black_floor=0.008))

    sh = (1.0 - lum) ** 1.80
    warm = (lum ** 0.75) * max(0.0, r - 0.78 * b + 0.14)
    rc = rc + 0.12 * warm - 0.03 * sh
    gc = gc + 0.04 * warm
    bc = bc - 0.07 * warm + 0.028 * sh
    return (float(np.clip(rc, 0.0, 1.0)), float(np.clip(gc, 0.0, 1.0)), float(np.clip(bc, 0.0, 1.0)))


def main() -> None:
    write_cube(os.path.join(OUT_DIR, "valley_obsidian_500t.cube"), "MARK SEVEN Valley Obsidian 500T", lut_valley_obsidian_500t)
    write_cube(os.path.join(OUT_DIR, "gorge_cyan_6500k.cube"), "MARK SEVEN Gorge Cyan 6500K", lut_gorge_cyan_6500k)
    write_cube(os.path.join(OUT_DIR, "spillway_storm_7000k.cube"), "MARK SEVEN Spillway Storm 7000K", lut_spillway_storm_7000k)
    write_cube(os.path.join(OUT_DIR, "lowgate_sodium_2600k.cube"), "MARK SEVEN Lowgate Sodium 2600K", lut_lowgate_sodium_2600k)
    print(f"Generated 4 500T film-emulsion 33x33x33 .cube LUTs in {OUT_DIR}")


if __name__ == "__main__":
    main()
