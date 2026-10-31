#!/usr/bin/env python3
"""
generate.py — v07 "IT ANSWERED — NIGHT TWO". Vertical 1080x1920, 30 fps, 60.0 s.

The v06 critique was that the film had objects on near-empty darkness and no world. This build
is organised around the opposite: a small library of *rooms* (window, table, wall, door, kitchen,
plan, corridor), each drawn with foreground, midground, background and its own light source, and
reused across the film with different lighting and different props so the flat is a place the
viewer can map. Nothing is ever an object floating on black.

Deterministic: frame n is a pure function of n and the fixed seeds in here.
"""
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WORK = HERE / "work"
FONT_DIR = HERE / "fonts"

W, H = 1080, 1920
FPS = 30
DUR = 60.0
NF = int(DUR * FPS)

# night palette (doc/STYLE-BREAKDOWN.md)
BG = (10, 14, 28)
WALL = (17, 23, 40)
WALL2 = (13, 18, 33)
FLOOR = (27, 22, 31)
WOOD = (46, 33, 26)
WOOD2 = (60, 43, 33)
AMBER = (245, 209, 78)
LAMP = (255, 197, 110)
RED = (226, 69, 60)
WHITE = (236, 240, 248)
DIM = (138, 154, 180)
GREEN = (124, 242, 156)
GLASS = (60, 92, 140)
RAIN = (120, 150, 200)

# Caption colour per narration line: "a" amber, "w" white, "r" red.
CAP_COLOUR = {1: "a", 2: "w", 3: "w", 4: "w", 5: "w", 6: "a", 7: "r", 8: "w", 9: "w",
              10: "w", 11: "w", 12: "r", 13: "r", 14: "w", 15: "w", 16: "w", 17: "r",
              18: "r", 19: "w", 20: "a"}


def build_captions():
    """Cue times come from the measured narration (work/narration.json), so picture, voice and
    caption can never drift apart. Segments split on commas; nothing longer than 5 words."""
    import json
    meta = json.loads((WORK / "narration.json").read_text())
    cues = []
    for ln in meta["lines"]:
        text = ln["text"]
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if not parts:
            parts = [text]
        total_chars = sum(len(p) for p in parts) or 1
        t0, span = ln["start"], max(0.35, ln["end"] - ln["start"])
        acc = 0
        for part in parts:
            a = t0 + span * acc / total_chars
            acc += len(part)
            b = t0 + span * acc / total_chars
            words = part.split()
            if len(words) > 5:                      # split long segments at word boundaries
                chunks = [words[i:i + 5] for i in range(0, len(words), 5)]
                sub = (b - a) / len(chunks)
                for k, ch in enumerate(chunks):
                    cues.append((a + k * sub, a + (k + 1) * sub, " ".join(ch).upper(),
                                 CAP_COLOUR.get(ln["i"], "w")))
            else:
                cues.append((a, b, part.upper(), CAP_COLOUR.get(ln["i"], "w")))
    return cues


CAPTIONS = []   # filled in main() / probe from build_captions()

# (start, end, room, variant) — uneven by design: 7 shots < 2 s, one 16 s hold before the twist
SHOTS = [
    (0.00, 4.10, "window", "street"),
    (4.10, 8.20, "table", "lamp"),
    (8.20, 9.60, "wall", "stain_small"),
    (9.60, 10.60, "door", "hall_light"),
    (10.60, 11.60, "kitchen", "glow"),
    (11.60, 13.60, "plan", "six"),
    (13.60, 16.70, "plan", "six_pulse"),
    (16.70, 19.20, "window", "rain_stop"),
    (19.20, 20.90, "table", "radio"),
    (20.90, 23.00, "kitchen", "kettle"),
    (23.00, 24.60, "door", "towel"),
    (24.60, 27.40, "wall", "stain_big"),
    (27.40, 30.20, "plan", "seven"),
    (30.20, 46.20, "corridor", "hold"),
    (46.20, 47.70, "wall", "slam"),
    (47.70, 49.60, "table", "ring_red"),
    (49.60, 52.20, "door", "shadow"),
    (52.20, 55.20, "corridor", "dark_room"),
    (55.20, 60.00, "hook", "card"),
]

