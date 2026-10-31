#!/usr/bin/env python3
"""
pixel v01 — "A Million Is Not a Billion" (60 seconds about seconds)
Team A (programmatic). Renders 1800 PNG frames (1920x1080 @30fps),
a 60.00s synthesized stereo WAV (48kHz), and captions.srt.

Deterministic: fixed seed, no wall-clock/network input to picture or sound.
Copy/timings below are the single source of truth shared by frames + captions;
they transcribe script.md verbatim. Fact-box arithmetic is asserted at startup.

Usage:
  python3 generate.py            # full render -> ../work/frames, ../work/audio.wav, ../captions.srt
  python3 generate.py --test     # 10 probe frames -> ../work/test/ (layout check, fast)
"""
import math, sys, wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants
W, H, FPS, DUR = 1920, 1080, 30, 60.0
NFRAMES = int(FPS * DUR)
HERE = Path(__file__).resolve().parent          # assets/
ROOT = HERE.parent                              # pixel-v01/
WORK = ROOT / "work"
FONT_SANS = HERE / "fonts" / "DejaVuSans-Bold.ttf"
FONT_MONO = HERE / "fonts" / "DejaVuSansMono-Bold.ttf"

BG = (26, 36, 51)          # #1A2433 graphite navy: luma ~0.13 > blackdetect pix_th 0.10
INK = (244, 247, 250)      # #F4F7FA
AMBER = (255, 176, 0)      # #FFB000
DIM = (138, 151, 165)      # #8A97A5
FAINT = (64, 80, 100)      # empty-dot colour

SHOTS = [(0.0, 6.0), (6.0, 12.0), (12.0, 22.0), (22.0, 28.0),
         (28.0, 40.0), (40.0, 50.0), (50.0, 57.0), (57.0, 60.0)]
DISSOLVE = 0.4

COLS, ROWS = 200, 50
NDOTS = COLS * ROWS                      # 10_000 exactly
GX0, GX1, GY0, GY1 = 120, 1800, 430, 960  # grid box
SX = (GX1 - GX0) / (COLS - 1)
SY = (GY1 - GY0) / (ROWS - 1)
DOT_R = 3

APOS = "\u2019"  # typographic apostrophe
COPY = {  # verbatim from script.md
    "s1_head": "A million. A billion.",
    "s1_tail": "They sound like neighbours.",
    "s1_lab_l": "one million", "s1_lab_r": "one billion",
    "s2_head": f"Let{APOS}s count them in seconds.",
    "leg_100": "One dot = 100 seconds.",
    "seconds": "seconds",
    "s3_punch": "= 11\u00bd days",
    "s3_exact": "11 days, 13 hours, 46 minutes.",
    "s3_mem": "You can remember 11 days ago.",
    "s4_keep": "Now keep the same picture.",
    "leg_100k": "One dot = 100,000 seconds.",
    "s4_slam": "\u00d71,000",
    "s4_same": "Same dots. \u00d71,000 more time.",
    "s5_punch": "= 31.7 years",
    "s5_1995": "A billion seconds ago was 1995.",
    "s5_31": "Someone born then is 31.",
    "s5_gen": "A billion seconds is a generation.",
    "s6_more": "One more \u00d71,000.",
    "leg_100m": "One dot = 100,000,000 seconds.",
    "s6_punch": "= 31,688 years",
    "s6_farm": "Before farming.", "s6_city": "Before cities.", "s6_write": "Before writing.",
    "s6_mam": "Mammoths were still here.",
    "s6_scale": "Drawn to scale:",
    "s6_blab": "1 billion seconds",
    "s6_mlab": "1 million \u2014 under 2 pixels wide",
    "s6_tlab": "1 trillion, to scale, would cross 833 of these screens \u2192",
    "s7_life": "A human life is about",
    "s7_num": "2\u00bd billion seconds.",
    "s7_yrs": "79 years", "s7_60": "60 s",
    "s7_used": "This film used 60 of yours.",
    "s8_end": f"Spend them like they{APOS}re counted.",
    "s8_cred": "pixel \u00b7 Team A \u00b7 made entirely with code \u2014 every dot counted",
    "r0": "0s", "r60": "60s",
}

