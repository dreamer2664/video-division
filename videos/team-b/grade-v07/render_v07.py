#!/usr/bin/env python3
"""
Memory-lean (<220 MB RAM) 1080p30 cinema renderer for MARK SIX (videos/team-b/grade-v07).

Applies four bespoke 33x33x33 .cube 3D LUTs via trilinear interpolation, smooth sub-pixel camera motion,
multi-plane optical storm rain, diegetic transducer light modulation (VHF carrier LED on Shot 03, analog VU
meter glow on Shot 06, hydraulic shear-bolt flash on Shot 09), opening architectural title card, and 40
WordBoundary-locked three-voice spatially-coded captions:
  - Voice A [REEL] : Left-shifted (-88 px), warm 2600K amber bar
  - Voice C [HORN] : Dead-center  (  0 px), seafoam VHF signal bar
  - Voice B [LINE] : Right-shifted (+88 px), cold 6800K cyan bar
"""

import gc
import hashlib
import json
import math
import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile

W, H = 1920, 1080
FPS = 30
TOTAL_FRAMES = 1800

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES_DIR = os.path.join(HERE, "plates")
LUTS_DIR = os.path.join(HERE, "luts")
TIMING_DIR = os.path.join(HERE, "timing")
AUDIO_DIR = os.path.join(HERE, "audio")
STILLS_DIR = os.path.join(HERE, "stills")
OUT_MP4 = os.path.join(HERE, "video.mp4")
CLIPS_DIR = "/tmp/grade_v07_build/clips"
MASTER_WAV = "/tmp/grade_v07_build/master_audio_48k.wav"


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
    return np.array(canvas, dtype=np.float32) / 255.0


def tokenize_cue(text: str, speaker: str) -> list[tuple[str, str]]:
    base_role = {"A": "ivory", "B": "ice", "C": "mint"}[speaker]
    out = []
    for w in text.split():
        clean = w.upper().strip(".,?!;:")
        if clean in ("MARK", "SIX"):
            out.append((w, "crimson" if clean == "SIX" else "amber"))
        elif clean in ("2:37", "AM", "EMPTY", "SURGE", "CHAMBER", "FLOOD", "BOLTS", "FIRED", "NOBODY"):
            out.append((w, {"A": "amber", "B": "cyan", "C": "seafoam"}[speaker]))
        else:
            out.append((w, base_role))
    return out