VIG = None
GRAIN = None


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), int(size))


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def ease_in_out(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def push(img, lt, dur, amount=0.06):
    """The reference's slow push-in: 1.00 -> 1.06, eased, on every shot."""
    s = 1.0 + amount * ease_in_out(lt / max(dur, 1e-3))
    if s <= 1.0005:
        return img
    w2, h2 = int(W * s), int(H * s)
    big = img.resize((w2, h2), Image.BILINEAR)
    x = (w2 - W) // 2
    y = (h2 - H) // 2
    return big.crop((x, y, x + W, y + H))


def init_layers():
    global VIG, GRAIN
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (x - W / 2) / (W / 2)
    dy = (y - H / 2) / (H / 2)
    r = np.sqrt(dx * dx + dy * dy) / 1.4
    # strong vignette (reference look) but never so dark that blackdetect calls it black
    VIG = np.clip(1.0 - 0.46 * r ** 1.8, 0.55, 1.0)
    rng = np.random.default_rng(23)
    GRAIN = []
    for _ in range(12):
        lr = rng.normal(0, 1.0, (H // 4, W // 4)).astype(np.float32)
        im = Image.fromarray(lr, mode="F").resize((W, H), Image.BILINEAR)
        GRAIN.append((np.asarray(im, dtype=np.float32) * 1.6).astype(np.float32))


def base(t):
    """Wall-and-floor shell every room sits in, with a slow light drift."""
    arr = np.zeros((H, W, 3), np.float32)
    floor_y = 1330
    yy = np.arange(H, dtype=np.float32)[:, None]
    drift = 2.5 * math.sin(t * 0.6)
    for i in range(3):
        arr[..., i] = np.where(yy < floor_y, WALL[i], FLOOR[i]) + drift
    arr *= VIG[..., None]
    return arr


def light(arr, cx, cy, radius, colour, strength):
    y0, y1 = max(0, int(cy - radius * 2.4)), min(H, int(cy + radius * 2.4))
    x0, x1 = max(0, int(cx - radius * 2.4)), min(W, int(cx + radius * 2.4))
    if y1 <= y0 or x1 <= x0:
        return
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (radius * radius)) * 1.7) * strength
    for i in range(3):
        arr[y0:y1, x0:x1, i] += g * colour[i]


# ---------------------------------------------------------------- room furniture
def rain_lines(dr, x0, y0, x1, y1, t, density=26, alpha=110, speed=520):
    for i in range(density):
        sx = x0 + ((i * 83 + int(t * 190)) % max(1, x1 - x0))
        sy = y0 + ((i * 57 + int(t * speed)) % max(1, y1 - y0))
        dr.line([sx, sy, sx - 5, sy + 26], fill=RAIN + (alpha,), width=2)


def draw_speaker(img, cx, cy, r, ring=0.0, listening=0.0, ring_col=None):
    """A cylinder smart speaker: fabric mesh body, a lit ring around its top edge, a faint
    top surface. Drawn as a cylinder so it reads as an object in a room, not a flat icon."""
    dr = ImageDraw.Draw(img, "RGBA")
    bw, bh = r * 1.55, r * 1.95
    x0, y0 = cx - bw / 2, cy - bh / 2
    # shadow on whatever it stands on
    dr.ellipse([x0 - r * 0.22, y0 + bh - r * 0.16, x0 + bw + r * 0.22, y0 + bh + r * 0.20],
               fill=(0, 0, 0, 90))
    # fabric body: one rounded rect with a soft inner light band
    dr.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(bw * 0.46), fill=(36, 42, 57, 255))
    dr.rounded_rectangle([x0 + bw * 0.10, y0 + bh * 0.18, x0 + bw * 0.44, y0 + bh * 0.80],
                         radius=int(bw * 0.18), fill=(42, 49, 66, 255))
    dr.rounded_rectangle([x0 + bw * 0.02, y0 + bh * 0.02, x0 + bw * 0.98, y0 + bh * 0.98],
                         radius=int(bw * 0.45), outline=(58, 66, 84, 255), width=2)
    # mesh: faint horizontal ribs
    for k in range(11):
        yy = y0 + bh * (0.16 + 0.072 * k)
        dr.line([x0 + bw * 0.16, yy, x0 + bw * 0.84, yy], fill=(52, 60, 78, 80), width=2)
    # top surface (an ellipse) and the light ring on its edge
    dr.ellipse([x0, y0 - r * 0.30, x0 + bw, y0 + r * 0.34], fill=(38, 45, 60, 255),
               outline=(64, 74, 94, 255), width=2)
    dr.ellipse([x0 + bw * 0.30, y0 - r * 0.10, x0 + bw * 0.70, y0 + r * 0.18], fill=(26, 31, 43, 255))
    if ring > 0:
        rc = ring_col or (GREEN if listening > 0 else AMBER)
        rr = 1.0 + 0.06 * math.sin(cx + ring * 6)
        dr.ellipse([x0 - 3 * rr, y0 - r * 0.325, x0 + bw + 3 * rr, y0 + r * 0.365],
                   outline=rc + (int(240 * ring),), width=max(3, int(5 + 4 * listening)))


def soft_glow(img, cx, cy, rx, ry, colour, strength, steps=48):
    """Radial falloff done by drawing at 1/8 scale and upscaling, which is band-free and cheap."""
    sw, sh_ = max(8, int(rx * 2 / 8)), max(8, int(ry * 2 / 8))
    small = Image.new("L", (sw, sh_), 0)
    d = ImageDraw.Draw(small)
    for k in range(steps, 0, -1):
        f = k / steps
        d.ellipse([sw / 2 - sw / 2 * f, sh_ / 2 - sh_ / 2 * f, sw / 2 + sw / 2 * f, sh_ / 2 + sh_ / 2 * f],
                  fill=int(255 * strength * (1 - f) ** 2.1))
    mask = small.resize((int(rx * 2), int(ry * 2)), Image.BICUBIC)
    layer = Image.new("RGB", mask.size, colour)
    img.paste(layer, (int(cx - rx), int(cy - ry)), mask)


def draw_clock(img, t, x=820, y=176, alpha=1.0):
    """Red LED clock, top-right (the vertical frame's upper third is UI-safe)."""
    dr = ImageDraw.Draw(img, "RGBA")
    f1 = font("Anton-Regular.ttf", 74)
    f2 = font("BarlowCondensed-SemiBold.ttf", 30)
    tw = dr.textlength("2:14", font=f1)
    dr.text((x - tw, y), "2:14", font=f1, fill=RED + (int(230 * alpha),))
    lw = dr.textlength("NIGHT 2", font=f2)
    dr.text((x - lw, y + 86), "NIGHT 2", font=f2, fill=(180, 120, 118, int(200 * alpha)))