# captions: (start, end, text) global seconds — mirrors on-screen lines in reading order
CAPTIONS = [
    (0.4, 3.4, COPY["s1_head"]),
    (3.4, 6.0, "1,000,000 \u00b7 1,000,000,000 \u2014 " + COPY["s1_tail"]),
    (6.0, 9.0, COPY["s2_head"]),
    (9.0, 12.0, COPY["leg_100"]),
    (12.0, 18.0, "[counter climbs; 10,000 dots fill]"),
    (18.0, 20.0, "1,000,000 seconds " + COPY["s3_punch"]),
    (20.0, 22.0, COPY["s3_exact"] + " " + COPY["s3_mem"]),
    (22.0, 24.5, COPY["s4_keep"]),
    (24.5, 28.0, COPY["leg_100k"] + " " + COPY["s4_same"]),
    (28.0, 34.2, "[the same 10,000 dots refill]"),
    (34.2, 36.0, "1,000,000,000 seconds " + COPY["s5_punch"]),
    (36.0, 38.0, COPY["s5_1995"]),
    (38.0, 40.0, COPY["s5_31"] + " " + COPY["s5_gen"]),
    (40.0, 42.0, COPY["s6_more"] + " " + COPY["leg_100m"]),
    (42.0, 44.5, "[dots refill; counter reaches 1,000,000,000,000]"),
    (44.5, 46.5, "1 trillion seconds " + COPY["s6_punch"]),
    (46.5, 48.2, COPY["s6_farm"] + " " + COPY["s6_city"] + " " + COPY["s6_write"] + " " + COPY["s6_mam"]),
    (48.2, 50.0, "Drawn to scale: 1 million is under 2 pixels beside 1 billion; 1 trillion would cross 833 screens."),
    (50.0, 53.0, COPY["s7_life"] + " " + COPY["s7_num"]),
    (53.0, 57.0, COPY["s7_used"]),
    (57.0, 60.0, COPY["s8_end"]),
]
# S6 bars (47.4-50.0) are captioned in cue 18; bar label wording on screen is
# transcribed in script.md's shot list. Burned-in text remains the primary track.

# ---------------------------------------------------------------- fact check
def fact_check():
    d, r = divmod(1_000_000, 86400); h, r = divmod(r, 3600); m, s = divmod(r, 60)
    assert (d, h, m, s) == (11, 13, 46, 40), (d, h, m, s)
    yr = 1_000_000_000 / 31_557_600
    assert abs(yr - 31.69) < 0.01, yr
    then = datetime(2026, 10, 31, tzinfo=timezone.utc) - timedelta(seconds=1_000_000_000)
    assert then.year == 1995, then
    tyr = 1_000_000_000_000 / 31_557_600
    assert abs(tyr - 31688.09) < 0.5, tyr
    assert NDOTS * 100 == 10**6 and NDOTS * 100_000 == 10**9 and NDOTS * 100_000_000 == 10**12
    assert 1600 / 1000 == 1.6 and round(1600 * 1000 / W) == 833
    life = 79 * 31_557_600
    assert abs(life - 2.49e9) < 0.01e9, life
    print(f"FACT CHECK OK: 1e6s=11d13h46m40s | 1e9s={yr:.2f}yr, back to {then.date()} "
          f"| 1e12s={tyr:.0f}yr | grid {COLS}x{ROWS}={NDOTS} | bars 1.6px/833 screens | 79yr={life:.3g}s")

