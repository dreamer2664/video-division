#!/usr/bin/env python3
"""
Export an inspectable MLT XML non-linear project (`project/kelvin-v04.mlt`)
compatible with Shotcut, Kdenlive, and CLI `melt` (ATSC 1080p 30fps profile).
"""
import os

SHOT_SPECS = [
    ("01", "shot_01_raw.jpg", 135, "01_cold_slate_dusk.cube"),
    ("02", "shot_02_raw.jpg", 135, "01_cold_slate_dusk.cube"),
    ("03", "shot_03_raw.jpg", 135, "01_cold_slate_dusk.cube"),
    ("04", "shot_04_raw.jpg", 180, "02_sodium_amber.cube"),
    ("05", "shot_05_raw.jpg", 180, "02_sodium_amber.cube"),
    ("06", "shot_06_raw.jpg", 165, "02_sodium_amber.cube"),
    ("07", "shot_07_raw.jpg", 195, "03_mercury_storm.cube"),
    ("08", "shot_08_raw.jpg", 195, "03_mercury_storm.cube"),
    ("09", "shot_09_raw.jpg", 195, "03_mercury_storm.cube"),
    ("10", "shot_10_raw.jpg", 165, "04_silver_dawn.cube"),
    ("11", "shot_11_raw.jpg", 150, "04_silver_dawn.cube"),
    ("12", "shot_12_raw.jpg", 135, "04_silver_dawn.cube"),
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_mlt = os.path.join(here, "kelvin-v04.mlt")

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<mlt LC_NUMERIC="C" version="7.30.0" title="KELVIN — Four Temperatures of Night (grade-v04)" producer="main_bin">',
        '  <profile description="HD 1080p 30 fps" width="1920" height="1080" progressive="1" sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="16" display_aspect_den="9" frame_rate_num="30" frame_rate_den="1" colorspace="709"/>',
    ]

    for sid, plate, frames, lut in SHOT_SPECS:
        lines.extend([
            f'  <producer id="prod_shot_{sid}" in="0" out="{frames - 1}">',
            f'    <property name="resource">../assets/plates/{plate}</property>',
            f'    <property name="length">{frames}</property>',
            f'    <filter id="lut_shot_{sid}">',
            f'      <property name="mlt_service">avfilter.lut3d</property>',
            f'      <property name="av.file">../assets/luts/{lut}</property>',
            f'    </filter>',
            f'  </producer>',
        ])

    lines.append('  <playlist id="video_track_main">')
    for idx, (sid, _, frames, _) in enumerate(SHOT_SPECS):
        # Trim 15 overlap frames reflected in NLE A/B roll dissolve schedule -> 1800 frames total
        use_out = frames - 16 if idx < len(SHOT_SPECS) - 1 else frames - 1
        lines.append(f'    <entry producer="prod_shot_{sid}" in="0" out="{use_out}"/>')
    lines.append('  </playlist>')

    lines.extend([
        '  <tractor id="main_bin" in="0" out="1799">',
        '    <track producer="video_track_main"/>',
        '  </tractor>',
        '</mlt>',
    ])

    with open(out_mlt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote MLT timeline project: {out_mlt}")


if __name__ == "__main__":
    main()