def render_caption_overlay(text: str, speaker: str) -> tuple:
    font_main = ImageFont.truetype(find_font([
        "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
        "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]), 50)
    font_tag = ImageFont.truetype(find_font([
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]), 21)

    COLORS = {
        "ivory": (244, 245, 248),
        "ice": (228, 242, 255),
        "mint": (232, 248, 242),
        "amber": (248, 198, 74),
        "cyan": (98, 212, 255),
        "seafoam": (92, 232, 184),
        "crimson": (238, 72, 64),
    }

    tokens = tokenize_cue(text, speaker)
    dummy = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    space_w = dummy.textlength(" ", font=font_main)
    widths = [dummy.textlength(t, font=font_main) for t, _ in tokens]
    text_w = sum(widths) + space_w * max(0, len(tokens) - 1)

    tag_str = {"A": "REEL · ", "B": "LINE · ", "C": "HORN · "}[speaker]
    tag_col = {"A": (248, 198, 74, 238), "B": (98, 212, 255, 238), "C": (92, 232, 184, 238)}[speaker]
    tag_w = dummy.textlength(tag_str, font=font_tag) + 8

    pad_x = 32
    box_w = int(math.ceil(tag_w + text_w + pad_x * 2))
    box_h = 90
    patch = Image.new("RGBA", (box_w + 24, box_h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)

    bg_col = {"A": (8, 9, 14, 206), "B": (5, 12, 22, 208), "C": (6, 15, 16, 208)}[speaker]
    bdr_col = {"A": (248, 198, 74, 64), "B": (98, 212, 255, 72), "C": (92, 232, 184, 72)}[speaker]
    d.rounded_rectangle([12, 12, 12 + box_w, 12 + box_h], radius=15, fill=bg_col, outline=bdr_col, width=1)

    # Spatial edge indicator matching stereo pan: Left bar (A), Top-Center bar (C), Right bar (B)
    if speaker == "A":
        d.rounded_rectangle([12, 24, 17, 12 + box_h - 12], radius=2, fill=(248, 198, 74, 240))
    elif speaker == "B":
        d.rounded_rectangle([12 + box_w - 5, 24, 12 + box_w, 12 + box_h - 12], radius=2, fill=(98, 212, 255, 240))
    else:
        d.rounded_rectangle([12 + box_w // 2 - 48, 12, 12 + box_w // 2 + 48, 16], radius=2, fill=(92, 232, 184, 240))

    cur_x = 12 + pad_x
    d.text((cur_x, 44), tag_str.strip(), font=font_tag, fill=tag_col, stroke_width=2, stroke_fill=(3, 6, 12, 230))
    cur_x += tag_w

    text_y = 25
    for (txt, role), w_px in zip(tokens, widths):
        col = COLORS[role]
        d.text((cur_x, text_y + 3), txt, font=font_main, fill=(0, 0, 0, 220), stroke_width=5, stroke_fill=(3, 5, 10, 220))
        d.text((cur_x, text_y), txt, font=font_main, fill=(*col, 255), stroke_width=3, stroke_fill=(4, 7, 13, 245))
        cur_x += w_px + space_w

    arr = np.array(patch, dtype=np.float32) / 255.0
    pan_shift = {"A": -88, "C": 0, "B": +88}[speaker]
    x0 = max(28, min(W - arr.shape[1] - 28, (W - arr.shape[1]) // 2 + pan_shift))
    y0 = 912
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

    patch = Image.new("RGBA", (680, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)
    d.text((8, 10), "M A R K   S I X", font=f_title, fill=(244, 242, 236, 244), stroke_width=2, stroke_fill=(4, 7, 13, 195))
    d.line([(10, 74), (398, 74)], fill=(248, 198, 74, 190), width=2)
    d.text((10, 86), "02:37 AM   ·   VAULT SIX ACOUSTIC RELAY", font=f_sub, fill=(248, 198, 74, 232), stroke_width=2, stroke_fill=(4, 7, 13, 195))
    arr = np.array(patch, dtype=np.float32) / 255.0
    return 86, 66, arr


# (lut_stem, z0, z1, px0, px1, py0, py1, rain_amt)
SHOT_SPECS = {
    "01": ("vault_slate_4300k",  1.000, 1.072,  0.000, -0.008,  0.004, -0.006, 0.14),
    "02": ("copper_cord_cyan",   1.010, 1.078,  0.010, -0.010,  0.004, -0.004, 0.05),
    "03": ("copper_cord_cyan",   1.005, 1.074,  0.000,  0.000,  0.014, -0.012, 0.06),
    "04": ("surge_breach_7000k", 1.000, 1.080, -0.010,  0.010,  0.008, -0.008, 0.30),
    "05": ("surge_breach_7000k", 1.010, 1.082, -0.012,  0.012,  0.006, -0.006, 0.32),
    "06": ("amber_oxide_reel",   1.005, 1.076, -0.006,  0.008,  0.006, -0.006, 0.06),
    "07": ("vault_slate_4300k",  1.064, 1.000,  0.000,  0.000, -0.006,  0.006, 0.16),  # Symmetrical Wall-Frame!
    "08": ("surge_breach_7000k", 1.000, 1.078, -0.006,  0.006,  0.008, -0.008, 0.26),
    "09": ("amber_oxide_reel",   1.010, 1.085,  0.010, -0.010,  0.006, -0.006, 0.10),
    "10": ("vault_slate_4300k",  1.068, 1.000,  0.000,  0.000, -0.008,  0.008, 0.22),
}


def main() -> None:
    os.makedirs(STILLS_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    tl = json.load(open(os.path.join(TIMING_DIR, "timeline_locked.json")))
    shots = tl["shots"]
    cues = tl["cues"]

    luts = {
        name: load_cube_lut(os.path.join(LUTS_DIR, f"{name}.cube"))
        for name in ("vault_slate_4300k", "amber_oxide_reel", "copper_cord_cyan", "surge_breach_7000k")
    }

    rain_diag_far = build_rain_tile(seed=901, density=0.00055, length=46, angle_deg=13.0, blur_r=0.7)
    rain_diag_near = build_rain_tile(seed=902, density=0.00022, length=88, angle_deg=14.5, blur_r=1.2)
    rain_vert = build_rain_tile(seed=903, density=0.00048, length=72, angle_deg=1.5, blur_r=0.9)
    tw, th = rain_diag_far.shape[1], rain_diag_far.shape[0]
    rain_col = np.array([0.66, 0.82, 0.98], dtype=np.float32)

    caption_patches = []
    for c in cues:
        x0, y0, rgba = render_caption_overlay(c["text"], c["speaker"])
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
        65:   "01_vault_three_chairs.png",        # 2.17s — Shot 01 Voice A REEL + title card
        280:  "02_dangling_handset_line.png",     # 9.33s — Shot 02 Voice B LINE caption
        450:  "03_ceiling_vhf_horn.png",          # 15.00s — Shot 03 Voice C HORN caption
        960:  "04_oxide_reel_room_mic.png",       # 32.00s — Shot 06 magnetic reel & room mic
        1225: "05_mark_six_interior_stencil.png", # 40.83s — Shot 08 MARK SIX stencil reveal
    }

    clip_paths = []
    cur_start_frame = 0

    for s in shots:
        sid = s["shot"]
        n_frames = s["frames"]
        s_frame = cur_start_frame
        e_frame = s_frame + n_frames
        cur_start_frame = e_frame

        lut_name, z0, z1, px0, px1, py0, py1, rain_amt = SHOT_SPECS[sid]
        pil_src = Image.open(os.path.join(PLATES_DIR, f"shot_{sid}.jpg")).convert("RGB")
        if pil_src.size != (W, H):
            pil_src = pil_src.resize((W, H), Image.Resampling.LANCZOS)
        raw_arr = np.array(pil_src, dtype=np.float32) / np.float32(255.0)
        del pil_src

        halo = None
        win_mask = None
        if sid in ("01", "03", "06", "07", "09"):
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            if sid == "01":
                win_mask = ((xx > 450) & (xx < 1470) & (yy > 280) & (yy < 590)).astype(np.float32)
            elif sid == "03":
                # Emerald VHF carrier pilot LED on ceiling junction box
                halo = np.exp(-(((xx - 994.0) / 36.0) ** 2 + ((yy - 608.0) / 36.0) ** 2)).astype(np.float32)
            elif sid == "06":
                # Warm 2600K analog VU meter glow on left magnetic tape deck
                halo = np.exp(-(((xx - 1378.0) / 115.0) ** 2 + ((yy - 606.0) / 72.0) ** 2)).astype(np.float32)
            elif sid == "07":
                win_mask = (np.clip((xx - 650.0) / 30.0, 0.0, 1.0) * np.clip((1270.0 - xx) / 30.0, 0.0, 1.0)
                            * np.clip((yy - 165.0) / 30.0, 0.0, 1.0) * np.clip((635.0 - yy) / 30.0, 0.0, 1.0)).astype(np.float32)
                halo = (
                    np.exp(-(((xx - 715.0) / 85.0) ** 2 + ((yy - 610.0) / 85.0) ** 2))
                    + np.exp(-(((xx - 960.0) / 85.0) ** 2 + ((yy - 610.0) / 85.0) ** 2))
                    + np.exp(-(((xx - 1205.0) / 85.0) ** 2 + ((yy - 610.0) / 85.0) ** 2))
                ).astype(np.float32)
            elif sid == "09":
                halo = np.exp(-(((xx - 1180.0) / 380.0) ** 2 + ((yy - 540.0) / 340.0) ** 2)).astype(np.float32)
            del xx, yy

        graded = apply_lut_trilinear(raw_arr, luts[lut_name])
        pil_single = Image.fromarray((graded * 255.0 + 0.5).astype(np.uint8))
        del raw_arr, graded
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

        for f_idx in range(s_frame, e_frame):
            t = f_idx / FPS
            u = (f_idx - s_frame) / max(n_frames - 1, 1)
            u_smooth = 0.35 * (0.5 - 0.5 * math.cos(math.pi * u)) + 0.65 * u

            zoom = z0 + (z1 - z0) * u_smooth
            px = px0 + (px1 - px0) * u_smooth
            py = py0 + (py1 - py0) * u_smooth

            cw, ch = W / zoom, H / zoom
            cx, cy = (W * 0.5) + px * W, (H * 0.5) + py * H
            bx0 = max(0.0, min(W - cw, cx - cw * 0.5))
            by0 = max(0.0, min(H - ch, cy - ch * 0.5))

            moved = pil_single.transform((W, H), Image.Transform.EXTENT, (bx0, by0, bx0 + cw, by0 + ch), Image.Resampling.BICUBIC)
            frame = np.array(moved, dtype=np.float32) * np.float32(1.0 / 255.0)

            # Diegetic transducer & practical lighting physics
            if sid == "03" and halo is not None:
                # Emerald VHF carrier LED pulses when Voice C (HORN) transmits
                mod = np.float32(0.075 + 0.045 * abs(math.sin(t * 16.0))) if (12.45 <= t <= 18.12) else np.float32(0.012)
                frame[:, :, 1] += halo * mod * np.float32(1.15)
                frame[:, :, 2] += halo * mod * np.float32(0.75)
            elif sid == "06" and halo is not None:
                # Warm 2600K VU meter modulation when Voice A (REEL) speaks
                mod = np.float32(0.050 + 0.038 * abs(math.sin(t * 11.5))) if (29.75 <= t <= 34.20) else np.float32(0.015)
                frame[:, :, 0] += halo * mod * np.float32(1.20)
                frame[:, :, 1] += halo * mod * np.float32(0.72)
            elif sid == "07" and halo is not None:
                p = np.float32(0.032 + 0.012 * math.sin(t * 4.4))
                frame[:, :, 0] += halo * (p * np.float32(1.15))
                frame[:, :, 1] += halo * (p * np.float32(0.65))
            elif sid == "09" and halo is not None:
                # Cold cyan hydraulic shear-bolt flash at 50.15s ("The window bolts just fired.")
                if 50.12 <= t <= 50.52:
                    fl = np.float32(math.exp(-((t - 50.18) / 0.11) ** 2) * 0.24)
                    frame[:, :, 1] += halo * fl * np.float32(0.85)
                    frame[:, :, 2] += halo * fl * np.float32(1.25)

            # Storm rain compositing (masked to window panes on Shots 01 & 07; full storm outside on Shots 04, 05, 08, 10)
            if rain_amt > 0.0:
                if sid in ("01", "07") and win_mask is not None:
                    ox = int((f_idx * 4) % (tw - W))
                    oy = int((-f_idx * 68) % (th - H))
                    rv = rain_vert[oy:oy + H, ox:ox + W] * win_mask * np.float32(rain_amt * 1.45)
                    np.clip(frame, 0.0, 1.0, out=frame)
                    frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - rv[:, :, None] * rain_col)
                else:
                    ox1 = int((f_idx * 19) % (tw - W))
                    oy1 = int((-f_idx * 58) % (th - H))
                    ox2 = int((f_idx * 33 + 310) % (tw - W))
                    oy2 = int((-f_idx * 94 + 170) % (th - H))
                    rt = (rain_diag_far[oy1:oy1 + H, ox1:ox1 + W] * np.float32(0.62) + rain_diag_near[oy2:oy2 + H, ox2:ox2 + W] * np.float32(0.85)) * np.float32(rain_amt)
                    np.clip(frame, 0.0, 1.0, out=frame)
                    frame = np.float32(1.0) - (np.float32(1.0) - frame) * (np.float32(1.0) - rt[:, :, None] * rain_col)

            np.clip(frame, 0.0, 1.0, out=frame)

            # Save clean uncaptioned Wall-Frame gallery print on Shot 07!
            if sid == "07" and f_idx == 1090:
                p_u8 = (frame * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
                Image.fromarray(p_u8).save(os.path.join(STILLS_DIR, "wall_frame_mark_six_clean.png"))

            # Opening architectural title card on Shot 01 (0.55s -> 3.60s)
            if 0.55 <= t <= 3.60:
                t_alpha = np.float32(min(1.0, (t - 0.55) / 0.45, (3.60 - t) / 0.55))
                th_p, tw_p = title_rgba.shape[0], title_rgba.shape[1]
                a_t = title_rgba[:, :, 3:4] * t_alpha
                roi = frame[title_y0:title_y0 + th_p, title_x0:title_x0 + tw_p]
                frame[title_y0:title_y0 + th_p, title_x0:title_x0 + tw_p] = roi * (np.float32(1.0) - a_t) + title_rgba[:, :, :3] * a_t

            # 40 Three-Voice WordBoundary-Locked Caption Beats
            for cp in caption_patches:
                if cp["start"] - 0.02 <= t <= cp["end"] + 0.03:
                    c_alpha = np.float32(max(0.0, min(1.0, (t - (cp["start"] - 0.02)) / 0.055, ((cp["end"] + 0.03) - t) / 0.065)))
                    ch_p, cw_p = cp["rgb"].shape[0], cp["rgb"].shape[1]
                    x0, y0 = cp["x0"], cp["y0"]
                    a_c = cp["alpha"] * c_alpha
                    roi = frame[y0:y0 + ch_p, x0:x0 + cw_p]
                    frame[y0:y0 + ch_p, x0:x0 + cw_p] = roi * (np.float32(1.0) - a_c) + cp["rgb"] * a_c
                    break

            # Short <= 0.28s head/tail fades so zero black spans exceed 0.5s
            if t < 0.26:
                frame *= np.float32(max(0.05, t / 0.26))
            elif t > 59.72:
                frame *= np.float32(max(0.05, (60.0 - t) / 0.28))

            out_u8 = (np.clip(frame, 0.0, 1.0) * np.float32(255.0) + np.float32(0.5)).astype(np.uint8)
            proc.stdin.write(out_u8.tobytes())

            if f_idx in still_targets:
                Image.fromarray(out_u8).save(os.path.join(STILLS_DIR, still_targets[f_idx]))

        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"Shot {sid} ffmpeg failed with {rc}")
        print(f"  Completed Shot {sid} ({n_frames}f -> {clip_path})")

        del pil_single
        if halo is not None:
            del halo
        if win_mask is not None:
            del win_mask
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

    # Record final MP4 SHA256, AAC correlation vs master_audio_48k.wav, L/R correlation, and per-10s MP4 RMS into gain_mapping.json
    gmap_path = os.path.join(AUDIO_DIR, "gain_mapping.json")
    gmap = json.load(open(gmap_path))
    dec_wav = "/tmp/grade_v07_build/_mp4_dec.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", OUT_MP4, "-vn", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", dec_wav],
        check=True,
    )
    _, m_pcm = wavfile.read(MASTER_WAV)
    _, d_pcm = wavfile.read(dec_wav)
    os.remove(dec_wav)
    n = min(len(m_pcm), len(d_pcm))
    corr_mp4 = float(np.corrcoef(m_pcm[:n].ravel().astype(float), d_pcm[:n].ravel().astype(float))[0, 1])
    res_db = float(20.0 * np.log10(np.sqrt(np.mean(((m_pcm[:n].astype(float) - d_pcm[:n].astype(float)) / 32768.0) ** 2)) + 1e-12))
    lr_corr = float(np.corrcoef(d_pcm[:, 0].astype(float), d_pcm[:, 1].astype(float))[0, 1])

    for i, w in enumerate(gmap["body_windows_10s"]):
        i0, i1 = i * 10 * 48000, (i + 1) * 10 * 48000
        w["mp4_mix_rms_dbfs"] = round(float(20.0 * np.log10(np.sqrt(np.mean((d_pcm[i0:i1].astype(float) / 32768.0) ** 2)) + 1e-12)), 2)

    gmap["delivered_mp4_sha256"] = hashlib.sha256(open(OUT_MP4, "rb").read()).hexdigest()
    gmap["mp4_stereo_LR_correlation"] = round(lr_corr, 4)
    gmap["master_to_mp4_aac_correlation_r"] = round(corr_mp4, 6)
    gmap["master_to_mp4_aac_residual_dbfs"] = round(res_db, 2)
    json.dump(gmap, open(gmap_path, "w"), indent=2)
    print(f"Successfully rendered {OUT_MP4} (r={corr_mp4:.6f}, LR_corr={lr_corr:.4f})")


if __name__ == "__main__":
    main()