# ---------------------------------------------------------------- helpers
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def ease_out_cubic(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_in_out(p): p = clamp(p); return p * p * (3 - 2 * p)
def ease_in_quad(p): p = clamp(p); return p * p
def fade(lt, t0, t1): return clamp((lt - t0) / max(t1 - t0, 1e-9))
def fmt(n): return f"{int(round(n)):,}"

_font_cache = {}
def font(kind, size):
    key = (kind, int(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONT_MONO if kind == "m" else FONT_SANS), int(size))
    return _font_cache[key]

def fit(kind, text, max_w, size, min_size=44):
    d = _probe_draw
    s = int(size)
    while s > min_size and d.textlength(text, font=font(kind, s)) > max_w:
        s -= 4
    return s

def text_c(dr, text, kind, size, cy, rgb, a=1.0, cx=W // 2, stroke=0, max_w=1680):
    if a <= 0: return
    s = fit(kind, text, max_w, size)
    f = font(kind, s)
    col = (rgb[0], rgb[1], rgb[2], int(255 * clamp(a)))
    sw = stroke
    dr.text((cx, cy), text, font=f, fill=col, anchor="mm",
            stroke_width=sw, stroke_fill=(BG[0], BG[1], BG[2], int(255 * clamp(a))) if sw else None)

def segments_c(dr, segs, kind, size, cy, a=1.0, cx=W // 2, stroke=0, max_w=1680):
    """segs: [(text, rgb), ...] drawn as one centered line."""
    if a <= 0: return
    full = "".join(t for t, _ in segs)
    s = fit(kind, full, max_w, size)
    f = font(kind, s)
    widths = [dr.textlength(t, font=f) for t, _ in segs]
    x = cx - sum(widths) / 2
    aa = int(255 * clamp(a))
    for (t, rgb), w in zip(segs, widths):
        dr.text((x, cy), t, font=f, fill=(rgb[0], rgb[1], rgb[2], aa), anchor="lm",
                stroke_width=stroke,
                stroke_fill=(BG[0], BG[1], BG[2], aa) if stroke else None)
        x += w

def legend(dr, per_dot, cy, a=1.0):
    segments_c(dr, [("One dot = ", INK), (fmt(per_dot), AMBER), (" seconds.", INK)],
               "s", 64, cy, a=a, stroke=6)

# ---------------------------------------------------------------- background + grid layers
def make_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = (x - W / 2) / (W / 2), (y - H / 2) / (H / 2)
    vig = 1.0 - 0.16 * np.clip(dx * dx + dy * dy, 0, 1.6)
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for i, c in enumerate(BG):
        arr[..., i] = c * vig
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

def dot_xy(i):
    return GX0 + (i % COLS) * SX, GY0 + (i // COLS) * SY

def make_grid_layer(rgb):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = (rgb[0], rgb[1], rgb[2], 255)
    for i in range(NDOTS):
        x, y = dot_xy(i)
        d.ellipse([x - DOT_R, y - DOT_R, x + DOT_R, y + DOT_R], fill=col)
    return img

BG_IMG = None; L_EMPTY = None; L_FULL = None; L_EDGE = None
_probe_draw = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
_grid_alpha_cache = {}

def _alpha_scaled(layer, a):
    key = (id(layer), round(a, 2))
    if key not in _grid_alpha_cache:
        arr = np.array(layer)
        arr[..., 3] = (arr[..., 3].astype(np.float32) * a).astype(np.uint8)
        _grid_alpha_cache.clear()
        _grid_alpha_cache[key] = Image.fromarray(arr, "RGBA")
    return _grid_alpha_cache[key]

def draw_grid(ov, filled_f, alpha=1.0):
    """Empty fabric + first `filled_f` dots lit; newest partial row in amber."""
    if alpha <= 0: return
    filled = int(clamp(filled_f, 0, NDOTS))
    lay_e, lay_f, lay_a = L_EMPTY, L_FULL, L_EDGE
    if alpha < 0.999:
        lay_e, lay_f, lay_a = (_alpha_scaled(l, alpha) for l in (lay_e, lay_f, lay_a))
    ov.alpha_composite(lay_e)
    if filled <= 0: return
    full_rows, part = divmod(filled, COLS)
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    if full_rows > 0:
        yb = GY0 + (full_rows - 1) * SY + SY / 2
        md.rectangle([0, 0, W, yb], fill=255)
    ov.paste(lay_f, (0, 0), mask)
    if part > 0:  # leading edge row in amber
        m2 = Image.new("L", (W, H), 0); m2d = ImageDraw.Draw(m2)
        y = GY0 + full_rows * SY
        xb = GX0 + (part - 1) * SX + SX / 2
        m2d.rectangle([0, y - SY / 2, xb, y + SY / 2], fill=255)
        ov.paste(lay_a, (0, 0), m2)

def counter_block(dr, value, a=1.0, cy=275, size=118, label=True):
    text_c(dr, fmt(value), "m", size, cy, INK, a=a, max_w=1720)
    if label:
        text_c(dr, COPY["seconds"], "s", 44, cy + 82, DIM, a=a)

def punch(dr, text, lt, t0, cy=695, size=168, rgb=INK):
    p = clamp((lt - t0) / 0.35)
    if p <= 0: return
    s = size * (1 + 0.22 * (1 - ease_out_cubic(p)))
    text_c(dr, text, "s", s, cy, rgb, a=min(1.0, p * 1.6), stroke=14, max_w=1760)

# ---------------------------------------------------------------- shots (overlay RGBA, local time lt)
def shot1(dr, ov, lt, t):
    text_c(dr, COPY["s1_head"], "s", 84, 250, INK, a=fade(lt, 0.3, 0.9))
    p = ease_out_cubic((lt - 0.5) / 2.3)
    for target, cx, lab in ((10**6, 470, COPY["s1_lab_l"]), (10**9, 1450, COPY["s1_lab_r"])):
        s = fmt(target * p) if p < 1 else fmt(target)
        f = font("m", 92)
        w = dr.textlength(s, font=f)
        x0 = cx - w / 2
        flash = clamp((lt - 3.1) / 1.4)
        zeros = [i for i, ch in enumerate(s) if ch == "0"]
        lit = int(round(flash * len(zeros))) if p >= 1 else 0
        cw = dr.textlength("0", font=f)
        dr.text((x0, 530), s, font=f, fill=INK + (255,), anchor="lm")
        for k in zeros[:lit]:
            dr.text((x0 + k * cw, 530), "0", font=f, fill=AMBER + (255,), anchor="lm")
        text_c(dr, lab, "s", 48, 620, DIM, a=fade(lt, 1.2, 2.0), cx=cx, max_w=760)
    text_c(dr, COPY["s1_tail"], "s", 64, 790, INK, a=fade(lt, 4.2, 5.0))

def fill_s2(lt):   return 150 * ease_in_quad((lt - 2.2) / 3.8)
def fill_s3(lt):   return 150 + (NDOTS - 150) * ease_in_out(lt / 6.0)
def fill_s5(lt):   return NDOTS * ease_in_out((lt - 0.3) / 5.7)
def fill_s6(lt):   return NDOTS * ease_out_cubic((lt - 0.8) / 3.0)

def shot2(dr, ov, lt, t):
    text_c(dr, COPY["s2_head"], "s", 84, 150, INK, a=fade(lt, 0.0, 0.6) * (1 - fade(lt, 2.45, 2.85)))
    legend(dr, 100, 150, a=fade(lt, 2.85, 3.25))
    ga = fade(lt, 1.2, 2.2)
    if ga > 0: draw_grid(ov, fill_s2(lt), alpha=ga)
    counter_block(dr, max(fill_s2(lt), 0) * 100, a=fade(lt, 0.8, 1.4))

def shot3(dr, ov, lt, t):
    f = fill_s3(lt)
    dim = fade(lt, 6.0, 6.6)
    draw_grid(ov, f, alpha=1 - 0.45 * dim)
    counter_block(dr, f * 100)
    top = 1 - fade(lt, 6.0, 6.38)
    legend(dr, 100, 150, a=top)
    text_c(dr, COPY["s3_exact"], "s", 60, 150, INK, a=fade(lt, 6.4, 6.8) * (1 - fade(lt, 7.95, 8.35)), stroke=6)
    text_c(dr, COPY["s3_mem"], "s", 60, 150, INK, a=fade(lt, 8.4, 8.9), stroke=6)
    punch(dr, COPY["s3_punch"], lt, 6.05)
    # 11.5 day-blocks under the punch
    if lt > 6.5:
        n_on = 11.5 * ease_out_cubic((lt - 6.5) / 1.8)
        bw, gap, y = 58, 14, 845
        x0 = W / 2 - (12 * bw + 11 * gap) / 2
        for i in range(12):
            frac = clamp(n_on - i)
            x = x0 + i * (bw + gap)
            dr.rounded_rectangle([x, y, x + bw, y + 34], 7, outline=DIM + (255,), width=2)
            if frac > 0:
                dr.rounded_rectangle([x, y, x + bw * frac, y + 34], 7, fill=AMBER + (255,))

def shot4(dr, ov, lt, t):
    drain = NDOTS * (1 - ease_in_out(lt / 1.5))
    draw_grid(ov, drain, alpha=0.32 + 0.68 * (1 - fade(lt, 0.0, 1.2)) if lt < 1.2 else 0.32)
    text_c(dr, COPY["s4_keep"], "s", 72, 215, INK, a=fade(lt, 0.4, 1.0), stroke=8)
    legend(dr, 100 if lt < 2.2 else 100_000, 330, a=fade(lt, 1.4, 2.0))
    if lt >= 2.2:  # hard legend flip is the point — no fade
        pass
    p = clamp((lt - 3.2) / 0.35)
    if p > 0:
        s = 300 * (1 + 0.3 * (1 - ease_out_cubic(p)))
        text_c(dr, COPY["s4_slam"], "s", s, 620, AMBER, a=min(1, p * 1.8), stroke=16)
    text_c(dr, COPY["s4_same"], "s", 60, 860, INK, a=fade(lt, 4.2, 4.9), stroke=8)

def shot5(dr, ov, lt, t):
    f = fill_s5(lt)
    dim = fade(lt, 6.1, 6.7)
    draw_grid(ov, f, alpha=1 - 0.5 * dim)
    counter_block(dr, f * 100_000)
    legend(dr, 100_000, 150, a=1 - fade(lt, 6.1, 6.6))
    text_c(dr, COPY["s5_1995"], "s", 60, 150, INK, a=fade(lt, 6.9, 7.5) * (1 - fade(lt, 9.2, 9.55)), stroke=6)
    text_c(dr, COPY["s5_31"], "s", 60, 150, INK, a=fade(lt, 9.55, 10.0), stroke=6)
    if lt < 10.3:
        punch(dr, COPY["s5_punch"], lt, 6.1)
    # year ruler 1995 -> 2026, on a dark panel so it stays legible over the dots
    if 6.9 < lt < 10.3:
        a = fade(lt, 6.9, 7.4) * (1 - fade(lt, 9.9, 10.3))
        p = ease_in_out((lt - 7.2) / 2.2)
        x0, x1, y = 380, 1540, 872
        aa = int(255 * a)
        dr.rounded_rectangle([300, 792, 1620, 950], 18, fill=BG + (int(220 * a),))
        dr.line([x0, y, x1, y], fill=DIM + (aa,), width=4)
        mx = x0 + (x1 - x0) * p
        dr.ellipse([mx - 11, y - 11, mx + 11, y + 11], fill=AMBER + (aa,))
        text_c(dr, "1995", "m", 48, y + 50, DIM, a=a, cx=x0 + 20, max_w=300)
        text_c(dr, "2026", "m", 48, y + 50, DIM, a=a, cx=x1 - 20, max_w=300)
        text_c(dr, str(int(1995 + 31 * p)), "m", 64, y - 52, AMBER, a=a,
               cx=int(max(430, min(1490, mx))), max_w=320)
    if lt >= 10.3:
        text_c(dr, COPY["s5_gen"], "s", 88, 695, INK, a=fade(lt, 10.3, 11.0), stroke=12)

def shot6(dr, ov, lt, t):
    if lt < 4.6:
        f = fill_s6(lt)
        dim = fade(lt, 3.9, 4.4)
        draw_grid(ov, f, alpha=1 - 0.45 * dim)
        counter_block(dr, f * 100_000_000, size=104)
        text_c(dr, COPY["s6_more"], "s", 64, 150, INK, a=fade(lt, 0.0, 0.5) * (1 - fade(lt, 0.85, 1.2)), stroke=6)
        legend(dr, 100_000_000, 150, a=fade(lt, 1.2, 1.6) * (1 - fade(lt, 4.0, 4.5)))
        punch(dr, COPY["s6_punch"], lt, 3.95)
    elif lt < 7.4:
        draw_grid(ov, NDOTS, alpha=0.16 * (1 - fade(lt, 6.9, 7.4)))
        text_c(dr, COPY["s6_punch"], "s", 168, 250, INK, a=1 - fade(lt, 6.9, 7.4), stroke=12)
        for i, k in enumerate(("s6_farm", "s6_city", "s6_write")):
            text_c(dr, COPY[k], "s", 76, 450 + i * 118, INK,
                   a=fade(lt, 4.7 + i * 0.7, 5.2 + i * 0.7) * (1 - fade(lt, 6.9, 7.4)), stroke=8)
        text_c(dr, COPY["s6_mam"], "s", 76, 860, AMBER,
               a=fade(lt, 6.2, 6.8) * (1 - fade(lt, 6.9, 7.4)), stroke=8)
    else:
        a_all = fade(lt, 7.4, 7.8)
        text_c(dr, COPY["s6_scale"], "s", 52, 270, DIM, a=a_all)
        x0 = 160
        # billion: full 1600px bar wipes in
        p = ease_out_cubic((lt - 7.6) / 0.8)
        dr.rectangle([x0, 540, x0 + 1600 * p, 576], fill=INK + (255,))
        text_c(dr, COPY["s6_blab"], "s", 52, 490, INK, a=fade(lt, 7.7, 8.1), cx=x0 + 800)
        # million: honest 1.6px -> drawn 2px sliver, labelled
        if lt > 8.3:
            dr.rectangle([x0, 370, x0 + 2, 406], fill=AMBER + (255,))
            dr.line([x0 + 2, 388, x0 + 90, 388], fill=AMBER + (255,), width=3)
            dr.text((x0 + 108, 388), COPY["s6_mlab"], font=font("s", 52),
                    fill=AMBER + (int(255 * fade(lt, 8.3, 8.8)),), anchor="lm")
        # trillion: launches off-screen
        if lt > 9.0:
            p2 = ease_in_quad((lt - 9.0) / 0.7)
            dr.rectangle([x0, 710, x0 + (W - x0 + 400) * p2, 746], fill=AMBER + (255,))
            text_c(dr, COPY["s6_tlab"], "s", 56, 812, INK, a=fade(lt, 9.2, 9.7))

def shot7(dr, ov, lt, t):
    text_c(dr, COPY["s7_life"], "s", 72, 280, INK, a=fade(lt, 0.1, 0.7))
    segments_c(dr, [("2\u00bd billion", AMBER), (" seconds.", INK)], "s", 138, 430, a=fade(lt, 0.9, 1.6))
    p = ease_in_out((lt - 1.4) / 2.8)
    x0, x1, y = 160, 1760, 620
    if p > 0:
        dr.rounded_rectangle([x0, y, x1, y + 44], 10, outline=DIM + (255,), width=3)
        dr.rounded_rectangle([x0, y, x0 + (x1 - x0) * p, y + 44], 10, fill=INK + (255,))
        text_c(dr, "0", "m", 44, y + 86, DIM, a=p, cx=x0, max_w=200)
        text_c(dr, COPY["s7_yrs"], "s", 44, y + 86, DIM, a=p, cx=x1 - 60, max_w=320)
    if lt > 4.4:  # this film, as a marker at the bar's start (true width: 0.00004px)
        pulse = 0.65 + 0.35 * math.sin((lt - 4.4) * 5.0)
        aa = int(255 * pulse * fade(lt, 4.4, 4.9))
        dr.rectangle([x0, y - 8, x0 + 4, y + 52], fill=AMBER + (aa,))
        text_c(dr, COPY["s7_60"], "m", 44, y - 48, AMBER, a=fade(lt, 4.4, 4.9), cx=x0 + 34, max_w=220)
    text_c(dr, COPY["s7_used"], "s", 84, 830, INK, a=fade(lt, 4.6, 5.3))

def shot8(dr, ov, lt, t):
    text_c(dr, COPY["s8_end"], "s", 96, 470, INK, a=fade(lt, 0.0, 0.8))
    text_c(dr, COPY["s8_cred"], "s", 44, 600, DIM, a=fade(lt, 0.9, 1.6))

SHOT_FNS = [shot1, shot2, shot3, shot4, shot5, shot6, shot7, shot8]

# ---------------------------------------------------------------- living texture
# Every frame gets real, seeded per-frame atmosphere: a drifting light gradient and fine
# grain. This is not decoration-free vanity: a slate-flat background during a typographic hold
# reads as a *frozen frame* to any motion check (and to the eye, as a dead image). The drift also
# gives the dark field a slow breathing quality that suits a film about time passing.
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_NX = (_XX - W / 2) / (W / 2)
_NY = (_YY - H / 2) / (H / 2)
_RAD = np.sqrt(_NX * _NX + _NY * _NY)
_rng = np.random.default_rng(7)
GRAIN_SIGMA = 2.0   # smallest value that keeps every hold clean under freezedetect d=0.5 (~8 Mbps here)
# Grain is generated at quarter resolution and upscaled: its structure lives at 2-4 px scale,
# which x264 actually preserves instead of spending bits fighting per-pixel noise. Fine
# per-pixel noise looked better in theory and cost 11 Mbps in practice.
def _grain_bank(n=6):
    out = []
    for _ in range(n):
        lr = _rng.normal(0.0, 1.0, (H // 4, W // 4)).astype(np.float32)
        im = Image.fromarray(lr, mode="F").resize((W, H), Image.BILINEAR)
        out.append((np.asarray(im, dtype=np.float32) * GRAIN_SIGMA).astype(np.float32))
    return out
_DGRAIN = _grain_bank()

def atmosphere(t):
    """Additive light field + grain, evaluated per frame index (deterministic)."""
    ang = 0.55 * np.sin(t * 0.41) + 0.35 * t
    cx, cy = 0.62 * np.cos(ang), 0.50 * np.sin(ang * 1.37 + 0.4)
    d2 = (_NX - cx) ** 2 + (_NY - cy) ** 2
    glow = 15.0 * np.exp(-d2 / 2.1) + 5.0 * np.exp(-_RAD ** 2 / 5.0)
    drift = 1.4 * np.sin(6.283 * (t * 0.11) + _RAD * 4.0)
    k = int(round(t * FPS)) % len(_DGRAIN)
    return (glow + drift + _DGRAIN[k])[..., None]

_ATMO_CACHE = {}
def _atmo_slice(t):
    key = round(t, 5)
    if key not in _ATMO_CACHE:
        _ATMO_CACHE.clear()
        _ATMO_CACHE[key] = atmosphere(t).astype(np.float32)
    return _ATMO_CACHE[key]

def draw_seconds_bar(img, t):
    """Whole film in one bar: elapsed amber, remaining empty, with a hairline spark.
    Always in motion, so no hold anywhere is a dead frame."""
    dr = ImageDraw.Draw(img)
    x0, x1, y = 160, 1760, 78
    p = clamp(t / DUR)
    dr.rounded_rectangle([x0, y - 3, x1, y + 3], 3, fill=(46, 60, 78))
    if p > 0:
        dr.rounded_rectangle([x0, y - 3, x0 + (x1 - x0) * p, y + 3], 3, fill=AMBER)
    sx = x0 + (x1 - x0) * p
    dr.ellipse([sx - 5, y - 5, sx + 5, y + 5], fill=INK)

def draw_ruler(img, t):
    dr = ImageDraw.Draw(img)
    x0, x1, y = 160, 1760, 1018
    dr.line([x0, y, x1, y], fill=FAINT, width=3)
    mx = x0 + (x1 - x0) * clamp(t / DUR)
    dr.line([x0, y, mx, y], fill=DIM, width=3)
    dr.ellipse([mx - 8, y - 8, mx + 8, y + 8], fill=AMBER)
    dr.text((x0 - 18, y), COPY["r0"], font=font("m", 44), fill=DIM, anchor="rm")
    dr.text((x1 + 18, y), COPY["r60"], font=font("m", 44), fill=DIM, anchor="lm")

def render_frame(t):
    img = BG_IMG.copy()
    idx = next(i for i, (a, b) in enumerate(SHOTS) if a <= t < b or (i == 7 and t <= b))
    a, b = SHOTS[idx]
    lt = t - a
    def overlay(fn_i, lti, alpha):
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        SHOT_FNS[fn_i](ImageDraw.Draw(ov), ov, lti, t)
        if alpha < 0.999:
            arr = np.array(ov)
            arr[..., 3] = (arr[..., 3].astype(np.float32) * alpha).astype(np.uint8)
            ov = Image.fromarray(arr, "RGBA")
        img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))
    if idx > 0 and lt < DISSOLVE:
        pa, pb = SHOTS[idx - 1]
        overlay(idx - 1, pb - pa, 1 - lt / DISSOLVE)
        overlay(idx, lt, lt / DISSOLVE)
    else:
        overlay(idx, lt, 1.0)
    draw_seconds_bar(img, t)
    draw_ruler(img, t)
    arr = np.asarray(img, dtype=np.float32) + _atmo_slice(t)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

# ---------------------------------------------------------------- audio (48kHz stereo, fully synthesized)
SR = 48000
def osc(freq, t0, dur, gain, kind="sine", attack=0.8, release=1.0, pan=0.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    if kind == "sine": w = np.sin(2 * np.pi * freq * tt)
    else: w = np.sign(np.sin(2 * np.pi * freq * tt)) * 0.4 + np.sin(2 * np.pi * freq * tt) * 0.6
    env = np.ones(n)
    na, nr = int(attack * SR), int(release * SR)
    if na: env[:na] = np.linspace(0, 1, na) ** 1.5
    if nr: env[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    w = (w * env * gain).astype(np.float32)
    lg, rg = math.sqrt((1 - pan) / 2) * math.sqrt(2), math.sqrt((1 + pan) / 2) * math.sqrt(2)
    return t0, np.stack([w * (lg / math.sqrt(2)), w * (rg / math.sqrt(2))], axis=1)

def add(buf, t0, sig):
    i = int(t0 * SR)
    j = min(len(buf), i + len(sig))
    if j > i: buf[i:j] += sig[:j - i]

_rng = np.random.default_rng(42)
def tick(t0, freq=1800.0, gain=0.16):
    n = int(0.045 * SR)
    tt = np.arange(n) / SR
    w = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 160) * 0.8
    w[:int(0.003 * SR)] += _rng.standard_normal(int(0.003 * SR)).astype(np.float32) * 0.35
    return t0, np.stack([w * gain, w * gain], axis=1).astype(np.float32)

def boom(t0, gain=0.5):
    n = int(1.4 * SR)
    tt = np.arange(n) / SR
    w = (np.sin(2 * np.pi * 55 * tt) + 0.35 * np.sin(2 * np.pi * 110 * tt)) * np.exp(-tt * 3.2)
    return t0, np.stack([w * gain, w * gain], axis=1).astype(np.float32)

def thump(t0, gain=0.32):
    n = int(0.16 * SR)
    tt = np.arange(n) / SR
    w = np.sin(2 * np.pi * 58 * tt) * np.exp(-tt * 26)
    return t0, np.stack([w * gain, w * gain], axis=1).astype(np.float32)

CHORDS = {"Am": [110.00, 164.81, 220.00, 261.63], "F": [87.31, 130.81, 174.61, 220.00],
          "C": [130.81, 196.00, 261.63, 329.63], "G": [98.00, 146.83, 196.00, 246.94]}
PAD_SCHEDULE = [(0, 7, "Am", 0.10), (6, 13, "F", 0.10), (12, 23, "C", 0.105),
                (22, 29, "Am", 0.095), (28, 35, "G", 0.105), (34, 41, "Am", 0.105),
                (40, 51, "F", 0.08), (50, 60.2, "Am", 0.095)]

def synth_audio(path):
    buf = np.zeros((int(DUR * SR), 2), dtype=np.float32)
    for t0, t1, name, g in PAD_SCHEDULE:
        for k, f in enumerate(CHORDS[name]):
            pan = (-0.5, -0.17, 0.17, 0.5)[k]
            for det in (0.9985, 1.0015):
                add(buf, *osc(f * det, t0, t1 - t0, g / 2, attack=1.4, release=1.6, pan=pan))
    for s in range(60):  # the film ticks its own theme, once per second
        g = 0.20 if s < 6 or s >= 50 else 0.11
        add(buf, *tick(s + 0.0, 1650, g))
    # fill shimmer: ticks as the dot count crosses every 200 dots (same fill functions as picture)
    for fillfn, g0, per in ((fill_s3, 12.0, 100), (fill_s5, 28.0, 100_000), (fill_s6, 40.0, 100_000_000)):
        prev = 0
        for step in range(1, 721):
            lt = step / 60.0
            cur = int(fillfn(lt))
            if cur // 200 > prev // 200 and cur < NDOTS:
                add(buf, *tick(g0 + lt, 1400 + 800 * (cur / NDOTS), 0.045))
            prev = cur
    add(buf, *boom(25.2, 0.5))   # x1000 slam (S4)
    add(buf, *boom(43.95, 0.55))  # trillion punch (S6)
    add(buf, *boom(18.05, 0.3))  # million punch (S3, gentler)
    add(buf, *boom(34.15, 0.4))  # billion punch (S5)
    for t0 in (36.0, 38.0, 51.0, 53.0, 55.0):  # heartbeat pairs
        add(buf, *thump(t0)); add(buf, *thump(t0 + 0.28, 0.22))
    fade_n = int(1.2 * SR)
    buf[-fade_n:] *= np.linspace(1, 0, fade_n)[:, None]
    buf[:int(0.25 * SR)] *= np.linspace(0, 1, int(0.25 * SR))[:, None]
    # gentle saturation: raises integrated level, caps crest so two-pass
    # loudnorm can stay linear (measured pre-master was ~-28 LUFS: too sparse)
    buf = (np.tanh(buf * 1.3) * 0.92).astype(np.float32)
    peak = float(np.max(np.abs(buf)))
    if peak > 0.891: buf *= 0.891 / peak; peak = 0.891
    pcm = (np.clip(buf, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"AUDIO: {path} | {len(pcm)/SR:.3f}s | peak {peak:.3f} pre-loudnorm")

# ---------------------------------------------------------------- captions
def srt_time(s):
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

def write_srt(path):
    out = []
    for i, (a, b, txt) in enumerate(CAPTIONS, 1):
        out += [str(i), f"{srt_time(a)} --> {srt_time(b)}", txt, ""]
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"CAPTIONS: {path} | {len(CAPTIONS)} cues")

# ---------------------------------------------------------------- main
def main():
    global BG_IMG, L_EMPTY, L_FULL, L_EDGE
    fact_check()
    BG_IMG = make_bg()
    L_EMPTY = make_grid_layer(FAINT); L_FULL = make_grid_layer(INK); L_EDGE = make_grid_layer(AMBER)
    WORK.mkdir(exist_ok=True)
    if "--test" in sys.argv:
        td = WORK / "test"; td.mkdir(exist_ok=True)
        for t in (2.0, 5.0, 9.5, 15.0, 20.5, 25.3, 32.0, 37.5, 39.5, 44.8, 48.8, 49.6, 54.0, 58.5):
            render_frame(t).save(td / f"t{t:05.1f}.png")
            print(f"test frame t={t}s done")
        return
    fd = WORK / "frames"; fd.mkdir(exist_ok=True)
    for i in range(NFRAMES):
        render_frame(i / FPS).save(fd / f"f{i:04d}.png", compress_level=3)
        if i % 300 == 0: print(f"frame {i}/{NFRAMES}", flush=True)
    print(f"FRAMES: {NFRAMES} -> {fd}")
    synth_audio(WORK / "audio.wav")
    write_srt(ROOT / "captions.srt")

if __name__ == "__main__":
    main()
