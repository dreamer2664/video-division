#!/usr/bin/env python3
"""
Master Reproducible A/B Benchmark Builder — video-division / research/build_ab_benchmark.py
Author: grade (Team B)

Reproduces every voice stem, graded still, 3D LUT, and quantitative metric table in
`research/ab-grade/` strictly offline from committed source files (zero API calls by default).

Run from repo root:
  python3 research/build_ab_benchmark.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import vocal_chain as vc
import grade_chain as gc


def stitch_turns_with_gaps(mp3_paths: List[str], gaps_s: List[float], trim_edges: bool = True) -> np.ndarray:
    """Decodes mono 48 kHz turns, trims dead encoder padding, and concatenates with specified gaps."""
    segs: List[np.ndarray] = []
    for idx, p in enumerate(mp3_paths):
        pcm = vc.decode_mono_48k(p)
        if trim_edges:
            # Trim leading/trailing encoder digital silence below -50 dBFS, keeping 35ms pre / 95ms post
            win = int(0.010 * vc.SR)
            nf = len(pcm) // win
            rms = np.sqrt(np.mean(pcm[: nf * win].reshape(nf, win) ** 2, axis=1))
            act = np.where(rms > 0.0032)[0]
            if len(act) > 0:
                i0 = max(0, int((act[0] * 0.010 - 0.035) * vc.SR))
                i1 = min(len(pcm), int(((act[-1] + 1) * 0.010 + 0.095) * vc.SR))
                pcm = pcm[i0:i1]
        # 15 ms cosine de-click on turn boundaries
        fade = min(int(0.015 * vc.SR), len(pcm) // 6)
        if fade > 8:
            pcm = pcm.copy()
            pcm[:fade] *= 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, fade)))
            pcm[-fade:] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, fade)))
        segs.append(pcm)
        if idx < len(gaps_s):
            segs.append(np.zeros(int(round(gaps_s[idx] * vc.SR)), dtype=np.float64))
    # Add 180 ms lead-in and 260 ms tail-out for clean playback framing
    lead = np.zeros(int(0.18 * vc.SR), dtype=np.float64)
    tail = np.zeros(int(0.26 * vc.SR), dtype=np.float64)
    return np.concatenate([lead, *segs, tail])


def run_voice_benchmarks(ab_dir: str) -> Dict[str, object]:
    src = os.path.join(ab_dir, "audio", "sources")
    out_audio = os.path.join(ab_dir, "audio")
    os.makedirs(out_audio, exist_ok=True)

    results: Dict[str, object] = {}

    # -----------------------------------------------------------------------
    # A. Full v07 Narration (4 turns: Turn 01, 06, 09, 12) — Old vs New Chain
    # -----------------------------------------------------------------------
    v07_4turns = [os.path.join(src, f) for f in ("turn_01_A.mp3", "turn_06_A.mp3", "turn_09_A.mp3", "turn_12_A.mp3")]

    # Old v07 chain: uniform 0.58s zero gaps, legacy 75-8000 Hz bandpass + +2.4 dB @ 2.9 kHz, no LUFS norm
    raw_v07_4_old = stitch_turns_with_gaps(v07_4turns, [0.58, 0.58, 0.58])
    st_v07_old = vc.process_legacy_v07_chain(raw_v07_4_old, normalize_to_minus16=False)
    p_v07_old = os.path.join(out_audio, "v07_narration_old_chain.flac")
    sha_old = vc.encode_audio(st_v07_old, p_v07_old)
    m_old = vc.evaluate_stem(p_v07_old)
    m_old["sha256"] = sha_old
    results["v07_full_old_chain"] = m_old

    # New chain on exact same v07 raw TTS turns, with asymmetric dramatic pauses + breath conditioner + -16 LUFS
    raw_v07_4_new = stitch_turns_with_gaps(v07_4turns, [0.64, 0.52, 0.94])
    st_v07_new, diag_v07_new = vc.process_vocal_chain(
        raw_v07_4_new, vc.ChainConfig(breath_conditioner="on", target_lufs=-16.0, seed=20260701)
    )
    p_v07_new = os.path.join(out_audio, "v07_narration_new_chain.flac")
    sha_new = vc.encode_audio(st_v07_new, p_v07_new)
    m_new = vc.evaluate_stem(p_v07_new)
    m_new["sha256"] = sha_new
    m_new["diagnostics"] = diag_v07_new
    results["v07_full_new_chain"] = m_new

    # -----------------------------------------------------------------------
    # B. ~15 s 3-Sentence A/B Voice Benchmark (Exact Same 3 Sentences = 191 chars)
    # -----------------------------------------------------------------------
    # 1. BEFORE: v07 Old Chain (ChristopherNeural -10%/-6Hz + legacy v07 chain)
    v07_3turns = [os.path.join(src, f) for f in ("turn_06_A.mp3", "turn_09_A.mp3", "turn_12_A.mp3")]
    raw_3_before = stitch_turns_with_gaps(v07_3turns, [0.58, 0.58])
    st_3_before = vc.process_legacy_v07_chain(raw_3_before, normalize_to_minus16=False)
    p_3_before = os.path.join(out_audio, "sample_15s_before_v07_old_chain.flac")
    sha = vc.encode_audio(st_3_before, p_3_before)
    m = vc.evaluate_stem(p_3_before)
    m["sha256"] = sha
    results["ab_15s_01_before_v07_old_chain"] = m

    # 2. AFTER (Local Same Speaker): ChristopherNeural native (0%/0Hz) + asymmetric pauses + New Chain
    chris_nat_3 = [os.path.join(src, f"chris_native_s{i}.mp3") for i in (1, 2, 3)]
    raw_3_chris = stitch_turns_with_gaps(chris_nat_3, [0.56, 0.92])
    st_3_chris, d_chris = vc.process_vocal_chain(
        raw_3_chris, vc.ChainConfig(breath_conditioner="on", target_lufs=-16.0, seed=20261102)
    )
    p_3_chris = os.path.join(out_audio, "sample_15s_after_local_chris_new_chain.flac")
    sha = vc.encode_audio(st_3_chris, p_3_chris)
    m = vc.evaluate_stem(p_3_chris)
    m["sha256"] = sha
    m["diagnostics"] = d_chris
    results["ab_15s_02_after_local_chris_new_chain"] = m

    # 3. AFTER (Local Best Baritone): BrianMultilingualNeural native + asymmetric pauses + New Chain
    brian_nat_3 = [os.path.join(src, f"brian_multi_native_s{i}.mp3") for i in (1, 2, 3)]
    raw_3_brian = stitch_turns_with_gaps(brian_nat_3, [0.58, 0.94])
    st_3_brian, d_brian = vc.process_vocal_chain(
        raw_3_brian, vc.ChainConfig(breath_conditioner="on", target_lufs=-16.0, seed=20261103)
    )
    p_3_brian = os.path.join(out_audio, "sample_15s_after_local_brian_new_chain.flac")
    sha = vc.encode_audio(st_3_brian, p_3_brian)
    m = vc.evaluate_stem(p_3_brian)
    m["sha256"] = sha
    m["diagnostics"] = d_brian
    results["ab_15s_03_after_local_brian_new_chain"] = m

    # 4-6. ElevenLabs eleven_multilingual_v2 (High-Stability Control, Expressive Brian, Documentary Bill)
    el_specs = [
        ("ab_15s_04_elevenlabs_v2_brian_highstab", "el_v2_brian_highstab.mp3", "sample_15s_elevenlabs_v2_brian_highstab_chained.flac"),
        ("ab_15s_05_elevenlabs_v2_brian_expressive", "el_v2_brian_expressive.mp3", "sample_15s_elevenlabs_v2_brian_expressive_chained.flac"),
        ("ab_15s_06_elevenlabs_v2_bill_documentary", "el_v2_bill_documentary.mp3", "sample_15s_elevenlabs_v2_bill_doc_chained.flac"),
    ]
    for key, src_mp3, out_flac in el_specs:
        raw_el = vc.decode_mono_48k(os.path.join(src, src_mp3))
        # Pad 150ms gentle lead/tail and run identical studio vocal chain (breath_conditioner="auto" detects real breaths!)
        raw_el = np.concatenate([np.zeros(int(0.15 * vc.SR)), raw_el, np.zeros(int(0.20 * vc.SR))])
        st_el, d_el = vc.process_vocal_chain(
            raw_el, vc.ChainConfig(breath_conditioner="off", target_lufs=-16.0, seed=20261105)
        )
        p_out = os.path.join(out_audio, out_flac)
        sha = vc.encode_audio(st_el, p_out)
        m = vc.evaluate_stem(p_out)
        m["sha256"] = sha
        m["diagnostics"] = d_el
        results[key] = m

    return results


def run_image_benchmarks(ab_dir: str) -> Dict[str, object]:
    stills_dir = os.path.join(ab_dir, "stills")
    src_dir = os.path.join(stills_dir, "sources")
    os.makedirs(stills_dir, exist_ok=True)

    cfg = gc.GradeConfig()
    lut_path = os.path.join(stills_dir, "kodak_5219_2383_house.cube")
    lut_sha = gc.export_cube_lut(lut_path, cfg)

    shots = [
        ("still_01", "plate_01_vault_lanterns.jpg", "Wide Vault Room — Lantern Practicals vs Storm Spillway"),
        ("still_02", "plate_02_ceiling_horn.jpg", "Overhead Vaulted Arch — Brass Horn & Distant Cage Lamp"),
        ("still_03", "plate_03_cracked_sightglass.jpg", "Macro Sight-Glass — Oil Lantern vs Submerged Cyan Chamber"),
    ]

    shot_reports: Dict[str, object] = {}
    bef_meds_lin: List[float] = []
    aft_meds_lin: List[float] = []
    bef_toes: List[float] = []
    aft_toes: List[float] = []

    for idx, (slug, fname, label) in enumerate(shots):
        in_path = os.path.join(src_dir, fname)
        raw_img = Image.open(in_path).convert("RGB")
        clean_img = gc.clean_and_scale_plate(raw_img, cfg.target_w, cfg.target_h)
        bef_srgb = np.asarray(clean_img, dtype=np.float32) / 255.0
        aft_srgb, diag = gc.grade_plate_array(bef_srgb, cfg, shot_seed_offset=idx * 101)

        p_bef = os.path.join(stills_dir, f"{slug}_before.jpg")
        p_aft = os.path.join(stills_dir, f"{slug}_after.jpg")
        p_cmp = os.path.join(stills_dir, f"{slug}_ab_card.jpg")

        clean_img.save(p_bef, quality=95, subsampling=0)
        Image.fromarray(np.round(aft_srgb * 255.0).astype(np.uint8)).save(p_aft, quality=95, subsampling=0)

        m_bef = gc.measure_plate_metrics(bef_srgb)
        m_aft = gc.measure_plate_metrics(aft_srgb)
        card = gc.render_split_comparison_card(bef_srgb, aft_srgb, label, m_bef, m_aft)
        card.save(p_cmp, quality=94, subsampling=0)

        # Track cross-shot consistency in photographic stops (scene-linear median luminance)
        b_lin_y = 0.2126 * gc.srgb_to_linear(bef_srgb)[..., 0] + 0.7152 * gc.srgb_to_linear(bef_srgb)[..., 1] + 0.0722 * gc.srgb_to_linear(bef_srgb)[..., 2]
        a_lin_y = 0.2126 * gc.srgb_to_linear(aft_srgb)[..., 0] + 0.7152 * gc.srgb_to_linear(aft_srgb)[..., 1] + 0.0722 * gc.srgb_to_linear(aft_srgb)[..., 2]
        bef_meds_lin.append(float(np.median(b_lin_y)))
        aft_meds_lin.append(float(np.median(a_lin_y)))
        bef_toes.append(m_bef["y_p02_ire"])
        aft_toes.append(m_aft["y_p02_ire"])

        shot_reports[slug] = {
            "label": label,
            "source": fname,
            "diagnostics": diag,
            "before": m_bef,
            "after": m_aft,
        }

    bef_range_stops = math.log2(max(bef_meds_lin) / max(min(bef_meds_lin), 1e-6))
    aft_range_stops = math.log2(max(aft_meds_lin) / max(min(aft_meds_lin), 1e-6))

    return {
        "lut_cube": {"path": "stills/kodak_5219_2383_house.cube", "sha256": lut_sha, "size": cfg.lut_size},
        "cross_shot_consistency": {
            "before_midtone_range_stops": round(bef_range_stops, 3),
            "after_midtone_range_stops": round(aft_range_stops, 3),
            "midtone_jump_reduction_pct": round((1.0 - aft_range_stops / max(bef_range_stops, 1e-6)) * 100.0, 1),
            "before_toe_p02_ire_values": bef_toes,
            "after_toe_p02_ire_values": aft_toes,
            "before_toe_p02_std_ire": round(float(np.std(bef_toes)), 3),
            "after_toe_p02_std_ire": round(float(np.std(aft_toes)), 3),
        },
        "stills": shot_reports,
    }


def main() -> None:
    ab_dir = os.path.join(HERE, "ab-grade")
    print("[1/2] Running deterministic voice chain & A/B benchmarks...")
    voice_res = run_voice_benchmarks(ab_dir)
    print("[2/2] Running deterministic photochemical plate grading & metrics...")
    img_res = run_image_benchmarks(ab_dir)

    full_metrics = {
        "agent": "grade",
        "branch": "grade/voice-imaging",
        "date": "2026-11-01",
        "voice_benchmarks": voice_res,
        "image_benchmarks": img_res,
    }
    out_json = os.path.join(ab_dir, "metrics.json")
    with open(out_json, "w") as f:
        json.dump(full_metrics, f, indent=2)
    print(f"Done. Wrote {out_json}")


if __name__ == "__main__":
    main()
