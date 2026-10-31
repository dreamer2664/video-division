#!/usr/bin/env python3
"""
generate.py — v06 "IT ANSWERED". Vertical master 1080x1920, 30 fps, 60.0 s.

Flat vector illustration in the reference grammar: dark room, soft radial pools of light, strong
vignette, one object per shot, one moving detail, hard cuts every 2-3 s, slow eased push-in.
Captions are the narration, burned in, 2-5 words per beat, colour-coded by meaning.

Deterministic: frame n is a pure function of n and the fixed seeds here.
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

BG = (11, 16, 32)
BG2 = (14, 21, 38)
AMBER = (245, 209, 78)
LAMP = (245, 197, 66)
RED = (226, 69, 60)
WHITE = (236, 240, 248)
DIM = (138, 154, 180)
GREEN = (124, 242, 156)

CAPTIONS = [
    (1,  0.30, 3.15, "IT'S 2:14 IN THE MORNING.", "a"),
    (2,  3.10, 6.25, "ONE SMART SPEAKER IN THIS FLAT.", "a"),
    (3,  6.28, 7.80, "ONE. THE COUNT IS ONE.", "a"),
    (4,  7.81, 10.45, "IT HAS NEVER BEEN TOLD MY NAME.", "w"),
    (5, 10.49, 12.60, "IT SAID MY NAME.", "r"),
    (6, 12.68, 14.62, "SO I MADE A RULE.", "w"),
    (7, 14.67, 16.80, "I DON'T ANSWER IT.", "w"),
    (8, 16.87, 18.20, "ONE SPEAKER.", "a"),
    (9, 18.21, 19.47, "ONE FLAT.", "a"),
    (10, 19.48, 20.95, "ONE PERSON.", "a"),
    (11, 21.02, 23.35, "THAT'S THE WHOLE COUNT.", "a"),
    (12, 23.42, 26.80, "IT STARTED ANSWERING MY THOUGHTS.", "r"),
    (13, 26.87, 29.50, "A QUESTION I NEVER SAID OUT LOUD.", "r"),
    (14, 29.58, 33.85, "ANSWERED. IN MY OWN WORDS.", "r"),
    (15, 33.93, 35.92, "I CHECKED THE MICROPHONE.", "w"),
    (16, 35.94, 37.92, "IT WAS SWITCHED OFF.", "w"),
    (17, 37.99, 41.90, "SO IT WAS NEVER THE MICROPHONE.", "w"),
    (18, 41.96, 44.70, "IT ONLY EVER HEARD ONE VOICE.", "a"),
    (19, 44.74, 47.02, "MINE.", "a"),
    (20, 47.09, 49.10, "IT DIDN'T LEARN WHAT I THOUGHT.", "w"),
    (21, 49.16, 55.10, "IT LEARNED THE PHRASE I SAY ALONE.", "r"),
    (22, 56.00, 60.00, "NIGHT 2", "w"),
]

SHOTS = [
    (0.00, 3.10, "flat_night"),
    (3.10, 6.25, "speaker_close"),
    (6.25, 7.81, "count_one"),
    (7.81, 10.49, "ring_lights"),
    (10.49, 12.68, "name_appears"),
    (12.68, 14.67, "rule"),
    (14.67, 16.87, "dont_answer"),
    (16.87, 18.21, "count_speaker"),
    (18.21, 19.48, "count_flat"),
    (19.48, 21.02, "count_person"),
    (21.02, 23.42, "count_whole"),
    (23.42, 26.87, "thought_bubble"),
    (26.87, 29.58, "unspoken"),
    (29.58, 33.93, "answered"),
    (33.93, 37.99, "mic_off"),
    (37.99, 41.96, "not_the_mic"),
    (41.96, 44.74, "one_voice"),
    (44.74, 47.09, "mine"),
    (47.09, 49.16, "going_dark"),
    (49.16, 55.10, "the_phrase"),
    (55.10, 60.00, "end_card"),
]

VIG = None
GRAIN_BANK = None


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), int(size))


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_in_out(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def ease_out(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def init_layers():
    """Vignette + a bank of quarter-res noise fields. A different grain field every frame is
    what stops a held illustration reading as a frozen frame; static grain produced 20 holds of
    up to 1.7 s under freezedetect on the first build."""
    global VIG, GRAIN_BANK
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (x - W / 2) / (W / 2)
    dy = (y - H / 2) / (H / 2)
    r = np.sqrt(dx * dx + dy * dy) / 1.35
    VIG = np.clip(1.0 - 0.78 * r ** 1.7, 0.18, 1.0)
    rng = np.random.default_rng(11)
    bank = []
    for _ in range(12):
        lr = rng.normal(0, 1.0, (H // 4, W // 4)).astype(np.float32)
        im = Image.fromarray(lr, mode="F").resize((W, H), Image.BILINEAR)
        bank.append((np.asarray(im, dtype=np.float32) * 1.7).astype(np.float32))
    GRAIN_BANK = bank


def base_frame(t):
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    drift = 3.0 * math.sin(t * 0.7)
    arr = np.empty((H, W, 3), np.float32)
    for i in range(3):
        arr[..., i] = (BG[i] + (BG2[i] - BG[i]) * yy) + drift
    arr *= VIG[..., None]
    return arr


def add_light(arr, cx, cy, radius, colour, strength):
    y0, y1 = max(0, int(cy - radius * 2.2)), min(H, int(cy + radius * 2.2))
    x0, x1 = max(0, int(cx - radius * 2.2)), min(W, int(cx + radius * 2.2))
    if y1 <= y0 or x1 <= x0:
        return
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (radius * radius)) * 1.9) * strength
    for i in range(3):
        arr[y0:y1, x0:x1, i] += g * colour[i]


def wrap(text, fnt, maxw):
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def draw_caption(img, text, colour, alpha):
    if alpha <= 0.01:
        return
    dr = ImageDraw.Draw(img)
    size = 88
    fnt = font("Anton-Regular.ttf", size)
    lines = wrap(text, fnt, 940)
    while len(lines) > 2 and size > 62:
        size -= 6
        fnt = font("Anton-Regular.ttf", size)
        lines = wrap(text, fnt, 940)
    lh = int(size * 1.14)
    y = 1420 - lh * len(lines) // 2
    for line in lines:
        w = dr.textlength(line, font=fnt)
        x = (W - w) / 2
        dr.text((x + 5, y + 6), line, font=fnt, fill=(0, 0, 0, int(190 * alpha)))
        dr.text((x, y), line, font=fnt, fill=colour + (int(255 * alpha),))
        y += lh


def draw_speaker(img, cx, cy, r, ring=0.0, listening=0.0):
    dr = ImageDraw.Draw(img, "RGBA")
    bw, bh = r * 1.55, r * 1.05
    x0, y0 = cx - bw / 2, cy - bh / 2
    dr.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(r * 0.30),
                         fill=(24, 30, 46, 255), outline=(46, 56, 78, 255), width=3)
    dr.ellipse([x0, y0 - r * 0.16, x0 + bw, y0 + r * 0.30], fill=(34, 42, 62, 255),
               outline=(58, 70, 96, 255), width=3)
    for i in range(6):
        for j in range(3):
            gx = x0 + bw * (0.20 + 0.12 * i)
            gy = y0 + bh * (0.42 + 0.15 * j)
            dr.ellipse([gx - 2.5, gy - 2.5, gx + 2.5, gy + 2.5], fill=(52, 62, 86, 255))
    if ring > 0:
        rc = GREEN if listening > 0 else AMBER
        dr.ellipse([x0 - 6, y0 - r * 0.22, x0 + bw + 6, y0 + r * 0.36],
                   outline=rc + (int(255 * ring),), width=int(4 + 3 * listening))


def draw_clock(img, t, alpha=1.0):
    dr = ImageDraw.Draw(img, "RGBA")
    f1 = font("Anton-Regular.ttf", 96)
    f2 = font("BarlowCondensed-SemiBold.ttf", 34)
    dr.text((96, 160), "2:14", font=f1, fill=RED + (int(235 * alpha),))
    dr.text((98, 160 + 96 * 1.16), "AM", font=f2, fill=(190, 128, 124, int(210 * alpha)))
    dr.text((98 + dr.textlength("AM", font=f2) + 14, 160 + 96 * 1.16), "31 OCT",
            font=f2, fill=(150, 122, 126, int(190 * alpha)))
    if int(t * 2) % 2 == 0:
        dr.rectangle([96 + 34, 160 + 29, 96 + 44, 160 + 39], fill=RED + (int(235 * alpha),))


# ---------------------------------------------------------------- shots
def s_flat_night(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([0, 1080, W, H], fill=(13, 18, 32, 255))
    dr.line([0, 1080, W, 1080], fill=(30, 38, 56, 255), width=3)
    wx, wy, ww, wh = 640, 430, 300, 400
    dr.rectangle([wx - 10, wy - 10, wx + ww + 10, wy + wh + 10], fill=(16, 22, 38, 255))
    dr.rectangle([wx, wy, wx + ww, wy + wh], fill=(22, 34, 58, 255), outline=(62, 80, 110, 255), width=6)
    for i in range(1, 3):
        dr.line([wx + ww * i / 3, wy, wx + ww * i / 3, wy + wh], fill=(52, 66, 92, 255), width=5)
    dr.line([wx, wy + wh / 2, wx + ww, wy + wh / 2], fill=(52, 66, 92, 255), width=5)
    for i in range(18):
        sx = wx + ((i * 97 + int(t * 210)) % ww)
        sy = wy + ((i * 61 + int(t * 470)) % wh)
        dr.line([sx, sy, sx - 4, sy + 20], fill=(104, 130, 172, 110), width=2)
    dr.ellipse([wx + 196, wy + 60, wx + 244, wy + 108], fill=(206, 218, 238, 200))
    dr.rectangle([110, 1010, 560, 1180], fill=(30, 24, 24, 255))
    dr.rectangle([110, 1010, 560, 1030], fill=(40, 32, 30, 255))
    dr.rectangle([150, 1180, 176, 1300], fill=(24, 19, 19, 255))
    dr.rectangle([494, 1180, 520, 1300], fill=(24, 19, 19, 255))
    dr.polygon([[700, 960], [790, 960], [770, 900], [720, 900]], fill=(52, 40, 30, 255))
    dr.rectangle([738, 960, 752, 1010], fill=(42, 34, 28, 255))
    dr.ellipse([712, 878, 778, 924], fill=(255, 206, 128, 210))
    dr.rectangle([880, 940, 1000, 1010], fill=(20, 26, 40, 255))
    dr.rectangle([880, 800, 906, 940], fill=(20, 26, 40, 255))
    dr.rectangle([870, 1010, 884, 1180], fill=(17, 22, 35, 255))
    dr.rectangle([996, 1010, 1010, 1180], fill=(17, 22, 35, 255))
    dr.ellipse([190, 1240, 890, 1420], fill=(19, 25, 40, 255))
    draw_speaker(img, 320, 936, 66, ring=0.30 + 0.25 * math.sin(t * 2.1))


def s_speaker_close(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rectangle([150, 1080, 930, 1116], fill=(38, 28, 24, 255))
    draw_speaker(img, 540, 985, 175, ring=0.55 + 0.35 * math.sin(t * 2.4))
    dr.text((540, 1180), "ONE DEVICE", font=font("BarlowCondensed-SemiBold.ttf", 52),
            fill=(138, 154, 180, 210), anchor="mm")


def s_count(img, t, lt, dur, glyph="speaker"):
    cols = rows = 100
    box = {"speaker": (140, 940, 660, 1220), "flat": (60, 1020, 560, 1060),
           "person": (200, 880, 760, 1240), "sum": (90, 990, 620, 1320)}[glyph]
    x0, x1, y0, y1 = box
    sub = 10
    yy, xx = np.mgrid[0:sub, 0:sub]
    dot = (((xx - sub / 2 + 0.5) ** 2 + (yy - sub / 2 + 0.5) ** 2) <= (sub * 0.30) ** 2)
    cell = np.zeros((sub, sub, 4), np.uint8)
    cell[..., 0], cell[..., 1], cell[..., 2] = 46, 58, 80
    cell[..., 3] = np.where(dot, 255, 0)
    g = np.tile(cell, (rows, cols, 1))
    layer = Image.fromarray(g, "RGBA").resize((x1 - x0, y1 - y0), Image.NEAREST)
    img.paste(layer, (x0, y0), layer)

    dr = ImageDraw.Draw(img, "RGBA")
    cx = x0 + sub / 2
    cy = y0 + sub / 2
    dr.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=(245, 197, 66, 40))
    dr.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(245, 197, 66, 255))

    gy = y0 - 210
    if glyph == "speaker":
        draw_speaker(img, 540, gy, 58, ring=0.9, listening=1.0)
        label = "SPEAKER"
    elif glyph == "flat":
        d2 = ImageDraw.Draw(img, "RGBA")
        d2.rectangle([440, gy - 58, 640, gy + 58], outline=AMBER + (230,), width=5)
        d2.line([430, gy - 58, 540, gy - 130], fill=AMBER + (230,), width=5)
        d2.line([650, gy - 58, 540, gy - 130], fill=AMBER + (230,), width=5)
        d2.rectangle([515, gy + 12, 565, gy + 58], fill=AMBER + (150,))
        label = "FLAT"
    elif glyph == "person":
        d2 = ImageDraw.Draw(img, "RGBA")
        d2.ellipse([510, gy - 100, 570, gy - 40], fill=AMBER + (230,))
        d2.rounded_rectangle([488, gy - 28, 592, gy + 62], radius=24, fill=AMBER + (230,))
        label = "PERSON"
    else:
        label = "THE WHOLE COUNT"
    dr.text((540, gy - 265), "1", font=font("Anton-Regular.ttf", 86), fill=AMBER + (255,), anchor="mm")
    dr.text((540, gy - 170), label, font=font("BarlowCondensed-SemiBold.ttf", 46),
            fill=(158, 172, 196, 235), anchor="mm")


def s_ring(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    cx, cy = 540, 860
    pulse = 0.5 + 0.5 * math.sin(lt * 5.2)
    for k in range(3):
        rr = 150 + k * 46 + 18 * pulse
        a = int((110 - k * 30) * (0.55 + 0.45 * pulse))
        dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=GREEN + (a,), width=4)
    draw_speaker(img, cx, cy + 40, 120, ring=1.0, listening=1.0)


def s_name(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    draw_speaker(img, 300, 1180, 96, ring=1.0, listening=1.0)
    f = font("Anton-Regular.ttf", 118)
    name = "DANIEL"
    reveal = ease_out((lt - 0.15) / 0.55)
    n = max(0, min(len(name), int(len(name) * reveal + 0.001)))
    full_w = dr.textlength(name, font=f)
    x0 = 700 - full_w / 2
    if n:
        dr.text((x0, 1130), name[:n], font=f, fill=GREEN + (255,), anchor="lm")
    if reveal >= 1.0 and int(t * 2) % 2 == 0:
        dr.rectangle([x0 + full_w + 8, 1088, x0 + full_w + 18, 1172], fill=GREEN + (200,))
    dr.text((700, 1215), "NEVER TOLD TO IT", font=font("BarlowCondensed-SemiBold.ttf", 46),
            fill=(150, 166, 190, 200), anchor="mm")


def s_rule(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    dr.text((540, 900), "THE RULE", font=font("Anton-Regular.ttf", 108), fill=WHITE + (235,), anchor="mm")
    dr.line([330, 1010, 750, 1010], fill=AMBER + (180,), width=4)
    dr.text((540, 1090), "DO NOT ANSWER IT", font=font("BarlowCondensed-Bold.ttf", 62),
            fill=AMBER + (235,), anchor="mm")


def s_dont_answer(img, t, lt, dur):
    draw_speaker(img, 540, 880, 110, ring=0.5 + 0.5 * math.sin(t * 3.0), listening=0.3)
    dr = ImageDraw.Draw(img, "RGBA")
    dr.text((540, 1040), "IT IS STILL LISTENING", font=font("BarlowCondensed-SemiBold.ttf", 52),
            fill=RED + (220,), anchor="mm")


def s_thought(img, t, lt, dur):
    draw_speaker(img, 540, 1120, 118, ring=1.0, listening=1.0)
    dr = ImageDraw.Draw(img, "RGBA")
    f = font("BarlowCondensed-Bold.ttf", 54)
    for i, m in enumerate(["YOU SHOULD SLEEP.", "THE DOOR IS LOCKED.", "YOU ALREADY KNOW."]):
        app = ease_out((lt - 0.4 - i * 0.75) / 0.5)
        if app <= 0:
            continue
        y = 300 + i * 150 - 40 * (1 - app)
        w = dr.textlength(m, font=f) + 70
        dr.rounded_rectangle([540 - w / 2, y - 42, 540 + w / 2, y + 42], radius=26,
                             fill=(18, 26, 42, int(240 * app)),
                             outline=GREEN + (int(180 * app),), width=3)
        dr.text((540, y), m, font=f, fill=GREEN + (int(255 * app),), anchor="mm")


def s_unspoken(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    f = font("BarlowCondensed-Bold.ttf", 58)
    dr.text((540, 700), "USER: —", font=f, fill=(110, 126, 152, 200), anchor="mm")
    dr.text((540, 790), 'ASSISTANT: "YOU SHOULD SLEEP."', font=f, fill=GREEN + (235,), anchor="mm")
    dr.line([170, 880, 910, 880], fill=(46, 56, 78, 255), width=3)
    dr.text((540, 960), "NO QUESTION IN THE LOG", font=font("BarlowCondensed-SemiBold.ttf", 48),
            fill=RED + (220,), anchor="mm")


def s_answered(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    f = font("BarlowCondensed-Bold.ttf", 56)
    for i, (who, what) in enumerate([("USER", "…"), ("ASSISTANT", "IN MY OWN WORDS"), ("USER", "…")]):
        y = 800 + i * 150
        col = GREEN if who == "ASSISTANT" else (110, 126, 152)
        dr.text((180, y), who, font=font("BarlowCondensed-SemiBold.ttf", 40), fill=col + (200,), anchor="lm")
        dr.text((180, y + 52), what, font=f, fill=col + (235,), anchor="lm")
    draw_speaker(img, 540, 1150, 110, ring=1.0, listening=1.0)


def s_mic_off(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    dr.rounded_rectangle([340, 900, 740, 1010], radius=55, outline=(70, 84, 110, 255), width=6)
    dr.ellipse([378, 913, 462, 997], fill=(60, 72, 96, 255))
    dr.text((540, 1090), "MIC  OFF", font=font("BarlowCondensed-SemiBold.ttf", 48),
            fill=DIM + (220,), anchor="mm")
    draw_speaker(img, 540, 1180, 115, ring=1.0, listening=1.0)


def s_not_the_mic(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    dr.ellipse([420, 700, 660, 940], outline=(90, 104, 130, 255), width=6)
    dr.line([440, 720, 640, 920], fill=RED + (255,), width=12)
    dr.line([640, 720, 440, 920], fill=RED + (255,), width=12)
    dr.text((540, 1060), "NOT THE MIC", font=font("Anton-Regular.ttf", 86), fill=WHITE + (240,), anchor="mm")
    draw_speaker(img, 540, 1150, 110, ring=1.0, listening=1.0)


def s_one_voice(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    cy, n = 820, 120
    for i in range(n):
        x = 90 + i * (900 / (n - 1))
        p = i / (n - 1)
        a = (0.5 + 0.5 * math.sin(i * 0.55 + t * 6.0)) * math.sin(math.pi * p) ** 1.5
        hgt = 12 + 90 * a
        dr.line([x, cy - hgt, x, cy + hgt], fill=(245, 197, 66, 210), width=4)
    dr.text((540, 1010), "ONE VOICE IN THE ROOM", font=font("BarlowCondensed-SemiBold.ttf", 50),
            fill=(150, 166, 190, 210), anchor="mm")


def s_mine(img, t, lt, dur):
    sc = 1.0 + 0.05 * ease_out(lt / 0.6)
    ImageDraw.Draw(img, "RGBA").text((540, 780), "MINE", font=font("Anton-Regular.ttf", int(200 * sc)),
                                     fill=AMBER + (255,), anchor="mm")


def s_going_dark(img, t, lt, dur):
    """The ring dims to nothing. The room does not change. The absence is the picture."""
    dr = ImageDraw.Draw(img, "RGBA")
    die = clamp(lt / 1.6)
    ring = max(0.0, 1.0 - die)
    draw_speaker(img, 540, 1000, 120, ring=ring, listening=1.0 if ring > 0 else 0.0)
    if ring > 0.02:
        rr = 150 + 60 * (1 - ring)
        dr.ellipse([540 - rr, 1000 - rr, 540 + rr, 1000 + rr], outline=GREEN + (int(120 * ring),), width=3)
    dr.text((540, 1240), "THE RING GOES OUT", font=font("BarlowCondensed-SemiBold.ttf", 50),
            fill=(120, 136, 162, int(200 * die)), anchor="mm")


def s_the_phrase(img, t, lt, dur):
    draw_speaker(img, 540, 1155, 92, ring=0.7 + 0.3 * math.sin(t * 2.2), listening=0.6)
    dr = ImageDraw.Draw(img, "RGBA")
    dr.text((540, 720), "ONE PHRASE", font=font("BarlowCondensed-SemiBold.ttf", 52),
            fill=DIM + (200,), anchor="mm")
    for i, (txt, col) in enumerate([("IT SHOULD", WHITE), ("NEVER HAVE", RED), ("LEARNED", RED)]):
        dr.text((540, 850 + i * 135), txt, font=font("Anton-Regular.ttf", 118), fill=col + (240,), anchor="mm")


def s_end_card(img, t, lt, dur):
    dr = ImageDraw.Draw(img, "RGBA")
    fade = ease_out(lt / 0.8)
    dr.text((540, 780), "IT ANSWERED", font=font("Anton-Regular.ttf", 132), fill=WHITE + (int(255 * fade),), anchor="mm")
    dr.text((540, 930), "ONE SPEAKER. ONE QUESTION:", font=font("BarlowCondensed-SemiBold.ttf", 52),
            fill=(150, 166, 190, int(220 * fade)), anchor="mm")
    dr.text((540, 1000), "WHAT DID IT LEARN?", font=font("BarlowCondensed-Bold.ttf", 64),
            fill=AMBER + (int(235 * fade),), anchor="mm")
    dr.ellipse([530, 1105, 550, 1125], fill=(245, 197, 66, int(200 * fade)))


SHOT_FN = {
    "flat_night": s_flat_night, "speaker_close": s_speaker_close,
    "count_one": lambda i, t, l, d: s_count(i, t, l, d, "speaker"),
    "ring_lights": s_ring, "name_appears": s_name, "rule": s_rule,
    "dont_answer": s_dont_answer,
    "count_speaker": lambda i, t, l, d: s_count(i, t, l, d, "speaker"),
    "count_flat": lambda i, t, l, d: s_count(i, t, l, d, "flat"),
    "count_person": lambda i, t, l, d: s_count(i, t, l, d, "person"),
    "count_whole": lambda i, t, l, d: s_count(i, t, l, d, "sum"),
    "thought_bubble": s_thought, "unspoken": s_unspoken, "answered": s_answered,
    "mic_off": s_mic_off, "not_the_mic": s_not_the_mic, "one_voice": s_one_voice,
    "mine": s_mine, "going_dark": s_going_dark, "the_phrase": s_the_phrase,
    "end_card": s_end_card,
}


def draw_timecode(img, t):
    dr = ImageDraw.Draw(img, "RGBA")
    x0, x1, y = 90, 990, 1700
    p = clamp(t / DUR)
    dr.rounded_rectangle([x0, y - 3, x1, y + 3], radius=3, fill=(40, 50, 70, 255))
    dr.rounded_rectangle([x0, y - 3, x0 + (x1 - x0) * p, y + 3], radius=3, fill=AMBER + (255,))
    f = font("BarlowCondensed-SemiBold.ttf", 40)
    dr.text((x0, y + 30), "0:00", font=f, fill=(120, 136, 162, 200), anchor="lt")
    dr.text((x1, y + 30), "1:00", font=f, fill=(120, 136, 162, 200), anchor="rt")


LIGHTS = {
    "flat_night": [(780, 720, 300, (1.0, 0.80, 0.42), 0.16), (550, 1010, 190, (1.0, 0.72, 0.30), 0.10)],
    "speaker_close": [(540, 1010, 420, (1.0, 0.74, 0.34), 0.15)],
    "dont_answer": [(540, 880, 420, (1.0, 0.74, 0.34), 0.15)],
    "mic_off": [(540, 1050, 420, (1.0, 0.74, 0.34), 0.15)],
    "the_phrase": [(540, 1050, 420, (1.0, 0.74, 0.34), 0.13)],
    "end_card": [(540, 960, 420, (1.0, 0.74, 0.34), 0.12)],
    "going_dark": [(540, 1000, 420, (0.42, 0.95, 0.62), 0.10)],
}


def render_frame(t):
    idx = next(i for i, (a, b, _) in enumerate(SHOTS) if a <= t < b or (i == len(SHOTS) - 1 and t <= b))
    a, b, kind = SHOTS[idx]
    lt = t - a
    arr = base_frame(t)
    for (cx, cy, rad, col, st) in LIGHTS.get(kind, [(540, 960, 420, (1.0, 0.78, 0.36), 0.10)]):
        add_light(arr, cx, cy, rad, col, st)
    if kind in ("ring_lights", "name_appears", "thought_bubble", "answered", "not_the_mic", "one_voice"):
        add_light(arr, 540, 980, 380, (0.42, 0.95, 0.62), 0.11)
    if kind.startswith("count"):
        add_light(arr, 540, 960, 480, (1.0, 0.78, 0.36), 0.07)
    if kind in ("rule", "unspoken", "mine"):
        add_light(arr, 540, 960, 420, (0.85, 0.88, 1.0), 0.07)

    arr = arr * (1.0 - 0.16 * (1 - ease_out(min(lt / 0.25, 1.0))))
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    SHOT_FN[kind](img, t, lt, b - a)

    if kind not in ("rule", "unspoken", "mine", "end_card"):
        draw_clock(img, t)
    for (_, cs, ce, text, col) in CAPTIONS:
        if cs <= t < ce:
            draw_caption(img, text, {"a": AMBER, "w": WHITE, "r": RED}[col],
                         clamp((t - cs) / 0.18) * clamp((ce - t) / 0.18))
            break
    draw_timecode(img, t)

    out = np.asarray(img, dtype=np.float32) + GRAIN_BANK[int(round(t * FPS)) % len(GRAIN_BANK)][..., None]
    out = np.roll(out, (int(round(0.5 * math.cos(t * 0.7))), int(round(0.6 * math.sin(t * 0.9)))), axis=(0, 1))
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- audio
SR = 48000


def synth_audio(nar_path, out_path):
    n = int(DUR * SR)
    t = np.arange(n) / SR
    mix = np.zeros((n, 2), np.float32)
    for f0, g in ((55.0, 0.085), (82.5, 0.045), (110.0, 0.030)):
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + f0)
        ph = np.sin(2 * np.pi * f0 * t)
        mix[:, 0] += g * ph * lfo
        mix[:, 1] += g * ph * np.roll(lfo, 400)

    rng = np.random.default_rng(4242)
    noise = rng.normal(0, 1, n).astype(np.float32)
    lp = np.empty_like(noise)
    acc = 0.0
    for i in range(0, n, 4800):
        seg = noise[i:i + 4800]
        out = np.empty_like(seg)
        for j, v in enumerate(seg):
            acc += 0.02 * (v - acc)
            out[j] = acc
        lp[i:i + 4800] = out
    lp *= 6.0
    mix[:, 0] += lp * 0.05
    mix[:, 1] += np.roll(lp, 900) * 0.05

    for hit_t, gain in ((8.00, 0.55), (23.42, 0.62), (37.99, 0.70), (49.16, 0.80)):
        i0 = int(hit_t * SR)
        ln = int(1.6 * SR)
        tt = np.arange(ln) / SR
        sig = (np.sin(2 * np.pi * (41 * np.exp(-tt * 1.2) + 28) * tt) * np.exp(-tt * 3.2) * gain).astype(np.float32)
        mix[i0:i0 + ln, 0] += sig
        mix[i0:i0 + ln, 1] += sig

    for chime_t in (8.00, 34.0):
        i0 = int(chime_t * SR)
        ln = int(1.4 * SR)
        tt = np.arange(ln) / SR
        s = (np.sin(2 * np.pi * 1244 * tt) * 0.5 + np.sin(2 * np.pi * 1661 * tt) * 0.35) * np.exp(-tt * 2.6) * 0.16
        mix[i0:i0 + ln, 0] += s.astype(np.float32)
        mix[i0:i0 + ln, 1] += (s * 0.96).astype(np.float32)

    for ct in (17.90, 19.48, 21.02, 22.40):
        i0 = int(ct * SR)
        ln = int(0.06 * SR)
        tt = np.arange(ln) / SR
        click = (np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 90) * 0.20).astype(np.float32)
        mix[i0:i0 + ln, 0] += click
        mix[i0:i0 + ln, 1] += click * 0.9

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

    mix = np.tanh(mix * 1.25) * 0.92
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
    for i, (_, cs, ce, text, _) in enumerate(CAPTIONS, 1):
        out += [str(i), f"{ts(cs)} --> {ts(ce)}", text, ""]
    Path(path).write_text("\n".join(out), encoding="utf-8")
    print(f"CAPTIONS: {path} | {len(CAPTIONS)} cues")


def main():
    WORK.mkdir(exist_ok=True)
    init_layers()
    if "--test" in sys.argv:
        d = WORK / "probe"
        d.mkdir(exist_ok=True)
        for t in (1.5, 4.5, 6.9, 9.0, 11.5, 13.6, 15.9, 17.5, 20.2, 22.0, 25.0, 28.5,
                  31.5, 35.5, 39.5, 43.0, 46.0, 48.4, 52.0, 58.0):
            render_frame(t).save(d / f"t{t:05.1f}.png")
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
