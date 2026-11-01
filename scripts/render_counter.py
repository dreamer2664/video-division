#!/usr/bin/env python3
"""Counter / beat renderer for the presenter-led explainer register.

Reads a cue sheet JSON and renders a video sequence in which:
  - the counter ticks at every frame (value read straight from the cue sheet),
  - captions are burned in, locked to voice word boundaries,
  - a STATUS block shows the live step.

This is the proof renderer. vox's animation engine consumes the same cue
sheet for the final film. Pipeline: voice first (audio + word timestamps
already generated), captions locked to those boundaries, then render.

Usage:
  python3 scripts/render_counter.py [cue_sheet.json] [start_s] [end_s] [out.mp4]
  Defaults render the 15 s proof (0 -> 15 s) from cue_sheets/sleep_premise/cue_sheet.json
  to output/15s_counter.mp4
"""

import json, os, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont

FPS = 30
W, H = 1080, 1920  # 1080 x 1920 portrait

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def load_font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def draw_gradient(draw, x0, y0, x1, y1, c_top, c_bot, vertical=True):
    """Vertical sunset-ish gradient background (reference set: sunset sky + warm floor)."""
    steps = (y1 - y0) if vertical else (x1 - x0)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        c = tuple(int(a + (b - a) * t) for a, b in zip(c_top, c_bot))
        if vertical:
            draw.line([(x0, y0 + i), (x1, y0 + i)], fill=c)
        else:
            draw.line([(x0 + i, y0), (x0 + i, y1)], fill=c)

def draw_text(draw, xy, text, font, fill, anchor="mm", stroke_w=0, stroke_fill=None):
    draw.text(xy, text, font=font, fill=fill, anchor=anchor,
              stroke_width=stroke_w, stroke_fill=stroke_fill)

def caption_text_wrap(draw, text, font, max_w):
    """Return text (single line) if it fits, else a shortened version with ellipsis."""
    if draw.textlength(text, font=font) <= max_w:
        return text
    # shrink by removing words from the end
    words = text.split()
    while words and draw.textlength(" ".join(words) + "...", font=font) > max_w:
        words.pop()
    return " ".join(words) + "..." if words else text