# ---------------------------------------------------------------- rooms
def room_window(img, t, lt, dur, variant):
    """Street at night seen through the flat's window: sill, glass, rain, the flat reflected."""
    dr = ImageDraw.Draw(img, "RGBA")
    # wall behind and window frame
    dr.rectangle([0, 0, W, 1330], fill=WALL + (255,))
    fx0, fy0, fx1, fy1 = 90, 300, 990, 1180
    dr.rectangle([fx0 - 34, fy0 - 34, fx1 + 34, fy1 + 34], fill=(26, 32, 50, 255))
    # the street beyond the glass
    dr.rectangle([fx0, fy0, fx1, fy1], fill=(18, 26, 46, 255))
    # far buildings with a few lit windows
    for i, (bx, bw, bh) in enumerate([(120, 180, 330), (330, 150, 250), (500, 210, 400), (740, 200, 290)]):
        dr.rectangle([fx0 + bx, fy1 - bh, fx0 + bx + bw, fy1], fill=(13, 19, 34, 255))
        for ry in range(4):
            for rx in range(3):
                if (i + ry + rx) % 3 == 0:
                    wx = fx0 + bx + 22 + rx * 52
                    wy = fy1 - bh + 30 + ry * 62
                    if wx + 26 < fx0 + bx + bw:
                        col = LAMP if (i + rx) % 2 else (120, 150, 190)
                        dr.rectangle([wx, wy, wx + 24, wy + 34], fill=col + (150,))
    # moonlit cloud band
    dr.ellipse([fx0 + 420, fy0 + 40, fx0 + 760, fy0 + 170], fill=(30, 40, 64, 180))
    # glass sheen + mullions
    dr.line([(fx0 + fx1) // 2, fy0, (fx0 + fx1) // 2, fy1], fill=(70, 84, 112, 255), width=10)
    dr.line([fx0, (fy0 + fy1) // 2, fx1, (fy0 + fy1) // 2], fill=(70, 84, 112, 255), width=10)
    dr.polygon([[fx0, fy0], [fx0 + 240, fy0], [fx0 + 60, fy1], [fx0, fy1]], fill=(120, 150, 200, 16))
    # rain: on the glass, and the street going quiet in the rain_stop variant
    density = 26 if variant != "rain_stop" else int(26 * max(0.0, 1 - lt / 2.3))
    if density > 0:
        rain_lines(dr, fx0, fy0, fx1, fy1, t, density=density)
    # a lit window opposite that dims in rain_stop
    lw_alpha = 230 if variant != "rain_stop" else int(230 * max(0.35, 1 - lt / 2.0))
    dr.rectangle([fx0 + 560, fy0 + 250, fx0 + 610, fy0 + 310], fill=LAMP + (lw_alpha,))
    # the sill, foreground
    dr.rectangle([fx0 - 46, fy1 + 10, fx1 + 46, fy1 + 58], fill=WOOD2 + (255,))
    dr.rectangle([fx0 - 46, fy1 + 10, fx1 + 46, fy1 + 24], fill=(84, 62, 46, 255))
    # a plant pot on the sill, foreground depth
    dr.polygon([[fx1 - 120, fy1 + 8], [fx1 - 40, fy1 + 8], [fx1 - 56, fy1 - 60], [fx1 - 104, fy1 - 60]],
               fill=(44, 32, 26, 255))
    for k in range(5):
        dr.line([(fx1 - 80) + k * 6 - 12, fy1 - 58, (fx1 - 80) + (k - 2) * 22, fy1 - 150 + abs(k - 2) * 18],
                fill=(38, 62, 52, 255), width=5)
    # floor + rug, foreground
    dr.rectangle([0, 1330, W, H], fill=FLOOR + (255,))
    for i in range(5):
        dr.line([0, 1350 + i * 116, W, 1346 + i * 116], fill=(34, 28, 38, 255), width=2)
    dr.ellipse([150, 1390, 930, 1880], fill=(44, 30, 32, 255))
    dr.ellipse([196, 1430, 884, 1840], outline=(62, 42, 42, 255), width=6)
    dr.ellipse([250, 1480, 830, 1790], outline=(56, 38, 40, 255), width=3)
    # sofa arm, foreground bottom-left, cropped by the frame
    dr.rounded_rectangle([-60, 1560, 300, 1920], radius=40, fill=(38, 33, 44, 255))
    dr.rounded_rectangle([-60, 1520, 300, 1600], radius=34, fill=(48, 42, 55, 255))
    dr.line([0, 1330, W, 1330], fill=(38, 46, 66, 255), width=4)


def room_table(img, t, lt, dur, variant):
    """The table: lamp, speaker, mug. Wood grain, chair back in foreground."""
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 0, W, 1200], fill=WALL2 + (255,))
    # wall art — proves this is a room, and gives the push something to pass
    dr.rectangle([700, 280, 950, 470], fill=(24, 30, 46, 255), outline=(52, 64, 88, 255), width=5)
    dr.ellipse([780, 330, 870, 420], fill=(40, 50, 72, 255))
    # shelves with a few objects, midground left — the wall is no longer empty
    for sy in (420, 640):
        dr.rectangle([60, sy, 470, sy + 16], fill=(52, 40, 32, 255))
        dr.rectangle([60, sy + 16, 470, sy + 26], fill=(34, 26, 21, 255))
    for (ox, ow, oh) in [(92, 34, 96), (150, 26, 132), (196, 46, 70)]:
        dr.rectangle([ox, 420 - oh, ox + ow, 420], fill=(44, 50, 68, 255))
    for (ox, ow, oh) in [(110, 40, 88), (180, 30, 110), (240, 54, 64), (330, 28, 96)]:
        dr.rectangle([ox, 640 - oh, ox + ow, 640], fill=(40, 46, 62, 255))
    # a doorway at the right: recess, jamb and a dim room beyond (also the source of the green light)
    dr.rectangle([980, 300, W, 1250], fill=(12, 17, 28, 255))
    dr.rectangle([980, 300, 996, 1250], fill=(44, 37, 32, 255))
    dr.rectangle([1050, 330, W, 1240], fill=(16, 21, 34, 255))
    soft_glow(img, 1085, 780, 150, 460, GREEN, 0.20)
    # table top
    dr.rectangle([0, 1200, W, H], fill=WOOD + (255,))
    dr.rectangle([0, 1200, W, 1240], fill=WOOD2 + (255,))
    for i in range(7):
        dr.line([0, 1290 + i * 90, W, 1286 + i * 90], fill=(52, 38, 30, 255), width=2)
    # chair, foreground left, cropped by the frame edge: back, seat and two legs
    dr.rectangle([-30, 1010, 190, 1130], fill=(34, 26, 21, 255))
    dr.rectangle([-30, 1030, 160, 1110], fill=(27, 20, 17, 255))
    dr.rectangle([-30, 1120, 240, 1180], fill=(40, 31, 25, 255))
    dr.rectangle([-10, 1180, 22, 1420], fill=(30, 23, 19, 255))
    dr.rectangle([150, 1180, 182, 1420], fill=(26, 20, 17, 255))
    # lamp, right — the room's main light
    soft_glow(img, 830, 620, 300, 300, (255, 197, 110), 0.30)
    dr.polygon([[744, 706], [916, 706], [874, 604], [786, 604]], fill=(58, 45, 33, 255))
    dr.polygon([[766, 700], [894, 700], [862, 616], [798, 616]], fill=(255, 216, 150, 232))
    dr.rectangle([824, 706, 836, 792], fill=(48, 38, 30, 255))
    dr.ellipse([800, 780, 860, 812], fill=(58, 45, 33, 255))
    # the speaker, centre-left on the table
    ring = 0.55 + 0.35 * math.sin(t * 2.2)
    rcol = None
    if variant == "ring_red":
        ring, rcol = 1.0, RED
    draw_speaker(img, 470, 1120, 96, ring=ring, listening=1.0, ring_col=rcol)
    # mug, and in ring_red it vibrates
    mx = 640 + (3 * math.sin(t * 60) if variant == "ring_red" else 0)
    dr.rounded_rectangle([mx - 46, 1080, mx + 46, 1180], radius=10, fill=(56, 44, 38, 255))
    dr.ellipse([mx - 46, 1066, mx + 46, 1094], fill=(40, 31, 27, 255))
    dr.arc([mx + 40, 1096, mx + 92, 1150], 300, 60, fill=(56, 44, 38, 255), width=10)
    # radio (radio variant) — a small box with a jumping needle
    if variant == "radio":
        dr.rounded_rectangle([180, 940, 420, 1080], radius=14, fill=(34, 40, 56, 255),
                             outline=(70, 84, 110, 255), width=4)
        for i in range(9):
            dr.line([206 + i * 22, 960, 206 + i * 22, 976], fill=(120, 136, 162, 255), width=3)
        nx = 210 + int(80 * (0.5 + 0.5 * math.sin(t * 7.3)))
        dr.line([nx, 990, nx + 10, 1050], fill=AMBER + (255,), width=5)
    # a book and a folded cloth on the table, foreground
    dr.polygon([[150, 1330], [470, 1322], [486, 1400], [160, 1412]], fill=(52, 42, 38, 255))
    dr.polygon([[150, 1330], [470, 1322], [472, 1348], [152, 1356]], fill=(78, 62, 52, 255))
    dr.polygon([[690, 1330], [860, 1326], [866, 1394], [696, 1398]], fill=(58, 60, 74, 255))
    # warm pool from the lamp onto the wood
    dr.ellipse([560, 1230, 1000, 1420], fill=(120, 90, 40, 26))


def room_wall(img, t, lt, dur, variant):
    """The wall the speaker throws its light across. Built as a wall, not a ring: plaster, skirting,
    a hung frame, a sideboard in the foreground and a soft projected pool of light that grows."""
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 0, W, H], fill=WALL + (255,))
    # plaster mottling — subtle, so the wall is a surface rather than a fill
    rng = np.random.default_rng(9)
    for _ in range(90):
        x, y = int(rng.integers(-40, W)), int(rng.integers(0, 1420))
        rr = int(rng.integers(40, 150))
        dr.ellipse([x, y, x + rr, y + rr * 0.7], fill=(20, 27, 45, int(rng.integers(8, 20))))
    # skirting board + floor edge: this is what makes it read as a room
    dr.rectangle([0, 1400, W, 1470], fill=(30, 37, 54, 255))
    dr.rectangle([0, 1470, W, H], fill=FLOOR + (255,))
    for i in range(6):
        dr.line([0, 1500 + i * 74, W, 1496 + i * 74], fill=(26, 21, 28, 255), width=2)
    # a hung frame, off-centre — a room detail the push-in travels past
    dr.rectangle([128, 330, 402, 610], fill=(22, 28, 44, 255), outline=(52, 64, 88, 255), width=6)
    dr.rectangle([150, 352, 380, 588], fill=(17, 22, 36, 255))
    dr.polygon([[170, 560], [300, 400], [360, 470], [360, 580]], fill=(28, 36, 54, 255))
    # sideboard, foreground left
    dr.rectangle([0, 1150, 330, 1420], fill=(38, 29, 24, 255))
    dr.rectangle([0, 1150, 330, 1186], fill=(52, 40, 32, 255))
    dr.line([165, 1186, 165, 1420], fill=(30, 23, 19, 255), width=4)
    for hy in (1260, 1340):
        dr.ellipse([60, hy, 78, hy + 18], outline=(96, 80, 52, 255), width=3)
        dr.ellipse([250, hy, 268, hy + 18], outline=(96, 80, 52, 255), width=3)
    # a plant on the sideboard, foreground depth against the light
    dr.polygon([[70, 1150], [150, 1150], [136, 1078], [84, 1078]], fill=(40, 32, 26, 255))
    for k in range(6):
        dr.line([110, 1080, 110 + (k - 3) * 30, 960 - abs(k - 3) * 26], fill=(36, 58, 48, 255), width=6)

    # the projected light on the wall — a soft pool, elliptical falloff, not stroked rings
    if variant == "stain_small":
        rr, a, col = 250, 0.30, GREEN
    elif variant == "stain_big":
        rr, a, col = 340 + 14 * math.sin(t * 1.7), 0.42, GREEN
    else:                                     # slam
        rr, a, col = 430, 0.62, RED
    cx = 590 + 46 * math.sin(t * 0.55)
    cy = 820 + 30 * math.cos(t * 0.47)
    # the pool of light: a real radial falloff, plus a tighter core so it reads as projected
    soft_glow(img, cx, cy, rr * 1.35, rr * 1.05, col, min(0.85, a * 1.9))
    soft_glow(img, cx, cy, rr * 0.55, rr * 0.44, col, min(0.95, a * 2.4))
    dr = ImageDraw.Draw(img, "RGBA")
    dr.ellipse([cx - rr * 0.30, cy - rr * 0.24, cx + rr * 0.30, cy + rr * 0.24],
               outline=col + (int(60 + 110 * a),), width=3)
    soft_glow(img, 250, 560, 240, 240, (255, 197, 110), 0.10)   # a lamp off-frame left
    dr = ImageDraw.Draw(img, "RGBA")
    # the speaker on the floor, in front of the wall, source of that light
    draw_speaker(img, 560, 1330, 92, ring=1.0, listening=1.0,
                 ring_col=(RED if variant == "slam" else None))
    dr.ellipse([cx - rr * 0.5, 1360, cx + rr * 0.5, 1440], fill=col + (int(22 * a * 3),))


