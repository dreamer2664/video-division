#!/usr/bin/env python3
"""
House Look Lower-Third Caption Renderer & WordBoundary Grouper (`look/house_captions.py`).

Enforces DIRECTIVE-2026-11-01-house-look.md §3:
  - Strictly 2-5 words per caption beat, locked directly to actual edge-tts WordBoundary timestamps.
  - Bold condensed/display sans >= 50 px at 1080p, lower-third pill.
  - Palette: House Amber `#F5D14E`, crisp White `#F4F5F8`, Threat Crimson `#EA443C` (plus optional
    Cyan `#62D4FF` / Seafoam `#5CE8B8` stereo-azimuth indicators for 2-voice or 3-voice dialogue).
"""

import math
import os
from typing import Iterable, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = 1920
H = 1080

PALETTE = {
    "white": (244, 245, 248),
    "amber": (245, 209, 78),    # #F5D14E — House directive signature amber
    "crimson": (234, 68, 60),   # #EA443C — Threat / twist emphasis
    "cyan": (98, 212, 255),     # #62D4FF — Secondary bandpassed line voice
    "seafoam": (92, 232, 184),  # #5CE8B8 — Tertiary VHF/radio horn voice
}


def find_house_font(bold: bool = True) -> str:
    candidates = (
        [
            "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
            "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    )
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("Install fonts-inter or fonts-liberation2 in the sandbox.")


def group_words_into_cues_2_to_5(words: list[dict], max_words: int = 4) -> list[dict]:
    """
    Deterministically partition a turn's WordBoundary list `[{'text':..., 'start':..., 'end':...}]`
    into 2-to-5-word beats (never leaving a 1-word orphan if `len(words) >= 2`).
    """
    max_words = max(2, min(5, max_words))
    n = len(words)
    if n == 0:
        return []
    if n <= 5:
        return [{"start": words[0]["start"], "end": words[-1]["end"], "text": " ".join(w["text"] for w in words)}]

    chunks = []
    idx = 0
    while idx < n:
        rem = n - idx
        if rem <= 5:
            take = rem
        elif rem == 6:
            take = 3
        elif rem == 7:
            take = 4
        else:
            take = max_words
            # Break naturally on punctuation if inside 2..5 window
            for k in range(2, min(5, rem - 2) + 1):
                if words[idx + k - 1]["text"].endswith((",", ".", "?", "!", ";", ":")):
                    take = k
                    break
        grp = words[idx : idx + take]
        chunks.append({
            "start": grp[0]["start"],
            "end": grp[-1]["end"],
            "text": " ".join(w["text"] for w in grp),
        })
        idx += take
    return chunks


def render_house_caption_patch(
    text: str,
    amber_words: Iterable[str] = (),
    crimson_words: Iterable[str] = (),
    speaker_tag: Optional[str] = None,
    accent: str = "amber",
    pan_px: int = 0,
    font_px: int = 52,
) -> tuple[int, int, np.ndarray]:
    """
    Render a high-contrast 1080p lower-third caption card.
    Returns `(x0, y0, rgba_float32_01)` ready to alpha-composite onto an `[H, W, 3]` frame.
    """
    amber_set = {w.upper().strip(".,?!;:") for w in amber_words}
    crimson_set = {w.upper().strip(".,?!;:") for w in crimson_words}

    font_main = ImageFont.truetype(find_house_font(bold=True), font_px)
    font_tag = ImageFont.truetype(find_house_font(bold=False), 21)

    tokens = []
    for w in text.split():
        key = w.upper().strip(".,?!;:")
        if key in crimson_set:
            tokens.append((w, PALETTE["crimson"]))
        elif key in amber_set:
            tokens.append((w, PALETTE["amber"]))
        else:
            tokens.append((w, PALETTE["white"]))

    dummy = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    space_w = dummy.textlength(" ", font=font_main)
    widths = [dummy.textlength(t, font=font_main) for t, _ in tokens]
    text_w = sum(widths) + space_w * max(0, len(tokens) - 1)

    tag_w = (dummy.textlength(f"{speaker_tag} · ", font=font_tag) + 8) if speaker_tag else 0
    pad_x = 32
    box_w = int(math.ceil(tag_w + text_w + pad_x * 2))
    box_h = 92

    patch = Image.new("RGBA", (box_w + 24, box_h + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)

    acc_rgb = PALETTE.get(accent, PALETTE["amber"])
    d.rounded_rectangle([12, 12, 12 + box_w, 12 + box_h], radius=15, fill=(6, 9, 15, 208), outline=(*acc_rgb, 68), width=1)

    if pan_px < 0:
        d.rounded_rectangle([12, 24, 17, 12 + box_h - 12], radius=2, fill=(*acc_rgb, 240))
    elif pan_px > 0:
        d.rounded_rectangle([12 + box_w - 5, 24, 12 + box_w, 12 + box_h - 12], radius=2, fill=(*acc_rgb, 240))
    else:
        d.rounded_rectangle([12 + box_w // 2 - 48, 12, 12 + box_w // 2 + 48, 16], radius=2, fill=(*acc_rgb, 240))

    cur_x = 12 + pad_x
    if speaker_tag:
        d.text((cur_x, 45), f"{speaker_tag} ·", font=font_tag, fill=(*acc_rgb, 238), stroke_width=2, stroke_fill=(3, 6, 12, 230))
        cur_x += tag_w

    text_y = 25
    for (tok, col), w_px in zip(tokens, widths):
        d.text((cur_x, text_y + 3), tok, font=font_main, fill=(0, 0, 0, 225), stroke_width=5, stroke_fill=(3, 5, 10, 225))
        d.text((cur_x, text_y), tok, font=font_main, fill=(*col, 255), stroke_width=3, stroke_fill=(4, 7, 13, 245))
        cur_x += w_px + space_w

    arr = np.array(patch, dtype=np.float32) / 255.0
    x0 = max(28, min(W - arr.shape[1] - 28, (W - arr.shape[1]) // 2 + pan_px))
    y0 = 910
    return x0, y0, arr


def format_srt_ts(sec: float) -> str:
    ms = int(round(sec * 1000.0))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: list[dict], out_srt_path: str) -> None:
    blocks = []
    for i, c in enumerate(cues, start=1):
        prefix = f"[{c['speaker']}] " if "speaker" in c else ""
        blocks.append(f"{i}\n{format_srt_ts(c['start'])} --> {format_srt_ts(c['end'])}\n{prefix}{c['text']}\n")
    with open(out_srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
