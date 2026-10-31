#!/usr/bin/env python3
"""
Memory-lean (<220 MB RAM) 1080p30 cinema renderer for MARK FIVE (grade-v06).
Author: grade <grade@agency.local>

Applies four bespoke 33x33x33 .cube 3D LUTs via trilinear interpolation, smooth sub-pixel camera moves,
parallax storm rain (including vertical oculus rain shafts in Shot 05), diegetic line-lamp modulation on
Shot 02, lantern dim-out on Shot 10, opening architectural title card, and 40 word-boundary-locked two-voice
captions (Speaker A Keeper left-offset amber/ivory; Speaker B Copper Line right-offset cyan/ice/crimson).
"""

import gc
import json
import math
import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = 1800

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES_DIR = os.path.join(HERE, "plates")
LUTS_DIR = os.path.join(HERE, "luts")
TIMING_DIR = os.path.join(HERE, "timing")
STILLS_DIR = os.path.join(HERE, "stills")
OUT_MP4 = os.path.join(HERE, "video.mp4")
CLIPS_DIR = "/tmp/grade_v06_build/clips"
MASTER_WAV = "/tmp/grade_v06_build/master_audio_48k.wav"


def find_font(candidates: list[str]) -> str:
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"None of {candidates} found")


def load_cube_lut(path: str) -> np.ndarray:
    rows = []
    size = 33
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("TITLE") or s.startswith("DOMAIN"):
                continue
            if s.startswith("LUT_3D_SIZE"):
                size = int(s.split()[1])
                continue
            parts = s.split()
            if len(parts) == 3:
                rows.append((float(parts[0]), float(parts[1]), float(parts[2])))
    arr = np.array(rows, dtype=np.float32).reshape((size, size, size, 3))
    return np.transpose(arr, (2, 1, 0, 3)).copy()


def apply_lut_trilinear(img01: np.ndarray, lut: np.ndarray) -> np.ndarray:
    n = lut.shape[0] - 1
    scaled = np.clip(img01, 0.0, 1.0) * np.float32(n)
    idx0 = np.clip(np.floor(scaled).astype(np.int32), 0, n - 1)
    idx1 = idx0 + 1
    fr = (scaled - idx0).astype(np.float32)

    r0, g0, b0 = idx0[:, :, 0], idx0[:, :, 1], idx0[:, :, 2]
    r1, g1, b1 = idx1[:, :, 0], idx1[:, :, 1], idx1[:, :, 2]
    dr, dg, db = fr[:, :, 0:1], fr[:, :, 1:2], fr[:, :, 2:3]

    c00 = lut[r0, g0, b0] * (1.0 - dr) + lut[r1, g0, b0] * dr
    c01 = lut[r0, g0, b1] * (1.0 - dr) + lut[r1, g0, b1] * dr
    c10 = lut[r0, g1, b0] * (1.0 - dr) + lut[r1, g1, b0] * dr
    c11 = lut[r0, g1, b1] * (1.0 - dr) + lut[r1, g1, b1] * dr

    c0 = c00 * (1.0 - dg) + c10 * dg
    c1 = c01 * (1.0 - dg) + c11 * dg
    return np.clip(c0 * (1.0 - db) + c1 * db, 0.0, 1.0).astype(np.float32)


def build_rain_tile(seed: int, density: float, length: int, angle_deg: float, blur_r: float) -> np.ndarray:
    tw, th = 2240, 1360
    rng = np.random.default_rng(seed)
    canvas = Image.new("L", (tw, th), 0)
    draw = ImageDraw.Draw(canvas)
    rad = math.radians(angle_deg)
    dx = math.sin(rad) * length
    dy = math.cos(rad) * length
    for _ in range(int(tw * th * density)):
        x0 = rng.uniform(-80, tw + 80)
        y0 = rng.uniform(-80, th + 80)
        bright = int(rng.uniform(95, 245))
        width = 1 if rng.random() < 0.78 else 2
        for ox in (-tw, 0, tw):
            for oy in (-th, 0, th):
                sx, sy = x0 + ox, y0 + oy
                if -length <= sx <= tw + length and -length <= sy <= th + length:
                    draw.line([(sx, sy), (sx + dx, sy + dy)], fill=bright, width=width)
    if blur_r > 0:
        canvas = canvas.filter(ImageFilter.GaussianBlur(blur_r))
    return (np.array(canvas, dtype=np.float32) / 255.0)