def room_door(img, t, lt, dur, variant):
    """The flat's front door, hallway light beneath it. Foreground floor + door handle."""
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 0, W, H], fill=WALL2 + (255,))
    dr.rectangle([0, 1400, W, H], fill=FLOOR + (255,))
    # door
    dx0, dy0, dx1, dy1 = 220, 250, 860, 1400
    dr.rectangle([dx0 - 26, dy0 - 26, dx1 + 26, dy1], fill=(30, 24, 22, 255))
    dr.rectangle([dx0, dy0, dx1, dy1], fill=(44, 33, 28, 255))
    for (px, py) in [(dx0 + 60, dy0 + 70), (dx0 + 340, dy0 + 70), (dx0 + 60, dy0 + 520), (dx0 + 340, dy0 + 520)]:
        dr.rectangle([px, py, px + 240, py + 400], fill=(40, 30, 26, 255), outline=(52, 40, 34, 255), width=3)
    dr.ellipse([dx1 - 110, 800, dx1 - 70, 840], fill=(150, 130, 96, 255))
    # gap of hallway light under the door — the film's whole threat lives here
    gap_alpha = 255
    gap_col = LAMP
    if variant == "towel":
        gap_alpha = int(255 * max(0.0, 1 - lt / 1.2))
    if variant == "shadow":
        # two vertical shadows in the light = someone standing outside
        gap_col, gap_alpha = (235, 190, 120), 255
    dr.rectangle([dx0, dy1 - 26, dx1, dy1], fill=gap_col + (gap_alpha,))
    if variant == "shadow":
        for sx in (dx0 + 190, dx0 + 420):
            dr.rectangle([sx, dy1 - 26, sx + 46, dy1], fill=(30, 24, 18, 255))
    # towel sliding in under the door
    if variant == "towel":
        tw_ty = dy1 - 26
        dr.rectangle([dx0 + 40, tw_ty - 6, dx1 - 40, tw_ty + 30], fill=(96, 104, 122, 255))
    # hallway light spilling on the floor
    dr.polygon([[dx0 - 60, dy1], [dx1 + 60, dy1], [dx1 + 240, H], [dx0 - 240, H]],
               fill=LAMP + (int(38 * (gap_alpha / 255)),))


