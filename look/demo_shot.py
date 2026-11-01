#!/usr/bin/env python3
"""
Self-contained 6.000s House Look Smoke-Test Shot (`look/demo_shot.py`).

Takes any 1920x1080 night plate (or synthesizes a wet-stone lantern test plate if `--plate` is omitted),
grades it through `house_obsidian_500t.cube` + 500T red-amber halation, adds parallax rain + drifting
mist + sub-pixel push-in, synthesizes one line with the House Voice (`en-US-ChristopherNeural`), locks
2-5 word captions to `WordBoundary`, writes lossless `.flac` stems, and muxes a `-16 LUFS` 1080p30 MP4.

Usage:
    python3 look/demo_shot.py --out-dir /tmp/house_demo
    python3 look/demo_shot.py --plate my_plate.jpg --out-dir /tmp/house_demo
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import numpy as np
from PIL import Image
from scipy.io import wavfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from look.generate_luts import generate_all_luts
from look.house_motion import load_cube_lut, render_moving_shot_clip
from look.house_captions import group_words_into_cues_2_to_5, render_house_caption_patch, write_srt
from look.house_audio import SR, synthesize_lines_with_telemetry, build_rain_and_sub_bed, duck_and_master_stems_flac


def make_synthetic_test_plate() -> np.ndarray:
    """Fallback photographic-lighting test target (6500K storm window + 2600K practical lantern) if no plate is passed."""
    w, h = 1920, 1080
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rng = np.random.default_rng(42)
    tex = rng.normal(0.0, 0.018, (h, w)).astype(np.float32)

    win = np.exp(-(((xx - 960.0) / 360.0) ** 2 + ((yy - 340.0) / 180.0) ** 2))
    lamp = np.exp(-(((xx - 680.0) / 130.0) ** 2 + ((yy - 680.0) / 110.0) ** 2))
    core = np.exp(-(((xx - 680.0) / 26.0) ** 2 + ((yy - 675.0) / 34.0) ** 2))
    floor_ref = np.exp(-(((xx - 680.0) / 180.0) ** 2 + ((yy - 920.0) / 90.0) ** 2))

    r = 0.028 + 0.14 * win + 0.68 * lamp + 0.85 * core + 0.30 * floor_ref + tex
    g = 0.036 + 0.34 * win + 0.42 * lamp + 0.65 * core + 0.18 * floor_ref + tex
    b = 0.052 + 0.56 * win + 0.10 * lamp + 0.25 * core + 0.05 * floor_ref + tex
    return np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plate", default=None, help="Path to a 1920x1080 night plate (.jpg/.png).")
    parser.add_argument("--out-dir", default="/tmp/house_demo", help="Output directory.")
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    lut_dir = os.path.join(out_dir, "luts")
    audio_dir = os.path.join(out_dir, "audio")
    tts_dir = os.path.join(audio_dir, "tts_lines")
    os.makedirs(tts_dir, exist_ok=True)

    generate_all_luts(lut_dir)
    lut = load_cube_lut(os.path.join(lut_dir, "house_obsidian_500t.cube"))

    if args.plate and os.path.exists(args.plate):
        pil = Image.open(args.plate).convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
        plate01 = np.array(pil, dtype=np.float32) / 255.0
    else:
        plate01 = make_synthetic_test_plate()

    dur_s = 6.0
    n_frames = 180
    n_samples = int(dur_s * SR)

    lines = [{
        "id": "01",
        "speaker": "A",
        "text": "Two in the morning, cold rain on wet stone, and one lamp burning inside.",
        "voice": "en-US-ChristopherNeural",
        "rate": "-12%",
        "pitch": "-4Hz",
        "gap_after": 0.4,
    }]
    turns, manifest = asyncio.run(synthesize_lines_with_telemetry(lines, tts_dir, start_cursor_s=0.35))
    json.dump({"turns": turns}, open(os.path.join(out_dir, "timeline_locked.json"), "w"), indent=2)
    json.dump({"turns": manifest}, open(os.path.join(out_dir, "tts_source_manifest.json"), "w"), indent=2)

    # Decode TTS MP3 onto 6.000s timeline
    rec = manifest[0]
    tmp_w = os.path.join(out_dir, "_t01.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", os.path.join(tts_dir, rec["mp3_filename"]), "-ar", str(SR), "-ac", "1", tmp_w],
        check=True,
    )
    _, pcm = wavfile.read(tmp_w)
    os.remove(tmp_w)
    xf = pcm.astype(np.float32) / 32768.0
    i0 = int(rec["trim_in_s"] * SR)
    i1 = min(len(xf), int(rec["trim_out_s"] * SR))
    seg = xf[i0:i1] * 0.85

    voice_st = np.zeros((n_samples, 2), dtype=np.float32)
    gate = np.zeros(n_samples, dtype=np.float32)
    dst0 = max(0, int((rec["timeline_start_s"] - (rec["first_word_offset_s"] - rec["trim_in_s"])) * SR))
    n = min(len(seg), n_samples - dst0)
    voice_st[dst0 : dst0 + n, 0] = seg[:n]
    voice_st[dst0 : dst0 + n, 1] = seg[:n]
    gate[dst0 : dst0 + n] = 1.0

    bed = build_rain_and_sub_bed(duration_s=dur_s)
    master_wav = os.path.join(out_dir, "master_audio_48k.wav")
    duck_and_master_stems_flac(voice_st, bed, gate, audio_dir, master_wav, tmp_dir=out_dir)

    cues = group_words_into_cues_2_to_5(turns[0]["words"], max_words=4)
    write_srt(cues, os.path.join(out_dir, "captions.srt"))
    patches = []
    for c in cues:
        x0, y0, rgba = render_house_caption_patch(c["text"], amber_words=("TWO", "MORNING", "LAMP"), crimson_words=("COLD", "BURNING"))
        patches.append({"start": c["start"], "end": c["end"], "x0": x0, "y0": y0, "rgb": rgba[:, :, :3], "a": rgba[:, :, 3:4]})

    def hook(frame: np.ndarray, gf: int, t: float) -> np.ndarray:
        for p in patches:
            if p["start"] - 0.02 <= t <= p["end"] + 0.03:
                al = np.float32(max(0.0, min(1.0, (t - (p["start"] - 0.02)) / 0.05, ((p["end"] + 0.03) - t) / 0.06)))
                ch_p, cw_p = p["rgb"].shape[:2]
                roi = frame[p["y0"] : p["y0"] + ch_p, p["x0"] : p["x0"] + cw_p]
                a = p["a"] * al
                frame[p["y0"] : p["y0"] + ch_p, p["x0"] : p["x0"] + cw_p] = roi * (1.0 - a) + p["rgb"] * a
                break
        if t < 0.24:
            frame *= np.float32(max(0.05, t / 0.24))
        elif t > dur_s - 0.24:
            frame *= np.float32(max(0.05, (dur_s - t) / 0.24))
        return frame

    clip_mp4 = os.path.join(out_dir, "_video_only.mp4")
    render_moving_shot_clip(plate01, lut, clip_mp4, n_frames=n_frames, halation_strength=0.24, rain_amount=0.26, mist_amount=0.09, frame_hook=hook)

    final_mp4 = os.path.join(out_dir, "demo_shot.mp4")
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", clip_mp4, "-i", master_wav,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
            "-r", "30", "-vsync", "cfr",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            final_mp4,
        ],
        check=True,
    )
    os.remove(clip_mp4)
    print(f"House Look demo shot ready: {final_mp4}")


if __name__ == "__main__":
    main()