def render_caption_overlay(tokens, speaker: str) -> tuple:
    """
    Two-voice visual caption differentiation:
      - Speaker A (Narrator/Keeper): shifted slightly left (-56 px), amber left accent bar, ivory/amber/crimson text.
      - Speaker B (Responder/Copper Line): shifted slightly right (+56 px), cyan right signal bar + 'LINE ·' micro-tag, ice/cyan/crimson text.
    """
    font_main = ImageFont.truetype(find_font([
        "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
        "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]), 54)
    font_tag = ImageFont.truetype(find_font([
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]), 22)

    COLORS = {
        "ivory": (242, 245, 250),
        "amber": (245, 200, 75),
        "ice": (228, 242, 255),
        "cyan": (106, 210, 255),
        "crimson": (234, 68, 60),
    }

    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    space_w = dummy.textlength(" ", font=font_main)
    widths = [dummy.textlength(txt, font=font_main) for txt, _ in tokens]
    text_w = sum(widths) + space_w * (len(tokens) - 1)

    tag_str = "LINE · " if speaker == "B" else ""
    tag_w = dummy.textlength(tag_str, font=font_tag) + 10 if speaker == "B" else 0

    pad_x = 34
    box_w = int(math.ceil(tag_w + text_w + pad_x * 2))
    box_h = 94
    patch = Image.new("RGBA", (box_w + 24, box_h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)

    bg_col = (5, 8, 15, 202) if speaker == "A" else (6, 13, 24, 208)
    border_col = (245, 200, 75, 55) if speaker == "A" else (106, 210, 255, 70)
    d.rounded_rectangle([12, 12, 12 + box_w, 12 + box_h], radius=16, fill=bg_col, outline=border_col, width=1)

    # Distinct stereo-matching edge bar (Left amber bar for Voice A; Right cyan bar for Voice B)
    if speaker == "A":
        d.rounded_rectangle([12, 24, 17, 12 + box_h - 12], radius=2, fill=(245, 200, 75, 235))
    else:
        d.rounded_rectangle([12 + box_w - 5, 24, 12 + box_w, 12 + box_h - 12], radius=2, fill=(106, 210, 255, 235))

    cur_x = 12 + pad_x
    if speaker == "B":
        d.text((cur_x, 46), "LINE ·", font=font_tag, fill=(106, 210, 255, 235), stroke_width=2, stroke_fill=(3, 6, 12, 230))
        cur_x += tag_w

    text_y = 26
    for (txt, role), w_px in zip(tokens, widths):
        col = COLORS[role]
        d.text((cur_x, text_y + 3), txt, font=font_main, fill=(0, 0, 0, 220), stroke_width=5, stroke_fill=(3, 5, 10, 220))
        d.text((cur_x, text_y), txt, font=font_main, fill=(*col, 255), stroke_width=3, stroke_fill=(4, 7, 13, 245))
        cur_x += w_px + space_w

    arr = (np.array(patch, dtype=np.float32) / 255.0)
    pan_shift = -58 if speaker == "A" else +58
    x0 = max(32, min(W - arr.shape[1] - 32, (W - arr.shape[1]) // 2 + pan_shift))
    y0 = 908
    return x0, y0, arr


def render_title_card() -> tuple:
    f_title = ImageFont.truetype(find_font([
        "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Regular.otf",
        "/usr/share/fonts/opentype/ebgaramond/EBGaramond08-Regular.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
    ]), 48)
    f_sub = ImageFont.truetype(find_font([
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]), 17)

    patch = Image.new("RGBA", (660, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)
    d.text((8, 10), "M A R K   F I V E", font=f_title, fill=(242, 240, 234, 242), stroke_width=2, stroke_fill=(4, 7, 13, 190))
    d.line([(10, 74), (372, 74)], fill=(245, 200, 75, 185), width=2)
    d.text((10, 86), "02:24 AM   ·   LOWER BASIN SPILLWAY", font=f_sub, fill=(245, 200, 75, 232), stroke_width=2, stroke_fill=(4, 7, 13, 190))
    arr = (np.array(patch, dtype=np.float32) / 255.0)
    return 86, 68, arr


def prep_shot10_dimmed_plate(raw_01: np.ndarray) -> np.ndarray:
    """Create the cold 6800K dimmed-lantern state of Shot 10 for Turn 10 ('It marks how high your tower fills.')."""
    dim = raw_01.copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # Cool down & dim the lower warm lantern glow while keeping the crimson 'MARK V' ceiling stencil legible!
    red_stencil = np.clip((dim[:, :, 0] - np.maximum(dim[:, :, 1], dim[:, :, 2])) * 2.6, 0.0, 1.0) * np.clip((680.0 - yy) / 140.0, 0.0, 1.0)
    warm_glow = np.clip((dim[:, :, 0] - dim[:, :, 2]) * 1.6, 0.0, 1.0) * (1.0 - red_stencil)
    lum = 0.2126 * dim[:, :, 0] + 0.7152 * dim[:, :, 1] + 0.0722 * dim[:, :, 2]

    cool_r = lum * 0.34
    cool_g = lum * 0.48
    cool_b = lum * 0.78
    k = np.clip(warm_glow * 0.92 + 0.28 * (1.0 - red_stencil), 0.0, 0.92)
    dim[:, :, 0] = dim[:, :, 0] * (1.0 - k) + cool_r * k + red_stencil * 0.08
    dim[:, :, 1] = dim[:, :, 1] * (1.0 - k) + cool_g * k
    dim[:, :, 2] = dim[:, :, 2] * (1.0 - k) + cool_b * k
    return np.clip(dim, 0.0, 1.0).astype(np.float32)


# (lut_name, z0, z1, px0, px1, py0, py1, rain_amt)
SHOT_SPECS = {
    "01": ("spillway_obsidian",   1.000, 1.072,  0.000,  0.006,  0.006, -0.008, 0.25),
    "02": ("copper_bakelite",     1.005, 1.075, -0.008,  0.010,  0.004, -0.004, 0.00),
    "03": ("spillway_obsidian",   1.015, 1.082,  0.008, -0.008,  0.010, -0.010, 0.24),
    "04": ("cyan_skylight",       1.005, 1.072, -0.010,  0.010,  0.000,  0.006, 0.00),
    "05": ("copper_bakelite",     1.000, 1.066,  0.000,  0.000,  0.008, -0.008, 0.18),  # Symmetrical Wall-Frame!
    "06": ("cyan_skylight",       1.010, 1.078,  0.000,  0.004,  0.008, -0.008, 0.08),
    "07": ("copper_bakelite",     1.010, 1.080, -0.010,  0.010, -0.008,  0.012, 0.00),
    "08": ("ceiling_flood_6800k", 1.015, 1.085, -0.010,  0.010,  0.006, -0.006, 0.26),
    "09": ("ceiling_flood_6800k", 1.000, 1.062,  0.000, -0.006,  0.006, -0.006, 0.26),
    "10": ("ceiling_flood_6800k", 1.045, 1.088,  0.000,  0.000,  0.020, -0.020, 0.05),  # Upward ceiling reveal!
}


def main():
    os.makedirs(STILLS_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    tl = json.load(open(os.path.join(TIMING_DIR, "timeline_locked.json")))
    cues = json.load(open(os.path.join(TIMING_DIR, "captions_locked.json")))
    shots = tl["shots"]

    luts = {
        name: load_cube_lut(os.path.join(LUTS_DIR, f"{name}.cube"))
        for name in ("spillway_obsidian", "copper_bakelite", "cyan_skylight", "ceiling_flood_6800k")
    }

    rain_diag_far = build_rain_tile(seed=801, density=0.00055, length=46, angle_deg=13.0, blur_r=0.7)
    rain_diag_near = build_rain_tile(seed=802, density=0.00022, length=88, angle_deg=14.5, blur_r=1.2)
    rain_vert = build_rain_tile(seed=803, density=0.00050, length=74, angle_deg=1.5, blur_r=0.9)
    tw, th = rain_diag_far.shape[1], rain_diag_far.shape[0]
    rain_col = np.array([0.66, 0.80, 0.98], dtype=np.float32)

    caption_patches = []
    for c in cues:
        x0, y0, rgba = render_caption_overlay(c["tokens"], c["speaker"])
        caption_patches.append({
            "start": c["start"],
            "end": c["end"],
            "speaker": c["speaker"],
            "x0": x0,
            "y0": y0,
            "rgb": rgba[:, :, :3].copy(),
            "alpha": rgba[:, :, 3:4].copy(),
        })

    title_x0, title_y0, title_rgba = render_title_card()

    still_targets = {
        75:   "still_01_spillway_hook.png",          # 2.50s — Shot 01 hook + title stamp
        365:  "still_02_copper_handset_line.png",    # 12.17s — Shot 02 Responder B LINE caption
        875:  "still_03_oculus_wall_frame.png",      # 29.17s — Shot 05 Wall-Frame composition
        1335: "still_04_rooftop_field_set.png",      # 44.50s — Shot 08 The Turn (alligator clips on stub)
        1635: "still_05_ceiling_mark_five.png",      # 54.50s — Shot 10 MARK V stenciled on ceiling
    }

    clip_paths = []

    for s in shots:
        sid = s["id"]
        lut_name, z0, z1, px0, px1, py0, py1, rain_amt = SHOT_SPECS[sid]
        raw_arr = np.array(Image.open(os.path.join(PLATES_DIR, f"shot_{sid}.jpg")).convert("RGB"), dtype=np.float32) / np.float32(255.0)

        halo = None
        oculus_col = None
        if sid in ("02", "05"):
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            if sid == "02":
                halo = np.exp(-(((xx - 1207.0) / 85.0) ** 2 + ((yy - 500.0) / 85.0) ** 2)).astype(np.float32)
            elif sid == "05":
                halo = np.exp(-(((xx - 1036.0) / 145.0) ** 2 + ((yy - 616.0) / 145.0) ** 2)).astype(np.float32)
                oculus_col = (np.exp(-((xx - 960.0) / 215.0) ** 2) * np.clip((920.0 - yy) / 240.0, 0.0, 1.0)).astype(np.float32)
            del xx, yy

        if sid == "10":
            lit_g = apply_lut_trilinear(raw_arr, luts[lut_name])
            dim_g = apply_lut_trilinear(prep_shot10_dimmed_plate(raw_arr), luts[lut_name])
            pil_lit = Image.fromarray((lit_g * 255.0 + 0.5).astype(np.uint8))
            pil_dim = Image.fromarray((dim_g * 255.0 + 0.5).astype(np.uint8))
            del lit_g, dim_g
        else:
            graded = apply_lut_trilinear(raw_arr, luts[lut_name])
            pil_single = Image.fromarray((graded * 255.0 + 0.5).astype(np.uint8))
            del graded
        del raw_arr
        gc.collect()

        clip_path = os.path.join(CLIPS_DIR, f"clip_{sid}.mp4")
        clip_paths.append(clip_path)

        ff_clip = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
            "-i", "-",
            "-vf", "noise=alls=4:allf=t+u",
            "-c:v", "libx264", "-preset", "fast", "-crf", "14",
            "-x264-params", "rc-lookahead=12:threads=2",
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            clip_path,
        ]
        proc = subprocess.Popen(ff_clip, stdin=subprocess.PIPE)

        for f_idx in range(s["start_frame"], s["end_frame"]):
            t = f_idx / FPS
            u = (f_idx - s["start_frame"]) / max(s["frames"] - 1, 1)
            u_smooth = 0.35 * (0.5 - 0.5 * math.cos(math.pi * u)) + 0.65 * u

            zoom = z0 + (z1 - z0) * u_smooth
            px = px0 + (px1 - px0) * u_smooth
            py = py0 + (py1 - py0) * u_smooth

            cw, ch = W / zoom, H / zoom
            cx, cy = (W * 0.5) + px * W, (H * 0.5) + py * H
            bx0 = max(0.0, min(W - cw, cx - cw * 0.5))
            by0 = max(0.0, min(H - ch, cy - ch * 0.5))

            if sid == "10":
                # Smoothly dim lantern between 56.15s and 56.75s as Responder B keys in for the final line!
                if t <= 56.15:
                    moved = pil_lit.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
                    frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)
                elif t < 56.75:
                    k = np.float32((t - 56.15) / 0.60)
                    m1 = np.array(pil_lit.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC), dtype=np.float32)
                    m2 = np.array(pil_dim.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC), dtype=np.float32)
                    frame = (m1 * (1.0 - k) + m2 * k) * np.float32(1.0 / 255.0)
                else:
                    moved = pil_dim.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
                    frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)
            else:
                moved = pil_single.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
                frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)

            # Practical lighting events
            if sid == "02":
                # Line-active neon bulb pulses brightly when Responder B speaks (10.75s - 15.39s)!
                if 10.70 <= t <= 15.42:
                    mod = np.float32(0.065 + 0.045 * abs(math.sin(t * 14.5)) * (0.5 + 0.5 * math.sin(t * 5.2)))
                else:
                    mod = np.float32(0.015)
                frame[:, :, 0] += halo * mod * np.float32(1.2)
                frame[:, :, 1] += halo * mod * np.float32(0.65)
            elif sid == "05":
                p = np.float32(0.046 + 0.016 * math.sin(t * 4.1) + 0.007 * math.sin(t * 10.7))
                frame[:, :, 0] += halo * (p * np.float32(1.15))
                frame[:, :, 1] += halo * (p * np.float32(0.66))
                frame[:, :, 2] += halo * (p * np.float32(0.10))

            # Rain sheets (vertical oculus shaft in Shot 05; diagonal storm sheets outside)
            if rain_amt > 0.0:
                if sid == "05":
                    ox = int((f_idx * 3) % (tw - W))
                    oy = int((-f_idx * 72) % (th - H))
                    rv = rain_vert[oy:oy + H, ox:ox + W] * oculus_col * np.float32(rain_amt * 1.45)
                    np.clip(frame, 0.0, 1.0, out=frame)
                    frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - rv[:, :, None] * np.array([0.85, 0.88, 0.96], dtype=np.float32))
                    wr = rv * halo * np.float32(1.4)
                    frame[:, :, 0] += wr * np.float32(0.55)
                    frame[:, :, 1] += wr * np.float32(0.32)
                else:
                    ox1 = int((f_idx * 19) % (tw - W))
                    oy1 = int((-f_idx * 58) % (th - H))
                    ox2 = int((f_idx * 33 + 310) % (tw - W))
                    oy2 = int((-f_idx * 94 + 170) % (th - H))
                    rt = (rain_diag_far[oy1:oy1 + H, ox1:ox1 + W] * np.float32(0.62) + rain_diag_near[oy2:oy2 + H, ox2:ox2 + W] * np.float32(0.85)) * np.float32(rain_amt)
                    np.clip(frame, 0.0, 1.0, out=frame)
                    frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - rt[:, :, None] * rain_col)

            np.clip(frame, 0.0, 1.0, out=frame)

            # Save clean uncaptioned Wall-Frame gallery print on Shot 05!
            if sid == "05" and f_idx == 875:
                p_u8 = (frame * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
                Image.fromarray(p_u8).save(os.path.join(STILLS_DIR, "wall_frame_mark_five_clean.png"))

            # Opening architectural title card on Shot 01 (0.55s -> 3.65s)
            if 0.55 <= t <= 3.65:
                t_alpha = np.float32(min(1.0, (t - 0.55) / 0.45, (3.65 - t) / 0.55))
                th_p, tw_p = title_rgba.shape[0], title_rgba.shape[1]
                a_t = title_rgba[:, :, 3:4] * t_alpha
                roi = frame[title_y0:title_y0 + th_p, title_x0:title_x0 + tw_p]
                frame[title_y0:title_y0 + th_p, title_x0:title_x0 + tw_p] = roi * (np.float32(1.0) - a_t) + title_rgba[:, :, :3] * a_t

            # 40 Two-Voice Word-Boundary-Locked Caption Beats
            for cp in caption_patches:
                if cp["start"] - 0.02 <= t <= cp["end"] + 0.03:
                    c_alpha = np.float32(max(0.0, min(1.0, (t - (cp["start"] - 0.02)) / 0.055, ((cp["end"] + 0.03) - t) / 0.065)))
                    ch_p, cw_p = cp["rgb"].shape[0], cp["rgb"].shape[1]
                    x0, y0 = cp["x0"], cp["y0"]
                    a_c = cp["alpha"] * c_alpha
                    roi = frame[y0:y0 + ch_p, x0:x0 + cw_p]
                    frame[y0:y0 + ch_p, x0:x0 + cw_p] = roi * (np.float32(1.0) - a_c) + cp["rgb"] * a_c
                    break

            # Short <= 0.30s head/tail fades so zero black spans exceed 0.5s
            if t < 0.27:
                frame *= np.float32(max(0.04, t / 0.27))
            elif t > 59.70:
                frame *= np.float32(max(0.04, (60.0 - t) / 0.30))

            out_u8 = (np.clip(frame, 0.0, 1.0) * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
            proc.stdin.write(out_u8.tobytes())

            if f_idx in still_targets:
                Image.fromarray(out_u8).save(os.path.join(STILLS_DIR, still_targets[f_idx]))

        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"Shot {sid} ffmpeg failed with {rc}")
        print(f"  Completed Shot {sid} ({s['frames']}f -> {clip_path})")

        if sid == "10":
            del pil_lit, pil_dim
        else:
            del pil_single
        if halo is not None:
            del halo
        if oculus_col is not None:
            del oculus_col
        gc.collect()

    concat_txt = os.path.join(CLIPS_DIR, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{cp}'\n")

    print(f"Muxing final 60.000s master -> {OUT_MP4}...")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", concat_txt,
            "-i", MASTER_WAV,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "22",
            "-maxrate", "4000k", "-bufsize", "8000k",
            "-x264-params", "rc-lookahead=18:threads=2",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
            "-r", str(FPS), "-vsync", "cfr",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            OUT_MP4,
        ],
        check=True,
    )
    print(f"Successfully rendered {OUT_MP4}")


if __name__ == "__main__":
    main()