def room_kitchen(img, t, lt, dur, variant):
    """Counter, kettle, tiles, and the speaker's glow bleeding in from the next room."""
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 0, W, 1250], fill=WALL2 + (255,))
    # tiled splashback
    for r in range(6):
        for c in range(9):
            tx, ty = 40 + c * 116, 420 + r * 116
            dr.rectangle([tx, ty, tx + 108, ty + 108], outline=(30, 38, 58, 255), width=3)
    # counter
    dr.rectangle([0, 1250, W, H], fill=(36, 40, 54, 255))
    dr.rectangle([0, 1250, W, 1290], fill=(56, 62, 80, 255))
    dr.rectangle([0, 1500, W, H], fill=(26, 30, 42, 255))
    # kettle
    kx = 330
    dr.rounded_rectangle([kx - 90, 1080, kx + 90, 1256], radius=26, fill=(64, 70, 88, 255))
    dr.arc([kx - 120, 1060, kx + 30, 1180], 200, 340, fill=(88, 96, 116, 255), width=14)
    dr.rectangle([kx - 16, 1040, kx + 16, 1088], fill=(80, 88, 108, 255))
    # steam in the kettle variant
    if variant == "kettle":
        for i in range(7):
            ph = (lt * 0.9 + i * 0.32) % 1.0
            sx = kx - 20 + 40 * math.sin(i * 2.1 + lt * 2.6)
            sy = 1040 - ph * 620
            a = int(120 * (1 - ph) * min(1, lt))
            dr.ellipse([sx - 26 - ph * 20, sy - 26 - ph * 20, sx + 26 + ph * 20, sy + 26 + ph * 20],
                       fill=(210, 220, 235, a))
    # the doorway to the next room, left: a lit opening and the green spilling out of it
    dr.rectangle([0, 300, 250, 1250], fill=(14, 19, 32, 255))
    dr.rectangle([196, 340, 250, 1250], fill=(58, 48, 40, 255))
    ga = 0.34 + 0.10 * math.sin(t * 1.6)
    for k in range(16, 0, -1):
        f = k / 16.0
        dr.polygon([[250, 380 - 60 * f], [250 + 430 * f, 470 - 90 * f],
                    [250 + 430 * f, 1180 + 90 * f], [250, 1200 + 60 * f]],
                   fill=GREEN + (int(ga * 5 * (1 - f) + 1),))
    dr.rectangle([196, 340, 208, 1250], fill=GREEN + (int(120 * ga * 2),))
    # jars on the counter, foreground
    for i, (jx, jw, jh) in enumerate([(640, 80, 150), (760, 64, 120), (864, 92, 190)]):
        dr.rounded_rectangle([jx, 1250 - jh, jx + jw, 1250], radius=12, fill=(48, 56, 74, 255))
        dr.rectangle([jx, 1250 - jh, jx + jw, 1250 - jh + 18], fill=(70, 80, 102, 255))


def room_plan(img, t, lt, dur, variant):
    """The flat drawn as a floorplan in light: six rooms, six marks, then a seventh."""
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 0, W, H], fill=(8, 11, 20, 255))
    # blueprint grid
    for i in range(0, W, 60):
        dr.line([i, 0, i, H], fill=(20, 28, 46, 255), width=1)
    for j in range(0, H, 60):
        dr.line([0, j, W, j], fill=(20, 28, 46, 255), width=1)
    # the flat: six rooms (the same six the film shows)
    rooms = [
        ("window", 120, 380, 420, 380),
        ("table", 560, 380, 400, 340),
        ("wall", 120, 800, 380, 340),
        ("door", 520, 760, 440, 300),
        ("kitchen", 120, 1180, 420, 320),
        ("corridor", 560, 1100, 400, 400),
    ]
    for i, (name, x, y, w, h) in enumerate(rooms):
        dr.rectangle([x, y, x + w, y + h], outline=(96, 150, 190, 235), width=5)
        dr.text((x + 18, y + 14), name.upper(), font=font("BarlowCondensed-SemiBold.ttf", 30),
                fill=(96, 150, 190, 190))
        # one microphone mark per room, pulsing in turn
        if variant == "six_pulse":
            ph = 0.5 + 0.5 * math.sin(lt * 3.4 - i * 0.9)
        else:
            ph = 0.35
        mx, my = x + w - 54, y + h - 54
        dr.ellipse([mx - 26, my - 26, mx + 26, my + 26], outline=RED + (int(120 + 120 * ph),), width=4)
        dr.ellipse([mx - 9, my - 9, mx + 9, my + 9], fill=RED + (int(140 + 110 * ph),))
    # the seventh: a room that is not there, appearing at 27.3 s
    if variant == "seven":
        grow = ease_out(lt / 0.9)
        x, y, w, h = 560, 590, 400, 150
        dr.rectangle([x, y, x + w * grow, y + h], outline=RED + (int(255 * grow),), width=5)
        dr.text((x + 18, y + 14), "— — —", font=font("BarlowCondensed-SemiBold.ttf", 30),
                fill=RED + (int(220 * grow),))
        mx, my = x + w - 54, y + 46
        dr.ellipse([mx - 30, my - 30, mx + 30, my + 30], outline=RED + (int(255 * grow),), width=5)
        dr.ellipse([mx - 11, my - 11, mx + 11, my + 11], fill=RED + (int(255 * grow),))
    count = "6" if variant != "seven" else "7"
    dr.text((540, 230), count, font=font("Anton-Regular.ttf", 160), fill=AMBER + (240,), anchor="mm")
    dr.text((540, 320), "SURFACES", font=font("BarlowCondensed-SemiBold.ttf", 40),
            fill=(150, 166, 190, 220), anchor="mm")


