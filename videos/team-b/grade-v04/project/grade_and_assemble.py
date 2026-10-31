#!/usr/bin/env python3
"""
Team B Visual Colour-Grading, Slow-Motion Camera/Atmosphere & Editorial Assembly Engine
for KELVIN (grade-v04).

Pipeline per shot (isolated subprocess -> peak RSS <= 680 MiB in 2 GB sandbox):
  1. Load neutral plate (assets/plates/shot_XX_raw.jpg), supersample to 4320x2430 (Lanczos 2.25x)
     for sub-pixel smooth `zoompan` camera choreography at 1920x1080 @ 30.00 fps.
  2. Convert to planar RGB (`gbrp`) for colorist-accurate grading:
     - Apply 33x33x33 `.cube` 3D LUT (`lut3d`)
     - Apply per-shot tonal/split-tone RGB `curves` trim
     - Composite slow-motion optical overlay (`ov_rain_slow`, `ov_mist_drift`, `ov_warm_halation`,
       `ov_water_shimmer`) using RGB `blend` (`screen` or `softlight`).
     - Shot 07 executes a live diagonal colourist wipe (`blend` expression) from flat ungraded
       silver-grey harbour fog into full 4200K mercury-cyan & crimson beacon grade.
  3. Convert to `yuv420p`, add subtle optical `vignette` and organic 35mm luma grain (`noise`),
     encode near-lossless intermediate (`-crf 13`).
  4. Assemble 4 act reels -> master 60.000s timeline via 11 x 0.50s filmic dissolves (`xfade`),
     burn >=44px high-contrast typography (`ass=assets/captions.ass`), mux 48kHz stereo AAC
     mastered to -16.0 LUFS integrated / <= -1.5 dBTP true peak with `+faststart`.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

FPS = 30
TRANS_DUR = 0.50  # 15 frames per transition x 11 transitions = 5.50s overlap -> 65.50 - 5.50 = 60.000s


SHOTS = [
    {
        "id": "01",
        "dur": 4.50,  # timeline 00.00 - 04.00s
        "plate": "shot_01_raw.jpg",
        "lut": "01_cold_slate_dusk.cube",
        # Smooth low-angle forward dolly along wet basalt pier
        "zp_z": "1.02 + 0.10*(on/{N})",
        "zp_x": "(iw - iw/zoom)*0.50",
        "zp_y": "(ih - ih/zoom)*(0.62 - 0.14*(on/{N}))",
        "curves": "r='0/0.02 0.35/0.29 0.75/0.72 1/0.96':g='0/0.03 0.35/0.33 0.75/0.76 1/0.97':b='0/0.05 0.35/0.39 0.75/0.82 1/0.99'",
        "overlay": "ov_water_shimmer.mp4",
        "blend_mode": "screen",
        "blend_op": 0.17,
        "extra_fade_in": True,
    },
    {
        "id": "02",
        "dur": 4.50,  # timeline 04.00 - 08.00s
        "plate": "shot_02_raw.jpg",
        "lut": "01_cold_slate_dusk.cube",
        # Slow lateral drift + push toward glowing lighthouse lantern
        "zp_z": "1.03 + 0.09*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.40 + 0.20*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.46 - 0.08*(on/{N}))",
        "curves": "r='0/0.01 0.30/0.26 0.70/0.74 1/0.98':g='0/0.02 0.30/0.28 0.70/0.72 1/0.96':b='0/0.05 0.30/0.35 0.70/0.75 1/0.95'",
        "overlay": "ov_warm_halation.mp4",
        "blend_mode": "screen",
        "blend_op": 0.24,
    },
    {
        "id": "03",
        "dur": 4.50,  # timeline 08.00 - 12.00s
        "plate": "shot_03_raw.jpg",
        "lut": "01_cold_slate_dusk.cube",
        # Slow crane pull-back revealing curving coastal road & waking distant lamps
        "zp_z": "1.13 - 0.10*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.56 - 0.14*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.44 + 0.10*(on/{N}))",
        "curves": "r='0/0.01 0.35/0.28 0.72/0.71 1/0.97':g='0/0.02 0.35/0.31 0.72/0.72 1/0.96':b='0/0.05 0.35/0.38 0.72/0.78 1/0.97'",
        "overlay": "ov_mist_drift.mp4",
        "blend_mode": "screen",
        "blend_op": 0.20,
    },
    {
        "id": "04",
        "dur": 6.00,  # timeline 12.00 - 17.50s (2100K Sodium Vapour)
        "plate": "shot_04_raw.jpg",
        "lut": "02_sodium_amber.cube",
        # Steady glide through wet brick viaduct arch under glowing sodium lamps
        "zp_z": "1.02 + 0.13*(on/{N})",
        "zp_x": "(iw - iw/zoom)*0.50",
        "zp_y": "(ih - ih/zoom)*(0.54 - 0.08*(on/{N}))",
        "curves": "r='0/0.01 0.25/0.22 0.62/0.72 1/0.99':g='0/0.02 0.25/0.19 0.62/0.58 1/0.93':b='0/0.05 0.25/0.20 0.62/0.38 1/0.78'",
        "overlay": "ov_rain_slow.mp4",
        "blend_mode": "screen",
        "blend_op": 0.24,
    },
    {
        "id": "05",
        "dur": 6.00,  # timeline 17.50 - 23.00s
        "plate": "shot_05_raw.jpg",
        "lut": "02_sodium_amber.cube",
        # Slow pan across wet dark ferry deck toward warm rain-beaded cabin window
        "zp_z": "1.05 + 0.08*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.32 + 0.34*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.50 - 0.06*(on/{N}))",
        "curves": "r='0/0.01 0.22/0.18 0.65/0.74 1/0.99':g='0/0.02 0.22/0.19 0.65/0.63 1/0.95':b='0/0.05 0.22/0.25 0.65/0.46 1/0.82'",
        "overlay": "ov_rain_slow.mp4",
        "blend_mode": "screen",
        "blend_op": 0.21,
    },
    {
        "id": "06",
        "dur": 5.50,  # timeline 23.00 - 28.00s
        "plate": "shot_06_raw.jpg",
        "lut": "02_sodium_amber.cube",
        # Slow macro pull-back from wet iron bollard & harbour bokeh reflections
        "zp_z": "1.15 - 0.11*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.62 - 0.20*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.58 - 0.14*(on/{N}))",
        "curves": "r='0/0.01 0.20/0.15 0.65/0.73 1/0.99':g='0/0.02 0.20/0.17 0.65/0.62 1/0.95':b='0/0.06 0.20/0.26 0.65/0.50 1/0.86'",
        "overlay": "ov_water_shimmer.mp4",
        "blend_mode": "screen",
        "blend_op": 0.18,
    },
    {
        "id": "07",
        "dur": 6.50,  # timeline 28.00 - 34.00s (4200K Live Dynamic Grade Sweep!)
        "plate": "shot_07_raw.jpg",
        "lut": "03_mercury_storm.cube",
        "dynamic_wipe": True,
        # Monumental upward tilt & push into fogbound gantry cranes
        "zp_z": "1.02 + 0.12*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.44 + 0.14*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.62 - 0.24*(on/{N}))",
        "curves": "r='0/0.01 0.30/0.21 0.70/0.64 1/0.97':g='0/0.02 0.30/0.30 0.70/0.74 1/0.98':b='0/0.05 0.30/0.34 0.70/0.79 1/0.99'",
        "overlay": "ov_mist_drift.mp4",
        "blend_mode": "screen",
        "blend_op": 0.22,
    },
    {
        "id": "08",
        "dur": 6.50,  # timeline 34.00 - 40.00s (Slow-motion wave explosion)
        "plate": "shot_08_raw.jpg",
        "lut": "03_mercury_storm.cube",
        # Dramatic slow-motion push into suspended ocean spray crest
        "zp_z": "1.02 + 0.14*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.48 + 0.10*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.56 - 0.18*(on/{N}))",
        "curves": "r='0/0.01 0.28/0.20 0.72/0.68 1/0.98':g='0/0.02 0.28/0.28 0.72/0.75 1/0.99':b='0/0.05 0.28/0.33 0.72/0.80 1/1.00'",
        "overlay": "ov_rain_slow.mp4",
        "blend_mode": "screen",
        "blend_op": 0.26,
    },
    {
        "id": "09",
        "dur": 6.50,  # timeline 40.00 - 46.00s (Watchtower in squall climax)
        "plate": "shot_09_raw.jpg",
        "lut": "03_mercury_storm.cube",
        # Push toward glowing coastal watchtower glass against dark storm sky
        "zp_z": "1.02 + 0.13*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.46 - 0.12*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.52 - 0.08*(on/{N}))",
        "curves": "r='0/0.01 0.26/0.19 0.68/0.66 1/0.98':g='0/0.02 0.26/0.27 0.68/0.73 1/0.98':b='0/0.05 0.26/0.32 0.68/0.76 1/0.98'",
        "overlay": "ov_rain_slow.mp4",
        "blend_mode": "screen",
        "blend_op": 0.28,
    },
    {
        "id": "10",
        "dur": 5.50,  # timeline 46.00 - 51.00s (6500K Silver Dawn jetty)
        "plate": "shot_10_raw.jpg",
        "lut": "04_silver_dawn.cube",
        # Serene horizon glide across mirror-still foggy jetty
        "zp_z": "1.09 - 0.06*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.62 - 0.24*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.54 - 0.06*(on/{N}))",
        "curves": "r='0/0.02 0.35/0.35 0.75/0.78 1/0.99':g='0/0.02 0.35/0.36 0.75/0.78 1/0.99':b='0/0.04 0.35/0.39 0.75/0.81 1/1.00'",
        "overlay": "ov_water_shimmer.mp4",
        "blend_mode": "softlight",
        "blend_op": 0.22,
    },
    {
        "id": "11",
        "dur": 5.00,  # timeline 51.00 - 55.50s (Solitary ship on silver glass sea)
        "plate": "shot_11_raw.jpg",
        "lut": "04_silver_dawn.cube",
        # Gentle expansive pull-back over calm silver sea mist
        "zp_z": "1.12 - 0.09*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.45 + 0.12*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*0.50",
        "curves": "r='0/0.02 0.40/0.42 0.78/0.81 1/0.99':g='0/0.02 0.40/0.41 0.78/0.80 1/0.99':b='0/0.04 0.40/0.44 0.78/0.83 1/1.00'",
        "overlay": "ov_mist_drift.mp4",
        "blend_mode": "softlight",
        "blend_op": 0.22,
    },
    {
        "id": "12",
        "dur": 4.50,  # timeline 55.50 - 60.00s (Headland daylight ocean resolution)
        "plate": "shot_12_raw.jpg",
        "lut": "04_silver_dawn.cube",
        # Slow luminous forward float out toward parting coastal fog & daylight ocean
        "zp_z": "1.02 + 0.09*(on/{N})",
        "zp_x": "(iw - iw/zoom)*(0.55 - 0.15*(on/{N}))",
        "zp_y": "(ih - ih/zoom)*(0.48 - 0.08*(on/{N}))",
        "curves": "r='0/0.02 0.38/0.40 0.76/0.80 1/0.99':g='0/0.02 0.38/0.39 0.76/0.79 1/0.99':b='0/0.03 0.38/0.41 0.76/0.81 1/1.00'",
        "overlay": "ov_mist_drift.mp4",
        "blend_mode": "screen",
        "blend_op": 0.16,
        "extra_fade_out": True,
    },
]


def run_cmd(cmd, desc=""):
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.time() - t0
    if res.returncode != 0:
        sys.stderr.write(f"ERROR in {desc}:\n{' '.join(cmd)}\n{res.stderr}\n")
        sys.exit(1)
    return dt, res.stderr


def render_single_shot(shot, base_dir, build_dir):
    sid = shot["id"]
    dur = shot["dur"]
    frames = int(round(dur * FPS))
    n_minus_1 = max(frames - 1, 1)

    plate_path = os.path.join(base_dir, "assets", "plates", shot["plate"])
    lut_path = os.path.join(base_dir, "assets", "luts", shot["lut"])
    ov_path = os.path.join(build_dir, "overlays", shot["overlay"])
    out_clip = os.path.join(build_dir, "shots", f"shot_{sid}.mp4")
    os.makedirs(os.path.dirname(out_clip), exist_ok=True)

    zp_z = shot["zp_z"].format(N=n_minus_1)
    zp_x = shot["zp_x"].format(N=n_minus_1)
    zp_y = shot["zp_y"].format(N=n_minus_1)

    zp_chain = (
        f"[0:v]scale=4320:2430:flags=lanczos,"
        f"zoompan=z='{zp_z}':x='{zp_x}':y='{zp_y}':d={frames}:s=1920x1080:fps={FPS},"
        f"setsar=1,format=gbrp"
    )

    inputs = ["-i", plate_path, "-i", ov_path]

    if shot.get("dynamic_wipe"):
        # Shot 07: SIMD maskedmerge live diagonal colourist wipe from flat log mist -> 4200K mercury storm grade
        matte_path = os.path.join(build_dir, "overlays", "ov_wipe_matte.mp4")
        inputs.extend(["-i", matte_path])
        grade_chain = (
            f"{zp_chain},split=2[raw_a][raw_b];"
            f"[raw_a]lut3d=file='{lut_path}',curves={shot['curves']},format=gbrp[graded];"
            f"[raw_b]curves=all='0/0.07 0.5/0.52 1/0.90',format=gbrp[logflat];"
            f"[2:v]trim=0:{dur},setpts=PTS-STARTPTS,format=gbrp[matte];"
            f"[logflat][graded][matte]maskedmerge[pre_ov];"
        )
    else:
        grade_chain = (
            f"{zp_chain},lut3d=file='{lut_path}',curves={shot['curves']},format=gbrp[pre_ov];"
        )

    ov_chain = f"[1:v]trim=0:{dur},setpts=PTS-STARTPTS,format=gbrp[ov];"
    post_filters = ["scale=out_color_matrix=bt709:out_range=tv", "format=yuv420p", "vignette=PI/5.6", "noise=c0s=3:c0f=t+u"]
    if shot.get("extra_fade_in"):
        # 0.28s gentle rise (strictly < 0.5s, never black)
        post_filters.append("fade=t=in:st=0:d=0.28:color=#0a1018")
    if shot.get("extra_fade_out"):
        # 0.28s gentle twilight settle at very tail (strictly < 0.5s, never black/frozen)
        post_filters.append(f"fade=t=out:st={dur - 0.28:.2f}:d=0.28:color=#101620")

    full_graph = (
        grade_chain
        + ov_chain
        + f"[pre_ov][ov]blend=all_mode={shot['blend_mode']}:all_opacity={shot['blend_op']},"
        + ",".join(post_filters)
        + "[vout]"
    )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", full_graph,
        "-map", "[vout]",
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
        out_clip,
    ]
    dt, _ = run_cmd(cmd, f"Shot {sid}")
    print(f"  Rendered Shot {sid} ({dur:.2f}s, {frames}f) in {dt:.1f}s -> {os.path.getsize(out_clip)/1024:.0f} KB")
    return out_clip


def xfade_group(clips, durs, out_path, transitions=None):
    """Join a small group of clips (3 or 4) with 0.50s dissolves (< 320 MB RSS)."""
    inputs = []
    for c in clips:
        inputs.extend(["-i", c])

    n = len(clips)
    if transitions is None:
        transitions = ["fade"] * (n - 1)

    fc_parts = []
    cum_dur = durs[0]
    prev_label = "[0:v]"
    for idx in range(1, n):
        offset = round(cum_dur - TRANS_DUR, 4)
        out_lbl = f"[v{idx}]"
        tr = transitions[idx - 1]
        fc_parts.append(
            f"{prev_label}[{idx}:v]xfade=transition={tr}:duration={TRANS_DUR}:offset={offset}{out_lbl}"
        )
        cum_dur = round(cum_dur + durs[idx] - TRANS_DUR, 4)
        prev_label = out_lbl

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", ";".join(fc_parts),
        "-map", prev_label,
        "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
        out_path,
    ]
    dt, _ = run_cmd(cmd, f"xfade -> {os.path.basename(out_path)}")
    return cum_dur, dt


def measure_loudnorm_mp4(mp4_path):
    res = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", mp4_path,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True, text=True, check=True,
    )
    m = re.search(r"\{[\s\S]*?\}", res.stderr)
    return json.loads(m.group(0))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(here, ".."))
    build_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/grade_v04_build"
    os.makedirs(build_dir, exist_ok=True)

    print("=== Stage 2: Per-Shot Colour Grading (.cube 3D LUT + curves) & Slow-Motion Compositing ===")
    rendered_clips = []
    for shot in SHOTS:
        rendered_clips.append(render_single_shot(shot, base_dir, build_dir))

    print("=== Stage 3: Chunked Act-Reel Editorial Dissolves (<= 320 MB RSS) ===")
    reels_dir = os.path.join(build_dir, "reels")
    os.makedirs(reels_dir, exist_ok=True)

    act_defs = [
        ("act1.mp4", rendered_clips[0:3], [s["dur"] for s in SHOTS[0:3]], ["fade", "fade"]),
        ("act2a.mp4", rendered_clips[3:6], [s["dur"] for s in SHOTS[3:6]], ["fade", "fade"]),
        ("act2b.mp4", rendered_clips[6:9], [s["dur"] for s in SHOTS[6:9]], ["fade", "fade"]),
        ("act3.mp4", rendered_clips[9:12], [s["dur"] for s in SHOTS[9:12]], ["fade", "fade"]),
    ]
    act_paths, act_durs = [], []
    for rname, rclips, rdurs, rtrs in act_defs:
        rpath = os.path.join(reels_dir, rname)
        cdur, dt = xfade_group(rclips, rdurs, rpath, rtrs)
        act_paths.append(rpath)
        act_durs.append(cdur)
        print(f"  Assembled {rname}: {cdur:.2f}s in {dt:.1f}s")

    master_unsub = os.path.join(build_dir, "master_visual_unsub.mp4")
    total_dur, dt_m = xfade_group(act_paths, act_durs, master_unsub, ["fade", "fade", "fade"])
    print(f"  Assembled master timeline: {total_dur:.3f}s in {dt_m:.1f}s")

    print("=== Stage 4: Burn High-Contrast >=44px Typography (libass) & Mux 48kHz Stereo AAC ===")
    ass_path = os.path.join(base_dir, "assets", "captions.ass")
    audio_wav = os.path.join(build_dir, "audio_master_48k.wav")
    out_mp4 = os.path.join(base_dir, "video.mp4")

    cmd_final = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", master_unsub,
        "-i", audio_wav,
        "-vf", f"ass=filename='{ass_path}',scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-level", "4.1",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", "60.000",
        "-movflags", "+faststart",
        out_mp4,
    ]
    dt_f, _ = run_cmd(cmd_final, "Final master encode")
    print(f"  Encoded initial video.mp4 in {dt_f:.1f}s ({os.path.getsize(out_mp4)/(1024*1024):.2f} MB)")

    # Verify post-AAC integrated loudness & apply exact linear trim if AAC drifted > 0.08 LUFS from -16.0
    stats = measure_loudnorm_mp4(out_mp4)
    meas_i = float(stats["input_i"])
    meas_tp = float(stats["input_tp"])
    print(f"  Post-AAC check: I={meas_i:.2f} LUFS, TP={meas_tp:.2f} dBTP")
    delta_db = -16.0 - meas_i
    if abs(delta_db) > 0.08 or meas_tp + delta_db > -1.1:
        safe_delta = min(delta_db, -1.25 - meas_tp)
        trimmed_mp4 = os.path.join(build_dir, "video_loudtrim.mp4")
        run_cmd(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", out_mp4,
                "-c:v", "copy",
                "-af", f"volume={safe_delta:.3f}dB",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart",
                trimmed_mp4,
            ],
            "Post-AAC exact LUFS trim",
        )
        shutil.move(trimmed_mp4, out_mp4)
        stats2 = measure_loudnorm_mp4(out_mp4)
        print(f"  Trimmed post-AAC: I={float(stats2['input_i']):.2f} LUFS, TP={float(stats2['input_tp']):.2f} dBTP")


if __name__ == "__main__":
    main()
