#!/usr/bin/env python3
"""
Generate four 33x33x33 Adobe/Resolve-standard .cube 3D LUTs for KELVIN (grade-v04).
Each LUT implements smooth filmic toe/shoulder roll-off and Kelvin-specific split-toning.
"""
import os
import numpy as np

LUT_SIZE = 33


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def filmic_curve(rgb, contrast=1.08, pivot=0.45, toe_lift=0.012, shoulder_max=0.985):
    x = np.clip(rgb, 0.0, 1.0)
    # S-curve around pivot in log-ish gamma domain
    centered = x - pivot
    y = pivot + centered * contrast / (1.0 + np.abs(centered) * (contrast - 1.0) * 1.35)
    y = np.clip(y, 0.0, 1.0)
    return toe_lift + y * (shoulder_max - toe_lift)


def adjust_saturation(rgb, sat):
    luma = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    return np.clip(luma[..., None] + (rgb - luma[..., None]) * sat, 0.0, 1.0)


def build_grid():
    lin = np.linspace(0.0, 1.0, LUT_SIZE, dtype=np.float64)
    # .cube order: B outer, G middle, R inner
    b, g, r = np.meshgrid(lin, lin, lin, indexing="ij")
    return np.stack([r, g, b], axis=-1)


def lut_01_cold_slate_dusk(rgb):
    """5600K -> 3800K: cool steel-slate twilight while preserving warm tungsten beacon/lamp jewels."""
    y = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    warm_mask = smoothstep(0.04, 0.22, rgb[..., 0] - rgb[..., 2]) * smoothstep(0.18, 0.65, y)

    base = filmic_curve(rgb, contrast=1.12, pivot=0.42, toe_lift=0.016, shoulder_max=0.975)
    cooled = adjust_saturation(base, 0.84)

    sh_w = 1.0 - smoothstep(0.0, 0.55, y)
    mid_w = smoothstep(0.12, 0.50, y) * (1.0 - smoothstep(0.55, 0.95, y))

    cooled[..., 0] += -0.032 * sh_w - 0.020 * mid_w
    cooled[..., 1] += -0.006 * sh_w + 0.005 * mid_w
    cooled[..., 2] += +0.048 * sh_w + 0.036 * mid_w

    # Let warm practicals (lighthouse beam, distant road lamps) glow rich amber
    warm = base.copy()
    warm[..., 0] = np.clip(warm[..., 0] * 1.10 + 0.035, 0.0, 1.0)
    warm[..., 1] = np.clip(warm[..., 1] * 1.01 + 0.008, 0.0, 1.0)
    warm[..., 2] = np.clip(warm[..., 2] * 0.80, 0.0, 1.0)

    out = cooled * (1.0 - warm_mask[..., None]) + warm * warm_mask[..., None]
    return np.clip(out, 0.0, 1.0)


def lut_02_sodium_amber(rgb):
    """2100K Low-Pressure Sodium: Prussian-blue shadows + rich sodium-amber midtones/highlights."""
    y = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    base = filmic_curve(rgb, contrast=1.16, pivot=0.40, toe_lift=0.015, shoulder_max=0.975)
    desat = adjust_saturation(base, 0.78)

    sh_w = 1.0 - smoothstep(0.02, 0.36, y)
    amber_w = smoothstep(0.16, 0.72, y)
    hi_w = smoothstep(0.68, 0.98, y)

    out = desat.copy()
    # Prussian-blue deep shadow bed
    out[..., 0] += -0.036 * sh_w + 0.125 * amber_w + 0.020 * hi_w
    out[..., 1] += +0.004 * sh_w + 0.032 * amber_w + 0.015 * hi_w
    out[..., 2] += +0.058 * sh_w - 0.135 * amber_w - 0.040 * hi_w
    return np.clip(out, 0.0, 1.0)


def lut_03_mercury_storm(rgb):
    """4200K Mercury-Halide Storm: Cold cyan-emerald industrial steel + boosted crimson warning beacons."""
    y = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    red_chroma = rgb[..., 0] - np.maximum(rgb[..., 1], rgb[..., 2])
    beacon_mask = smoothstep(0.08, 0.26, red_chroma) * smoothstep(0.12, 0.55, rgb[..., 0])

    base = filmic_curve(rgb, contrast=1.20, pivot=0.44, toe_lift=0.014, shoulder_max=0.985)
    storm = adjust_saturation(base, 0.88)

    sh_w = 1.0 - smoothstep(0.0, 0.45, y)
    mid_w = smoothstep(0.15, 0.80, y)

    storm[..., 0] += -0.042 * sh_w - 0.048 * mid_w
    storm[..., 1] += +0.012 * sh_w + 0.032 * mid_w
    storm[..., 2] += +0.048 * sh_w + 0.044 * mid_w

    # Preserve and intensify crimson warning lights & warm watchtower practicals
    crimson = base.copy()
    crimson[..., 0] = np.clip(crimson[..., 0] * 1.16 + 0.04, 0.0, 1.0)
    crimson[..., 1] = np.clip(crimson[..., 1] * 0.92, 0.0, 1.0)
    crimson[..., 2] = np.clip(crimson[..., 2] * 0.86, 0.0, 1.0)

    out = storm * (1.0 - beacon_mask[..., None]) + crimson * beacon_mask[..., None]
    return np.clip(out, 0.0, 1.0)


def lut_04_silver_dawn(rgb):
    """6500K Silver Dawn: Clean bleach-silver calm water opening into luminous pale-rose daylight."""
    y = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    base = filmic_curve(rgb, contrast=1.06, pivot=0.48, toe_lift=0.022, shoulder_max=0.990)
    silver = adjust_saturation(base, 0.76)

    sh_w = 1.0 - smoothstep(0.0, 0.48, y)
    hi_w = smoothstep(0.45, 0.92, y)

    silver[..., 0] += -0.012 * sh_w + 0.026 * hi_w
    silver[..., 1] += +0.004 * sh_w + 0.010 * hi_w
    silver[..., 2] += +0.024 * sh_w + 0.018 * hi_w
    return np.clip(silver, 0.0, 1.0)


def write_cube(path, title, table):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    flat = table.reshape(-1, 3)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'TITLE "{title}"\n')
        f.write(f"LUT_3D_SIZE {LUT_SIZE}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        np.savetxt(f, flat, fmt="%.6f %.6f %.6f")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    luts_dir = os.path.abspath(os.path.join(here, "..", "assets", "luts"))
    grid = build_grid()

    # Self-check grid ordering: at b=0, g=0, r=1 -> index 1 must have R>0, G==0, B==0
    flat_id = grid.reshape(-1, 3)
    assert flat_id[1, 0] > 0 and flat_id[1, 1] == 0 and flat_id[1, 2] == 0, "Invalid .cube axis order!"

    specs = [
        ("01_cold_slate_dusk.cube", "KELVIN 01 - 5600K-3800K Cold Slate Dusk", lut_01_cold_slate_dusk(grid)),
        ("02_sodium_amber.cube", "KELVIN 02 - 2100K Sodium Amber Split", lut_02_sodium_amber(grid)),
        ("03_mercury_storm.cube", "KELVIN 03 - 4200K Mercury Storm & Crimson", lut_03_mercury_storm(grid)),
        ("04_silver_dawn.cube", "KELVIN 04 - 6500K Bleach Silver Dawn", lut_04_silver_dawn(grid)),
    ]
    for fname, title, tbl in specs:
        out_path = os.path.join(luts_dir, fname)
        write_cube(out_path, title, tbl)
        print(f"Wrote {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")


if __name__ == "__main__":
    main()