def room_corridor(img, t, lt, dur, variant):
    """The flat seen down its own hallway, in one-point perspective.

    This is the 16-second hold and the shot that has to prove the film has a *place*, so it is
    built geometrically rather than sketched: a corridor cross-section projected at depth z, with
    both walls, the ceiling, the floor, a runner rug, doorways with light under them, ceiling
    lamps, and the far window with rain still moving. Near the end one doorway goes dark.
    """
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 0, W, H], fill=(9, 12, 22, 255))

    VX, VY = 540, 900
    W0, H0 = 660, 800          # corridor half-width / half-height at the near plane
    K = 3.4                    # perspective strength

    def sc(z):                 # scale at depth z in [0,1]
        return 1.0 / (1.0 + K * z)

    def pt(u, v, z):           # u across [-1,1], v down [-1,1], z depth
        s_ = sc(z)
        return (VX + u * W0 * s_, VY + v * H0 * s_)

    # --- shell: ceiling, floor, both walls
    dr.polygon([pt(-1, -1, 0), pt(1, -1, 0), pt(1, -1, 1), pt(-1, -1, 1)], fill=(17, 22, 37, 255))   # ceiling
    dr.polygon([pt(-1, 1, 0), pt(1, 1, 0), pt(1, 1, 1), pt(-1, 1, 1)], fill=(30, 24, 27, 255))       # floor
    dr.polygon([pt(-1, -1, 0), pt(-1, 1, 0), pt(-1, 1, 1), pt(-1, -1, 1)], fill=(26, 32, 50, 255))   # left wall
    dr.polygon([pt(1, -1, 0), pt(1, 1, 0), pt(1, 1, 1), pt(1, -1, 1)], fill=(23, 29, 46, 255))       # right wall

    # --- the far end: a window with rain, and the street beyond it
    far = [pt(-0.52, -0.62, 1), pt(0.52, -0.62, 1), pt(0.52, 0.30, 1), pt(-0.52, 0.30, 1)]
    dr.polygon(far, fill=(18, 26, 48, 255), outline=(58, 70, 96, 255))
    fx0, fy0 = far[0]
    fx1, fy1 = far[2]
    dr.ellipse([fx0 + 26, fy0 + 26, fx0 + 96, fy0 + 96], fill=(226, 232, 244, 232))
    for i in range(5):
        dr.rectangle([fx0 + 14 + i * 34, fy0 + (fy1 - fy0) * 0.5, fx0 + 38 + i * 34, fy0 + (fy1 - fy0) * 0.66],
                     fill=LAMP + (120,))
    rain_lines(dr, int(fx0) + 6, int(fy0) + 6, int(fx1) - 6, int(fy1) - 6, t, density=8, alpha=60, speed=260)
    dr.line([(fx0 + fx1) / 2, fy0, (fx0 + fx1) / 2, fy1], fill=(58, 70, 96, 255), width=3)

    # --- runner rug down the floor, and skirting lines converging on the vanishing point
    dr.polygon([pt(-0.42, 1.0, 0), pt(0.42, 1.0, 0), pt(0.42, 1.0, 1), pt(-0.42, 1.0, 1)],
               fill=(38, 24, 26, 255))
    dr.polygon([pt(-0.42, 0.965, 0), pt(0.42, 0.965, 0), pt(0.42, 0.965, 1), pt(-0.42, 0.965, 1)],
               fill=(58, 34, 34, 255))
    for z in (0.06, 0.18, 0.31, 0.46, 0.63, 0.82):        # rug bands give the depth its rhythm
        dr.line([pt(-0.42, 1.0, z), pt(0.42, 1.0, z)], fill=(74, 46, 42, 255), width=max(1, int(7 * sc(z))))
    dr.line([pt(-1, 0.94, 0), pt(-1, 0.94, 1)], fill=(44, 52, 74, 255), width=5)
    dr.line([pt(1, 0.94, 0), pt(1, 0.94, 1)], fill=(44, 52, 74, 255), width=5)
    # wall/ceiling corner lines — without these the hallway floats
    dr.line([pt(-1, -1, 0), pt(-1, -1, 1)], fill=(40, 48, 70, 255), width=4)
    dr.line([pt(1, -1, 0), pt(1, -1, 1)], fill=(40, 48, 70, 255), width=4)
    dr.line([pt(-1, -1, 1), pt(1, -1, 1)], fill=(40, 48, 70, 255), width=3)
    dr.line([pt(-1, 1, 1), pt(1, 1, 1)], fill=(44, 36, 40, 255), width=3)

    # --- doorways down both walls. One goes dark late in the shot.
    def doorway(side, z0, wid, on, tone, openness=0.0):
        """A doorway is an opening, not a glowing panel: frame, recess, a door slab and the light
        under it. `openness` 0 = shut door with light beneath, 1 = door standing open on a lit room."""
        z1 = min(0.995, z0 + wid)
        u = side * 0.999
        top, bot = -0.56, 1.0
        a, b = pt(u, top, z0), pt(u, top, z1)
        c, d = pt(u, bot, z1), pt(u, bot, z0)
        dr.polygon([a, b, c, d], fill=(74, 62, 50, 255))                    # frame
        # recess: inset toward the vanishing point, shaded
        inset = 0.012
        ia = (a[0] + (VX - a[0]) * inset, a[1] + (VY - a[1]) * inset * 0.4)
        ib = (b[0] + (VX - b[0]) * inset, b[1] + (VY - b[1]) * inset * 0.4)
        ic = (c[0] + (VX - c[0]) * inset, c[1] + (VY - c[1]) * inset * 0.4)
        idd = (d[0] + (VX - d[0]) * inset, d[1] + (VY - d[1]) * inset * 0.4)
        dr.polygon([ia, ib, ic, idd], fill=(14, 18, 30, 255))
        if on:
            # the lit room beyond, seen through the opening
            if openness > 0:
                # an open door shows a dim room, not a lit panel: dark interior, one warm far wall
                dr.polygon([ia, ib, ic, idd], fill=(19, 23, 36, 255))
                h = (ic[1] - ia[1])
                dr.polygon([(ia[0] + (ib[0] - ia[0]) * 0.55, ia[1] + h * 0.10),
                            ib, ic,
                            (idd[0] + (ib[0] - ia[0]) * 0.55, idd[1] - h * 0.12)],
                           fill=(sum(tone[:3]) // 3, int(sum(tone[:3]) / 3 * 0.84),
                                 int(sum(tone[:3]) / 3 * 0.62), 132))
                # the door slab itself, standing open against the frame
                dr.polygon([ia, (ia[0] + (ib[0] - ia[0]) * 0.22, ia[1]),
                            (idd[0] + (ib[0] - ia[0]) * 0.22, idd[1]), idd],
                           fill=(70, 58, 46, 255))
            # a shut door with the light leaking under it
            dr.line([(idd[0], idd[1] - 4), (ic[0], ic[1] - 4)],
                    fill=(255, 219, 158, 240), width=max(3, int(10 * sc(z0))))
            # and spilling onto the runner
            sp = 0.16
            dr.polygon([(idd[0], idd[1]), (ic[0], ic[1]),
                        (ic[0] + (VX - ic[0]) * sp, ic[1] + 30 * sc(z1)),
                        (idd[0] + (VX - idd[0]) * sp, idd[1] + 30 * sc(z0))],
                       fill=(sum(tone[:3]) // 3, int(sum(tone[:3]) / 3 * 0.82), int(sum(tone[:3]) / 3 * 0.6), 62))

    warm, cool = (243, 203, 139, 255), (146, 170, 205, 255)
    # In the 16 s hold the doors go out one at a time — the flat going quiet, on screen.
    if variant == "hold":
        off_at = [3.6, 5.1, 7.0, 8.4, 10.2, 12.1]     # lights die across the hold, far to near
        lit = [not (lt > o) for o in off_at]
    elif variant == "dark_room":
        lit = [False] * 6
    else:
        lit = [True] * 6
    for (side, z0, wid, tone, op, k) in [(-1, 0.05, 0.10, warm, 0.0, 0), (-1, 0.26, 0.09, warm, 0.0, 1),
                                         (-1, 0.52, 0.08, warm, 0.0, 2), (1, 0.15, 0.09, cool, 0.6, 3),
                                         (1, 0.42, 0.08, warm, 0.0, 4), (1, 0.74, 0.07, cool, 0.5, 5)]:
        doorway(side, z0, wid, lit[k], tone, openness=op)

    # --- ceiling lights: small glowing panels, the source that makes the walls read
    for z in (0.18, 0.52):
        a, b = pt(-0.16, -0.99, z), pt(0.16, -0.99, z)
        rr = int(26 * sc(z))
        dr.ellipse([(a[0] + b[0]) / 2 - rr, a[1] - rr * 0.5,
                    (a[0] + b[0]) / 2 + rr, a[1] + rr * 0.5], fill=(255, 226, 172, 210))

    # --- foreground: a coat rack and the speaker, so the near plane is occupied
    dr.line([64, 1120, 92, 1760], fill=(28, 24, 22, 255), width=10)
    dr.polygon([[20, 1160], [110, 1160], [132, 1560], [0, 1560]], fill=(34, 30, 38, 255))
    dr.polygon([[34, 1180], [96, 1180], [112, 1400], [22, 1400]], fill=(27, 24, 30, 255))
    # the speaker stands clear of the rack, in front of the runner, above the caption band
    draw_speaker(img, 300, 1330, 100, ring=0.30 + 0.26 * math.sin(t * 0.9), listening=1.0)


def room_hook(img, t, lt, dur, variant):
    """End card. Not a black rectangle: the darkened flat stays visible underneath and the type
    sits over it, so the last thing the viewer sees is still the place."""
    room_corridor(img, t, lt, dur, "dark_room")
    ov = Image.new("RGBA", (W, H), (7, 10, 20, 0))
    ImageDraw.Draw(ov).rectangle([0, 0, W, H], fill=(7, 10, 20, 132))
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))

    dr = ImageDraw.Draw(img, "RGBA")
    rise = ease_out(lt / 0.9)
    # the series mark
    f_small = font("BarlowCondensed-SemiBold.ttf", 44)
    dr.text((W / 2, 470 + 26 * (1 - rise)), "NIGHT  TWO",
            font=f_small, fill=AMBER + (int(232 * rise),), anchor="mm")
    # the title
    f_big = font("Anton-Regular.ttf", 132)
    dr.text((W / 2, 616 + 30 * (1 - rise)), "IT ANSWERED",
            font=f_big, fill=WHITE + (int(255 * rise),), anchor="mm")
    dr.line([W / 2 - 190 * rise, 720, W / 2 + 190 * rise, 720], fill=RED + (int(220 * rise),), width=4)
    # the hook — my words, not the reference's
    f_hook = font("Anton-Regular.ttf", 76)
    y = 1400
    for line in ("TOMORROW,", "THE QUIET", "ANSWERS."):
        w = text_width(f_hook, line)
        dr.text(((W - w) / 2 + 6, y + 30 + 6), line, font=f_hook, fill=(0, 0, 0, int(210 * rise)))
        dr.text(((W - w) / 2, y + 30), line, font=f_hook, fill=AMBER + (int(250 * rise),))
        y += 92


