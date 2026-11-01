#!/usr/bin/env python3
"""
Memory-lean (<220 MB RAM) 1080p30 cinema renderer for MARK FOUR (grade-v05).
Author: grade <grade@agency.local>

Renders each of the 11 shots sequentially into `/tmp/grade_v05_build/clips/clip_XX.mp4` (holding only one
plate in RAM at a time), applies 33x33x33 .cube 3D LUTs via trilinear interpolation, parallax storm rain,
practical halation, Shot 10's 52.44s booth-lamp snap-off, Shot 01's architectural title stamp, and all 39
word-boundary-locked 2-5 word caption beats, then muxes with `/tmp/grade_v05_build/master_audio_48k.wav`
into `videos/team-b/grade-v05/video.mp4` (+faststart, yuv420p, 48kHz stereo AAC) and saves `stills/`.
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
CLIPS_DIR = "/tmp/grade_v05_build/clips"
MASTER_WAV = "/tmp/grade_v05_build/master_audio_48k.wav"


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


def render_caption_overlay(tokens) -> tuple:
    font_path = find_font([
        "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
        "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ])
    font = ImageFont.truetype(font_path, 58)
    COLORS = {
        "ivory": (242, 245, 250),
        "amber": (245, 200, 75),
        "crimson": (232, 69, 60),
    }

    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    space_w = dummy.textlength(" ", font=font)
    widths = [dummy.textlength(txt, font=font) for txt, _ in tokens]
    total_w = sum(widths) + space_w * (len(tokens) - 1)

    pad_x = 34
    box_w = int(math.ceil(total_w + pad_x * 2))
    box_h = 98
    patch = Image.new("RGBA", (box_w + 24, box_h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)
    d.rounded_rectangle([12, 12, 12 + box_w, 12 + box_h], radius=18, fill=(5, 8, 15, 198), outline=(255, 255, 255, 26), width=1)
    patch = patch.filter(ImageFilter.GaussianBlur(0.5))
    d = ImageDraw.Draw(patch)

    cur_x = 12 + pad_x
    text_y = 28
    for (txt, role), w_px in zip(tokens, widths):
        col = COLORS[role]
        d.text((cur_x, text_y + 3), txt, font=font, fill=(0, 0, 0, 220), stroke_width=5, stroke_fill=(3, 5, 10, 220))
        d.text((cur_x, text_y), txt, font=font, fill=(*col, 255), stroke_width=3, stroke_fill=(4, 7, 13, 245))
        cur_x += w_px + space_w

    arr = (np.array(patch, dtype=np.float32) / 255.0)
    x0 = (W - arr.shape[1]) // 2
    y0 = 905
    return x0, y0, arr


def render_title_card() -> tuple:
    serif_path = find_font([
        "/usr/share/fonts/opentype/ebgaramond/EBGaramond12-Regular.otf",
        "/usr/share/fonts/opentype/ebgaramond/EBGaramond08-Regular.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
    ])
    sans_path = find_font([
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ])
    f_title = ImageFont.truetype(serif_path, 48)
    f_sub = ImageFont.truetype(sans_path, 17)

    patch = Image.new("RGBA", (620, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)
    d.text((8, 10), "M A R K   F O U R", font=f_title, fill=(242, 240, 234, 242), stroke_width=2, stroke_fill=(4, 7, 13, 190))
    d.line([(10, 74), (358, 74)], fill=(245, 200, 75, 185), width=2)
    d.text((10, 86), "02:17 AM   ·   BLACKWATER LOCK", font=f_sub, fill=(245, 200, 75, 232), stroke_width=2, stroke_fill=(4, 7, 13, 190))
    arr = (np.array(patch, dtype=np.float32) / 255.0)
    return 86, 68, arr


def prep_shot10_lit_plate(unlit_01: np.ndarray) -> np.ndarray:
    lit = unlit_01.copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    in_pane = (xx >= 1193) & (xx <= 1237) & (yy >= 209) & (yy <= 291)
    muntin = (np.abs(xx - 1215) <= 2) | (np.abs(yy - 248) <= 2)
    glass = np.where(in_pane & (~muntin), 1.0, 0.0).astype(np.float32)
    glass = np.array(Image.fromarray((glass * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4)), dtype=np.float32) / 255.0

    bulb_grad = np.exp(-(((xx - 1215.0) / 26.0) ** 2 + ((yy - 246.0) / 44.0) ** 2)).astype(np.float32)
    pane_glow = glass * (0.65 + 0.35 * bulb_grad)
    lit[:, :, 0] = lit[:, :, 0] * (1.0 - pane_glow * 0.85) + 0.98 * pane_glow
    lit[:, :, 1] = lit[:, :, 1] * (1.0 - pane_glow * 0.85) + 0.68 * pane_glow
    lit[:, :, 2] = lit[:, :, 2] * (1.0 - pane_glow * 0.85) + 0.20 * pane_glow

    d2 = ((xx - 1215.0) / 72.0) ** 2 + ((yy - 250.0) / 62.0) ** 2
    halo = np.exp(-0.5 * d2).astype(np.float32)
    lit[:, :, 0] += halo * 0.24
    lit[:, :, 1] += halo * 0.13
    lit[:, :, 2] += halo * 0.02

    spec = np.clip((unlit_01.mean(axis=2) - 0.32) / 0.45, 0.0, 1.0)
    path_zone = (np.exp(-((xx - 1155.0) / 145.0) ** 2) * np.exp(-((yy - 520.0) / 210.0) ** 2)).astype(np.float32)
    refl = spec * path_zone
    lit[:, :, 0] += refl * 0.30
    lit[:, :, 1] += refl * 0.17
    lit[:, :, 2] -= refl * 0.05
    return np.clip(lit, 0.0, 1.0).astype(np.float32)


SHOT_SPECS = {
    "01": ("blackwater_slate",  1.000, 1.072,  0.000,  0.008,  0.000, -0.006, 0.24),
    "02": ("blackwater_slate",  1.020, 1.085, -0.010,  0.008,  0.012, -0.010, 0.22),
    "03": ("blackwater_slate",  1.010, 1.075, -0.014,  0.012,  0.006, -0.006, 0.24),
    "04": ("amber_ledger",      1.000, 1.068, -0.008,  0.010,  0.008, -0.008, 0.00),
    "05": ("mercury_stillness", 1.005, 1.078,  0.010, -0.010,  0.000,  0.006, 0.22),
    "06": ("mercury_stillness", 1.015, 1.072, -0.012,  0.012, -0.005,  0.006, 0.07),
    "07": ("amber_ledger",      1.000, 1.066,  0.000,  0.000,  0.006, -0.008, 0.25),
    "08": ("amber_ledger",      1.010, 1.082, -0.010,  0.008, -0.010,  0.012, 0.19),
    "09": ("sluice_breach",     1.025, 1.095,  0.012, -0.008,  0.008, -0.010, 0.25),
    "10": ("sluice_breach",     1.005, 1.065,  0.006, -0.008,  0.008, -0.008, 0.26),
    "11": ("sluice_breach",     1.000, 1.082,  0.000,  0.006,  0.008, -0.010, 0.28),
}


def main():
    os.makedirs(STILLS_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    tl = json.load(open(os.path.join(TIMING_DIR, "timeline_locked.json")))
    cues = json.load(open(os.path.join(TIMING_DIR, "captions_locked.json")))
    shots = tl["shots"]

    luts = {
        name: load_cube_lut(os.path.join(LUTS_DIR, f"{name}.cube"))
        for name in ("blackwater_slate", "amber_ledger", "mercury_stillness", "sluice_breach")
    }

    rain_far = build_rain_tile(seed=701, density=0.00055, length=46, angle_deg=13.5, blur_r=0.7)
    rain_near = build_rain_tile(seed=702, density=0.00022, length=88, angle_deg=15.0, blur_r=1.2)
    tw, th = rain_far.shape[1], rain_far.shape[0]
    rain_col = np.array([0.66, 0.80, 0.98], dtype=np.float32)

    caption_patches = []
    for c in cues:
        x0, y0, rgba = render_caption_overlay(c["tokens"])
        caption_patches.append({
            "start": c["start"],
            "end": c["end"],
            "x0": x0,
            "y0": y0,
            "rgb": rgba[:, :, :3].copy(),
            "alpha": rgba[:, :, 3:4].copy(),
        })

    title_x0, title_y0, title_rgba = render_title_card()

    still_targets = {
        72:   "still_01_blackwater_hook.png",
        510:  "still_02_amber_ledger.png",
        1055: "still_03_poster_catwalk.png",
        1405: "still_04_unbolted_mark_four.png",
        1715: "still_05_sluice_already_open.png",
    }

    clip_paths = []

    for s in shots:
        sid = s["id"]
        lut_name, z0, z1, px0, px1, py0, py1, rain_amt = SHOT_SPECS[sid]
        raw_arr = np.array(Image.open(os.path.join(PLATES_DIR, f"shot_{sid}.jpg")).convert("RGB"), dtype=np.float32) / np.float32(255.0)

        # Precompute single-shot spatial halo only if needed
        halo = None
        if sid in ("04", "07", "11"):
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            if sid == "04":
                halo = np.exp(-(((xx - 1575.0) / 260.0) ** 2 + ((yy - 275.0) / 190.0) ** 2)).astype(np.float32)
            elif sid == "07":
                halo = np.exp(-(((xx - 1035.0) / 135.0) ** 2 + ((yy - 605.0) / 135.0) ** 2)).astype(np.float32)
            elif sid == "11":
                halo = np.exp(-(((xx - 1182.0) / 130.0) ** 2 + ((yy - 358.0) / 110.0) ** 2)).astype(np.float32)
            del xx, yy

        if sid == "10":
            lit_graded = apply_lut_trilinear(prep_shot10_lit_plate(raw_arr), luts[lut_name])
            off_graded = apply_lut_trilinear(raw_arr, luts[lut_name])
            pil_lit = Image.fromarray((lit_graded * 255.0 + 0.5).astype(np.uint8))
            pil_off = Image.fromarray((off_graded * 255.0 + 0.5).astype(np.uint8))
            del lit_graded, off_graded
        else:
            graded = apply_lut_trilinear(raw_arr, luts[lut_name])
            pil_single = Image.fromarray((graded * 255.0 + 0.5).astype(np.uint8))
            del graded
        del raw_arr
        gc.collect()

        clip_path = os.path.join(CLIPS_DIR, f"clip_{sid}.mp4")
        clip_paths.append(clip_path)

        # Use FFmpeg's C SIMD `noise=alls=4:allf=t+u` for organic 35mm grain and ultra-low-memory rc-lookahead=12
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
                if t < 52.433:
                    moved = pil_lit.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
                    frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)
                elif t < 52.490:
                    k = np.float32((t - 52.433) / 0.057)
                    m1 = np.array(pil_lit.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC), dtype=np.float32)
                    m2 = np.array(pil_off.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC), dtype=np.float32)
                    frame = (m1 * (1.0 - k) + m2 * k) * np.float32(1.0 / 255.0)
                else:
                    moved = pil_off.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
                    frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)
            else:
                moved = pil_single.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
                frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)

            # Practical halation breathing
            if sid == "04":
                p = np.float32(0.025 + 0.020 * math.sin(t * 3.1))
                frame[:, :, 0] += halo * p
                frame[:, :, 1] += halo * (p * np.float32(0.6))
            elif sid == "07":
                p = np.float32(0.048 + 0.018 * math.sin(t * 4.4) + 0.008 * math.sin(t * 11.3))
                frame[:, :, 0] += halo * (p * np.float32(1.15))
                frame[:, :, 1] += halo * (p * np.float32(0.65))
                frame[:, :, 2] += halo * (p * np.float32(0.10))
            elif sid == "11":
                bp = np.float32(0.055 * (0.5 + 0.5 * math.sin(2.0 * math.pi * 0.85 * t)))
                frame[:, :, 0] += halo * bp
                frame[:, :, 1] += halo * (bp * np.float32(0.12))
                frame[:, :, 2] += halo * (bp * np.float32(0.16))

            # Parallax storm rain sheets
            if rain_amt > 0.0:
                ox1 = int((f_idx * 19) % (tw - W))
                oy1 = int((-f_idx * 58) % (th - H))
                ox2 = int((f_idx * 33 + 310) % (tw - W))
                oy2 = int((-f_idx * 94 + 170) % (th - H))
                rt = (rain_far[oy1:oy1 + H, ox1:ox1 + W] * np.float32(0.62) + rain_near[oy2:oy2 + H, ox2:ox2 + W] * np.float32(0.85)) * np.float32(rain_amt)
                np.clip(frame, 0.0, 1.0, out=frame)
                frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - rt[:, :, None] * rain_col)
                if sid == "07":
                    wr = rt * halo * np.float32(1.35)
                    frame[:, :, 0] += wr * np.float32(0.55)
                    frame[:, :, 1] += wr * np.float32(0.32)

            np.clip(frame, 0.0, 1.0, out=frame)

            if sid == "07" and f_idx == 1055:
                p_u8 = (frame * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
                Image.fromarray(p_u8).save(os.path.join(STILLS_DIR, "poster_mark_four_clean.png"))

            # Opening title stamp on Shot 01 (0.55s -> 3.65s)
            if 0.55 <= t <= 3.65:
                t_alpha = np.float32(min(1.0, (t - 0.55) / 0.45, (3.65 - t) / 0.55))
                th_p, tw_p = title_rgba.shape[0], title_rgba.shape[1]
                a_t = title_rgba[:, :, 3:4] * t_alpha
                roi = frame[title_y0:title_y0 + th_p, title_x0:title_x0 + tw_p]
                frame[title_y0:title_y0 + th_p, title_x0:title_x0 + tw_p] = roi * (np.float32(1.0) - a_t) + title_rgba[:, :, :3] * a_t

            # 39 Word-Boundary-Locked 2-5 Word Caption Beats
            for cp in caption_patches:
                if cp["start"] - 0.02 <= t <= cp["end"] + 0.03:
                    c_alpha = np.float32(max(0.0, min(1.0, (t - (cp["start"] - 0.02)) / 0.055, ((cp["end"] + 0.03) - t) / 0.065)))
                    ch_p, cw_p = cp["rgb"].shape[0], cp["rgb"].shape[1]
                    x0, y0 = cp["x0"], cp["y0"]
                    a_c = cp["alpha"] * c_alpha
                    roi = frame[y0:y0 + ch_p, x0:x0 + cw_p]
                    frame[y0:y0 + ch_p, x0:x0 + cw_p] = roi * (np.float32(1.0) - a_c) + cp["rgb"] * a_c
                    break

            # Short <0.30s head/tail optical fades so zero black spans exceed 0.5s
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
            del pil_lit, pil_off
        else:
            del pil_single
        if halo is not None:
            del halo
        gc.collect()

    # Concatenate all 11 video clips + master 48kHz stereo WAV into final deliverable MP4
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