def render_frame(f, cue, words_by_time, out_path):
    """Render a single frame f (0-indexed) from the cue sheet."""
    t = f / FPS
    counter_hours = cue["counter_per_frame"][f]
    counter_int = int(math.floor(counter_hours))

    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    unit = cue["meta"]["unit"]

    # --- background: sunset sky gradient down to warm floor ---
    draw_gradient(d, 0, 0, W, int(H * 0.55), (26, 18, 46), (90, 40, 60))   # deep sky
    draw_gradient(d, 0, int(H * 0.55), W, H, (60, 30, 20), (150, 90, 40))  # warm floor

    # --- rail / tube lattice behind (abstract, low detail) ---
    for x in range(0, W, 120):
        d.line([(x, int(H * 0.5)), (x + 60, int(H * 0.62))], fill=(120, 70, 50), width=6)
    for y in range(int(H * 0.5), H, 160):
        d.line([(int(W * 0.35), y), (int(W * 0.65), y + 40)], fill=(100, 55, 40), width=4)

    # --- STATUS block (corner tag, live step) ---
    status = f"STEP · COUNTER {counter_int} h · {t:.1f}s"
    sw = load_font(26, bold=True)
    tw = d.textlength(status, font=sw)
    d.rounded_rectangle([20, 20, tw + 44, 70], radius=10, fill=(0, 0, 0, 0))
    # PIL rounded_rectangle fill doesn't take alpha well; use opaque dark panel
    d.rounded_rectangle([20, 20, int(tw + 44), 70], radius=10, fill=(20, 14, 30))
    draw_text(d, (40, 45), status, sw, (255, 255, 255), anchor="lm")

    # --- presenter placeholder (stylised, chest-up, lower-middle) ---
    px, py = W // 2, int(H * 0.78)
    d.ellipse([px - 70, py - 130, px + 70, py + 10], fill=(240, 210, 180))  # head
    d.ellipse([px - 44, py - 104, px - 20, py - 80], fill=(40, 30, 30))     # left eye
    d.ellipse([px + 20, py - 104, px + 44, py - 80], fill=(40, 30, 30))     # right eye
    d.arc([px - 30, py - 80, px + 30, py - 40], start=200, end=340, width=5, fill=(180, 60, 40))  # brow/mouth
    d.rectangle([px - 110, py + 10, px + 110, py + 100], fill=(40, 100, 70))  # teal sweater
    d.rectangle([px - 75, py + 55, px + 75, py + 95], fill=(255, 255, 255))  # gesturing hands hint

    # --- sidekick: spiky red blob on red pole (right of presenter) ---
    sx = int(W * 0.82)
    d.line([(sx, int(H * 0.55)), (sx, int(H * 0.78))], fill=(200, 40, 40), width=10)
    # blob body
    d.ellipse([sx - 40, int(H * 0.70), sx + 40, int(H * 0.80)], fill=(220, 30, 30))
    d.ellipse([sx - 16, int(H * 0.715), sx - 2, int(H * 0.735)], fill=(40, 30, 30))  # eye
    d.ellipse([sx + 2, int(H * 0.715), sx + 16, int(H * 0.735)], fill=(40, 30, 30))  # eye
    # spikes
    for ang in range(0, 360, 45):
        import math as _m
        r = 48
        x2 = sx + _m.cos(_m.radians(ang)) * r
        y2 = int(H * 0.75) + _m.sin(_m.radians(ang)) * r * 0.5
        d.line([(sx, int(H * 0.75)), (x2, y2)], fill=(160, 20, 20), width=6)

    # --- counter (big, centre) ---
    cf = load_font(210, bold=True)
    draw_text(d, (W // 2, int(H * 0.42)), f"{counter_int}", cf, (255, 255, 255), anchor="mm",
              stroke_w=6, stroke_fill=(0, 0, 0))
    uf = load_font(34, bold=True)
    draw_text(d, (W // 2, int(H * 0.50)), unit, uf, (230, 200, 160), anchor="mm")

    # --- caption (locked to word boundaries), white heavy sans, dark outline ---
    caption = caption_for(t, cue, words_by_time)
    if caption:
        capf = load_font(56, bold=True)
        wrapped = caption_text_wrap(d, caption, capf, W - 120)
        draw_text(d, (W // 2, int(H * 0.60)), wrapped, capf, (255, 255, 255), anchor="mm",
                  stroke_w=8, stroke_fill=(0, 0, 0))

    img.save(out_path)

def caption_for(t, cue, words_by_time):
    """Return the caption text live at time t, locked to word boundaries."""
    for cap in cue["captions"]:
        wb = cap.get("word_boundaries")
        if wb:
            start_s, end_s = wb["start"], wb["end"]
        else:
            start_s, end_s = cap["start_s"], cap["end_s"]
        if start_s <= t < end_s:
            return cap["text"]
    return None

def main():
    cue_path = sys.argv[1] if len(sys.argv) > 1 else "/home/user/video-division/cue_sheets/sleep_premise/cue_sheet.json"
    start_s = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    end_s = float(sys.argv[3]) if len(sys.argv) > 3 else 15.0
    out = sys.argv[4] if len(sys.argv) > 4 else "/home/user/video-division/output/15s_counter.mp4"

    with open(cue_path) as f:
        cue = json.load(f)

    # Word boundaries locked from the ElevenLabs synthesis (voice first).
    words_path = "/home/user/video-division/audio/15s_proof/word_timestamps.json"
    words_by_time = None
    wb_applied = False
    if os.path.exists(words_path):
        with open(words_path) as f:
            wdata = json.load(f)
        words = wdata["words"]
        # Map the two proof captions to word-boundary spans.
        # Caption 0: words 0..5  ("What if I never slept?")
        # Caption 1: words 6..10 ("I stayed awake for you")
        spans = [(0, 5), (6, 10)]
        for i, (a, b) in enumerate(spans):
            if i < len(cue["captions"]):
                cue["captions"][i]["word_boundaries"] = {
                    "start": words[a]["start"],
                    "end": words[b]["end"],
                    "words": [w["word"] for w in words[a:b + 1]],
                }
                wb_applied = True
        print(f"[cue] word boundaries locked for {len(spans)} caption beat(s)")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    frame_dir = "/tmp/frames_15s"
    os.makedirs(frame_dir, exist_ok=True)

    start_frame = int(round(start_s * FPS))
    end_frame = int(round(end_s * FPS))  # exclusive
    print(f"[render] frames {start_frame}..{end_frame}  ({start_s}s -> {end_s}s)")
    for f in range(start_frame, end_frame):
        render_frame(f, cue, words_by_time, f"{frame_dir}/{f:05d}.png")
    print(f"[render] wrote {end_frame - start_frame} frames to {frame_dir}")

    # Audio: pad the 8.13s voice to the full sequence length with silence.
    audio_in = "/home/user/video-division/audio/15s_proof/voice.mp3"
    duration = end_s - start_s
    # Build a silent pad then concat: use ffmpeg apad + concat is complex; instead
    # use a single command that pads audio to `duration` via the apad filter.
    os.makedirs(os.path.dirname(out), exist_ok=True)
    vf_cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(FPS),
        "-i", f"{frame_dir}/%05d.png",
        "-i", audio_in,
        "-filter_complex", f"[1:a]apad=pad_dur={duration}[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "128k",
        "-movflags", "+faststart",
        "-t", str(duration),
        out,
    ]
    subprocess.run(vf_cmd, check=True)
    print(f"[render] wrote {out}")

if __name__ == "__main__":
    main()