ROOMS = {
    "window": room_window, "table": room_table, "wall": room_wall, "door": room_door,
    "kitchen": room_kitchen, "plan": room_plan, "corridor": room_corridor, "hook": room_hook,
}


def wrap(text, fnt, maxw=900):
    tmp = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if tmp.textlength(t, font=fnt) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_width(fnt, text):
    return ImageDraw.Draw(Image.new("RGB", (8, 8))).textlength(text, font=fnt)


def draw_caption(img, text, colour, alpha, room="", variant=""):
    """Bottom band only, and autoshrunk so the block clears any prop in that room. Cues could not
    be hand-tuned per shot here — they are generated from the measured narration — so the layout
    has to be safe for the worst case rather than the case I looked at."""
    if alpha <= 0.01:
        return
    dr = ImageDraw.Draw(img)
    # (font size allowed, band top, band bottom) per room; props live above band_top
    low_rooms = {"kitchen", "wall", "corridor"}
    if room in low_rooms:
        size, top, bottom = 80, 1500, 1830
    else:
        size, top, bottom = 88, 1460, 1830
    for _ in range(9):
        fnt = font("Anton-Regular.ttf", size)
        lines = wrap(text, fnt, 920)
        lh = int(size * 1.12)
        block_h = lh * len(lines)
        if block_h <= (bottom - top) and len(lines) <= 3:
            break
        size -= 6
    fnt = font("Anton-Regular.ttf", size)
    lines = wrap(text, fnt, 920)
    lh = int(size * 1.12)
    block_h = lh * len(lines)
    y = bottom - block_h                        # anchor the block to the bottom of the band
    for line in lines:
        w = text_width(fnt, line)
        x = (W - w) / 2
        dr.text((x + 6, y + 7), line, font=fnt, fill=(0, 0, 0, int(200 * alpha)))
        dr.text((x, y), line, font=fnt, fill=colour + (int(255 * alpha),))
        y += lh


def render_frame(t):
    idx = next(i for i, (a, b, _, _) in enumerate(SHOTS) if a <= t < b or (i == len(SHOTS) - 1 and t <= b))
    a, b, room, variant = SHOTS[idx]
    lt, dur = t - a, b - a

    arr = base(t)
    for (cx, cy, rad, col, st) in {
        "window": [(540, 740, 460, (0.55, 0.68, 0.95), 0.10), (760, 1180, 300, (1.0, 0.78, 0.42), 0.09)],
        "table": [(830, 600, 360, (1.0, 0.76, 0.36), 0.22), (470, 1120, 260, (0.42, 0.95, 0.62), 0.10)],
        "wall": [(540, 760, 480, (0.42, 0.95, 0.62), 0.13)],
        "door": [(540, 1380, 420, (1.0, 0.78, 0.40), 0.12)],
        "kitchen": [(180, 800, 380, (0.42, 0.95, 0.62), 0.11)],
        "plan": [(540, 960, 520, (0.30, 0.55, 0.95), 0.08)],
        "corridor": [(540, 900, 560, (1.0, 0.80, 0.50), 0.09)],
        "hook": [(540, 900, 520, (1.0, 0.80, 0.50), 0.06)],
    }[room]:
        light(arr, cx, cy, rad, col, st)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    body = ROOMS[room](img, t, lt, dur, variant)
    if body is not None:
        img = body

    draw_clock(img, t, alpha=1.0 if room != "hook" else 0.35)

    for (cs, ce, text, col) in CAPTIONS:
        if room == "hook" and cs > 55.0:
            break                      # the end card sets this line itself
        if cs <= t < ce:
            draw_caption(img, text, {"a": AMBER, "w": WHITE, "r": RED}[col],
                         ease_out((t - cs) / 0.16) * clamp((ce - t) / 0.16), room, variant)
            break

    if room != "hook":
        img = push(img, lt, dur, 0.06)

    out = np.asarray(img, dtype=np.float32) + GRAIN[int(round(t * FPS)) % len(GRAIN)][..., None]
    out = np.roll(out, (int(round(0.5 * math.cos(t * 0.8))), int(round(0.6 * math.sin(t * 0.9)))), axis=(0, 1))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- audio
SR = 48000


def synth_audio(nar_path, out_path):
    n = int(DUR * SR)
    t = np.arange(n) / SR
    mix = np.zeros((n, 2), np.float32)

    # drone: Dm pedal, low and slow
    for f0, g in ((73.4, 0.075), (110.0, 0.042), (146.8, 0.026)):
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.045 * t + f0)
        ph = np.sin(2 * np.pi * f0 * t)
        mix[:, 0] += g * ph * lfo
        mix[:, 1] += g * ph * np.roll(lfo, 520)

    # rain: stereo-filtered noise, present nearly the whole film
    rng = np.random.default_rng(77)
    noise = rng.normal(0, 1, n).astype(np.float32)
    rain = np.empty_like(noise)
    acc = 0.0
    for i in range(0, n, 4800):
        seg = noise[i:i + 4800]
        out = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc += 0.05 * (v - acc)
            out[j] = acc
        rain[i:i + 4800] = out
    rain *= 4.0
    mix[:, 0] += rain * 0.06
    mix[:, 1] += np.roll(rain, 700) * 0.06

    # sub hits on the escalation cuts
    for hit_t, gain in ((6.90, 0.42), (24.10, 0.55), (27.30, 0.62), (46.00, 0.85), (49.40, 0.70)):
        i0 = int(hit_t * SR)
        ln = int(1.8 * SR)
        tt = np.arange(ln) / SR
        sig = (np.sin(2 * np.pi * (44 * np.exp(-tt * 1.1) + 26) * tt) * np.exp(-tt * 2.8) * gain).astype(np.float32)
        mix[i0:i0 + ln, 0] += sig
        mix[i0:i0 + ln, 1] += sig

    # the 16-second hold: one string-like swell that never resolves
    i0, ln = int(30.0 * SR), int(16.0 * SR)
    tt = np.arange(ln) / SR
    env = np.minimum(1, tt / 6.0) * np.minimum(1, (16.0 - tt) / 3.0)
    swell = (np.sin(2 * np.pi * 73.4 * tt) * 0.5 + np.sin(2 * np.pi * 110.0 * tt) * 0.3 +
             np.sin(2 * np.pi * 146.8 * tt) * 0.18) * env * 0.30
    mix[i0:i0 + ln, 0] += swell.astype(np.float32)
    mix[i0:i0 + ln, 1] += (swell * 0.98).astype(np.float32)

    # kettle rise (19.9) and radio static (18.4)
    i0, ln = int(19.9 * SR), int(1.4 * SR)
    tt = np.arange(ln) / SR
    k = np.sin(2 * np.pi * (400 + 900 * tt) * tt) * np.minimum(1, tt / 0.8) * 0.06
    mix[i0:i0 + ln, 0] += k.astype(np.float32)
    i0, ln = int(18.4 * SR), int(1.5 * SR)
    rs = rng.normal(0, 1, ln).astype(np.float32) * 0.035
    mix[i0:i0 + ln, 0] += rs
    mix[i0:i0 + ln, 1] += rs * 0.9

    # voice
    voice = np.zeros(n, np.float32)
    if Path(nar_path).exists():
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(nar_path), "-ar", str(SR),
                            "-ac", "1", "-f", "f32le", "-"], capture_output=True)
        v = np.frombuffer(r.stdout, dtype=np.float32)
        voice[:min(n, len(v))] = v[:n]
    vf = np.zeros_like(voice)
    vf[1:] = voice[1:] - 0.86 * voice[:-1]
    voice = vf * 2.4
    mix[:, 0] += voice * 0.95
    mix[:, 1] += voice * 0.95

    mix = np.tanh(mix * 1.2) * 0.92
    peak = np.abs(mix).max()
    if peak > 0:
        mix *= 0.70 / peak
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    w = wave.open(str(out_path), "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
    w.close()
    print(f"AUDIO: {out_path} | {n / SR:.3f}s | peak {peak:.3f}")


def write_srt(path):
    def ts(s):
        return f"{int(s // 3600):02d}:{int((s % 3600) // 60):02d}:{s % 60:06.3f}".replace(".", ",")
    out = []
    for i, (cs, ce, text, _) in enumerate(CAPTIONS, 1):
        out += [str(i), f"{ts(cs)} --> {ts(ce)}", text, ""]
    Path(path).write_text("\n".join(out), encoding="utf-8")
    print(f"CAPTIONS: {path} | {len(CAPTIONS)} cues")


def main():
    WORK.mkdir(exist_ok=True)
    global CAPTIONS
    CAPTIONS = build_captions()
    init_layers()
    if "--test" in sys.argv:
        d = WORK / "probe"
        d.mkdir(exist_ok=True)
        for (a, b, room, variant) in SHOTS:
            render_frame((a + b) / 2).save(d / f"{room}_{variant}.png")
        print("probe frames written")
        return
    fd = WORK / "frames"
    fd.mkdir(exist_ok=True)
    for i in range(NF):
        render_frame(i / FPS).save(fd / f"f{i:04d}.png", compress_level=1)
        if i % 300 == 0:
            print(f"frame {i}/{NF}", flush=True)
    print(f"FRAMES: {NF}")
    synth_audio(WORK / "narration_master.wav", WORK / "mix.wav")
    write_srt(ROOT / "captions.srt")


if __name__ == "__main__":
    main()
