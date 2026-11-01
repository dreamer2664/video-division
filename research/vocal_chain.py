#!/usr/bin/env python3
"""
Reusable Documentary Vocal Mix Chain — video-division / research/vocal_chain.py
Author: grade (Team B)

Transforms a flat mono/stereo TTS or dry booth stem into an intimate, broadcast-ready
48 kHz stereo documentary voiceover stem at -16.0 LUFS (TP <= -1.5 dBTP).

Signal Chain Architecture (8 deterministic DSP stages):
  0. Optional Breath & Booth-Air Conditioner (replaces dead -inf dBFS TTS gaps with
     -52 dBFS studio air + subtle pre-phrase velar/palatal inhalation cues)
  1. High-Pass Filter: 4th-order Butterworth @ 80 Hz + cardioid proximity shelf (+1.5 dB @ 135 Hz)
  2. Boxiness & Spectral-Tilt Conditioning: -3.2 dB bell @ 355 Hz (Q=1.85) + adaptive
     high-mid vocoder buzz shelf above 4.0 kHz when input tilt > -3.6 dB/octave
  3. Presence Lift: +1.8 dB bell @ 3,000 Hz (Q=1.15) + -1.0 dB harshness dip @ 4,600 Hz (Q=2.2)
  4. Split-Band Dynamic De-Esser: 6,000-8,500 Hz sidechain envelope detector with
     0.8 ms attack / 45 ms release, up to -5.2 dB dynamic sibilance attenuation
  5. Slow 3:1 Optical-Style Compressor: 22 ms attack, 220 ms release, 3.0:1 ratio,
     4.0 dB soft knee (~3.5-4.5 dB peak GR so consonants pass intact while tails lift)
  6. Subtle Early-Reflection Studio Booth IR: 7 discrete wood/booth reflections across
     8.7-23.8 ms, L/R micro-decorrelated, damped > 4.8 kHz, mixed at -21.0 dB wet
  7. Light Asymmetric Tube/Tape Saturation: biased soft-clipper adding -28 dB 2nd-harmonic
     chest warmth alongside gentle odd-order peak rounding
  8. Two-Pass ITU-R BS.1770-4 / EBU R128 Normalization to -16.0 LUFS, TP <= -1.5 dBTP

CLI Usage:
  python3 research/vocal_chain.py input.mp3 output.flac --report metrics.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000


# ---------------------------------------------------------------------------
# Biquad & Filter Primitives (RBJ Audio EQ Cookbook, 64-bit internal state)
# ---------------------------------------------------------------------------

def peaking_biquad(x: np.ndarray, freq_hz: float, q: float, gain_db: float, sr: int = SR) -> np.ndarray:
    if abs(gain_db) < 1e-6:
        return x
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * freq_hz / sr
    alpha = math.sin(w0) / (2.0 * q)
    b0 = 1.0 + alpha * a
    b1 = -2.0 * math.cos(w0)
    b2 = 1.0 - alpha * a
    a0 = 1.0 + alpha / a
    a1 = -2.0 * math.cos(w0)
    a2 = 1.0 - alpha / a
    sos = np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)
    return signal.sosfilt(sos, x.astype(np.float64))


def high_shelf_biquad(x: np.ndarray, freq_hz: float, q: float, gain_db: float, sr: int = SR) -> np.ndarray:
    if abs(gain_db) < 1e-6:
        return x
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * freq_hz / sr
    cos_w0 = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * q)
    two_sqrt_a_alpha = 2.0 * math.sqrt(a) * alpha
    b0 = a * ((a + 1.0) + (a - 1.0) * cos_w0 + two_sqrt_a_alpha)
    b1 = -2.0 * a * ((a - 1.0) + (a + 1.0) * cos_w0)
    b2 = a * ((a + 1.0) + (a - 1.0) * cos_w0 - two_sqrt_a_alpha)
    a0 = (a + 1.0) - (a - 1.0) * cos_w0 + two_sqrt_a_alpha
    a1 = 2.0 * ((a - 1.0) - (a + 1.0) * cos_w0)
    a2 = (a + 1.0) - (a - 1.0) * cos_w0 - two_sqrt_a_alpha
    sos = np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)
    return signal.sosfilt(sos, x.astype(np.float64))


# ---------------------------------------------------------------------------
# Audio I/O & Loudness / Acoustic Metering
# ---------------------------------------------------------------------------

def decode_mono_48k(path: str) -> np.ndarray:
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"]
    )
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)


def decode_stereo_48k(path: str) -> np.ndarray:
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"]
    )
    return np.frombuffer(raw, dtype="<f4").astype(np.float64).reshape(-1, 2)


def encode_audio(stereo_48k: np.ndarray, out_path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    clipped = np.clip(stereo_48k, -0.9999, 0.9999)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp_wav = tf.name
    try:
        # Write 24-bit / 32-bit float intermediate WAV for clean encoding
        wavfile.write(tmp_wav, SR, clipped.astype(np.float32))
        ext = os.path.splitext(out_path)[1].lower()
        if ext == ".flac":
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", tmp_wav, "-c:a", "flac", "-sample_fmt", "s16", "-compression_level", "12", out_path]
        elif ext == ".mp3":
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", tmp_wav, "-c:a", "libmp3lame", "-b:a", "192k", out_path]
        else:
            cmd = ["ffmpeg", "-y", "-v", "error", "-i", tmp_wav, "-c:a", "pcm_s16le", out_path]
        subprocess.run(cmd, check=True)
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)
    return hashlib.sha256(open(out_path, "rb").read()).hexdigest()


def measure_loudnorm_ebur128(stereo_48k: np.ndarray) -> Dict[str, float]:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp_wav = tf.name
    try:
        wavfile.write(tmp_wav, SR, np.clip(stereo_48k, -0.9999, 0.9999).astype(np.float32))
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", tmp_wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        m = re.search(r"\{\s*\"input_i\".*?\}", proc.stderr, flags=re.S)
        if not m:
            raise RuntimeError("Could not parse ffmpeg loudnorm JSON output")
        data = json.loads(m.group(0))
        return {
            "integrated_lufs": float(data["input_i"]),
            "true_peak_dbtp": float(data["input_tp"]),
            "lra_lu": float(data["input_lra"]),
            "thresh_lufs": float(data["input_thresh"]),
        }
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)


def measure_spectral_tilt_db_oct(mono_48k: np.ndarray) -> Tuple[float, float, float, float]:
    active = mono_48k[np.abs(mono_48k) > 0.008]
    if len(active) < 4096:
        active = mono_48k
    freqs, psd = signal.welch(active, fs=SR, nperseg=4096)
    mask = (freqs >= 100.0) & (freqs <= 8000.0) & (psd > 1e-20)
    slope = float(np.polyfit(np.log2(freqs[mask] / 100.0), 10.0 * np.log10(psd[mask]), 1)[0])
    centroid = float(np.sum(freqs * psd) / max(float(np.sum(psd)), 1e-18))

    e_body = float(np.trapezoid(psd[(freqs >= 100.0) & (freqs <= 500.0)], freqs[(freqs >= 100.0) & (freqs <= 500.0)]))
    e_sib = float(np.trapezoid(psd[(freqs >= 6000.0) & (freqs <= 8500.0)], freqs[(freqs >= 6000.0) & (freqs <= 8500.0)]))
    e_air = float(np.trapezoid(psd[(freqs >= 8500.0) & (freqs <= 15000.0)], freqs[(freqs >= 8500.0) & (freqs <= 15000.0)]))
    sib_rel_db = 10.0 * math.log10((e_sib + 1e-20) / (e_body + 1e-20))
    air_rel_db = 10.0 * math.log10((e_air + 1e-20) / (e_body + 1e-20))
    return slope, centroid, sib_rel_db, air_rel_db


def measure_f0_statistics(mono_48k: np.ndarray, f0_min: float = 62.0, f0_max: float = 215.0) -> Dict[str, float]:
    x = signal.resample_poly(mono_48k, 1, 3)
    sr16 = 16000
    bp = signal.sosfilt(signal.butter(4, [f0_min, f0_max + 25.0], btype="bandpass", fs=sr16, output="sos"), x)
    win = int(0.045 * sr16)
    hop = int(0.010 * sr16)
    min_lag = int(sr16 / f0_max)
    max_lag = int(sr16 / f0_min)

    f0s: List[float] = []
    for i in range(0, len(bp) - win, hop):
        orig = x[i : i + win]
        if float(np.sqrt(np.mean(orig ** 2))) < 0.012:
            continue
        seg = (bp[i : i + win] - float(np.mean(bp[i : i + win]))) * np.hanning(win)
        ac = signal.correlate(seg, seg, mode="full", method="fft")[win - 1 :]
        if ac[0] <= 1e-12:
            continue
        ac = ac / ac[0]
        sub = ac[min_lag:max_lag]
        pks, _ = signal.find_peaks(sub, prominence=0.08)
        if not len(pks):
            continue
        max_val = float(np.max(sub[pks]))
        if max_val < 0.45:
            continue
        cand = [p for p in pks if sub[p] >= 0.88 * max_val]
        pk = int(cand[0] + min_lag)
        if 1 <= pk < len(ac) - 1:
            y0, y1, y2 = float(ac[pk - 1]), float(ac[pk]), float(ac[pk + 1])
            denom = y0 - 2.0 * y1 + y2
            delta = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-9 else 0.0
            pk_f = pk + float(np.clip(delta, -0.5, 0.5))
        else:
            pk_f = float(pk)
        f0s.append(sr16 / pk_f)

    if len(f0s) >= 5:
        f0_arr = signal.medfilt(np.array(f0s, dtype=np.float64), kernel_size=5)
    elif len(f0s) > 0:
        f0_arr = np.array(f0s, dtype=np.float64)
    else:
        return {"f0_mean_hz": 0.0, "f0_median_hz": 0.0, "f0_std_hz": 0.0, "f0_std_st": 0.0, "f0_iqr_st": 0.0, "f0_p95_p05_st": 0.0}

    med = float(np.median(f0_arr))
    st = 12.0 * np.log2(f0_arr / med)
    return {
        "f0_mean_hz": round(float(np.mean(f0_arr)), 2),
        "f0_median_hz": round(med, 2),
        "f0_std_hz": round(float(np.std(f0_arr)), 2),
        "f0_std_st": round(float(np.std(st)), 2),
        "f0_iqr_st": round(float(np.percentile(st, 75) - np.percentile(st, 25)), 2),
        "f0_p95_p05_st": round(float(np.percentile(st, 95) - np.percentile(st, 5)), 2),
    }


def evaluate_stem(path: str) -> Dict[str, object]:
    st = decode_stereo_48k(path)
    mono = 0.5 * (st[:, 0] + st[:, 1])
    loud = measure_loudnorm_ebur128(st)
    tilt, centroid, sib_db, air_db = measure_spectral_tilt_db_oct(mono)
    f0 = measure_f0_statistics(mono)

    # Measure inter-phrase pause floor (check if digital -inf or living room/breath floor)
    win = int(0.020 * SR)
    n_frames = len(mono) // win
    frames = mono[: n_frames * win].reshape(n_frames, win)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    thr = max(float(np.max(rms)) * 0.035, 1e-4)
    act = np.where(rms >= thr)[0]
    pause_floor_db = -120.0
    if len(act) > 4:
        interior = rms[act[0] : act[-1] + 1]
        quiet = interior[interior < thr]
        if len(quiet) > 3:
            pause_floor_db = 20.0 * math.log10(max(float(np.median(quiet)), 1e-6))

    return {
        "duration_s": round(len(mono) / SR, 2),
        **{k: round(v, 2) for k, v in loud.items()},
        "spectral_tilt_db_oct": round(tilt, 2),
        "spectral_centroid_hz": round(centroid, 1),
        "sibilance_6_8k5_rel_body_db": round(sib_db, 2),
        "air_8k5_15k_rel_body_db": round(air_db, 2),
        "pause_floor_dbfs": round(pause_floor_db, 1),
        **f0,
    }


# ---------------------------------------------------------------------------
# Stage Processors for the New Reusable Mix Chain
# ---------------------------------------------------------------------------

@dataclass
class ChainConfig:
    breath_conditioner: str = "auto"   # "auto" | "on" | "off"
    hpf_hz: float = 80.0
    proximity_hz: float = 135.0
    proximity_gain_db: float = 1.5
    boxiness_hz: float = 355.0
    boxiness_gain_db: float = -3.2
    boxiness_q: float = 1.85
    adaptive_tilt_target_db_oct: float = -4.15
    presence_hz: float = 3000.0
    presence_gain_db: float = 1.8
    presence_q: float = 1.15
    harsh_dip_hz: float = 4600.0
    harsh_dip_gain_db: float = -1.1
    deess_low_hz: float = 6000.0
    deess_high_hz: float = 8500.0
    deess_max_cut_db: float = 5.0
    comp_ratio: float = 3.0
    comp_attack_ms: float = 22.0
    comp_release_ms: float = 220.0
    comp_knee_db: float = 4.0
    comp_target_gr_db: float = 3.8
    er_wet_db: float = -21.0
    sat_drive: float = 0.85
    sat_bias: float = 0.09
    target_lufs: float = -16.0
    max_tp_dbtp: float = -1.5
    seed: int = 20261101


def _synthesize_soft_inhalation(dur_s: float, rng: np.random.Generator) -> np.ndarray:
    """Physiological velar/palatal quiet inhalation (Szekely et al., ICASSP 2020)."""
    n = int(round(dur_s * SR))
    white = rng.normal(0.0, 1.0, n)
    # Oral-tract inspiratory resonances (~520 Hz, ~1580 Hz, ~2650 Hz) + gentle air
    f1 = signal.sosfilt(signal.butter(2, [380, 720], btype="bandpass", fs=SR, output="sos"), white) * 0.55
    f2 = signal.sosfilt(signal.butter(2, [1300, 1950], btype="bandpass", fs=SR, output="sos"), white) * 0.32
    f3 = signal.sosfilt(signal.butter(2, [2300, 3400], btype="bandpass", fs=SR, output="sos"), white) * 0.16
    air = signal.sosfilt(signal.butter(2, [3500, 7500], btype="bandpass", fs=SR, output="sos"), white) * 0.06
    breath = f1 + f2 + f3 + air
    # Natural asymmetric inspiratory envelope (gradual 45% rise, 55% taper)
    t = np.linspace(0.0, 1.0, n)
    env = np.sin(np.pi * (t ** 0.82)) ** 1.6
    breath *= env
    rms = max(float(np.sqrt(np.mean(breath ** 2))), 1e-8)
    # Calibrate quiet documentary inhalation around -37 dBFS relative to normalized speech
    return breath * (10.0 ** (-37.5 / 20.0) / rms)


def stage0_breath_and_booth_air(x: np.ndarray, mode: str, seed: int) -> Tuple[np.ndarray, int]:
    if mode == "off":
        return x.copy(), 0
    rng = np.random.default_rng(seed)

    # Pre-normalize working copy to -20 dBFS active RMS so thresholds are scale-invariant
    act = x[np.abs(x) > np.max(np.abs(x)) * 0.04]
    act_rms = float(np.sqrt(np.mean(act ** 2))) if len(act) > 200 else 0.08
    y = x * (0.10 / max(act_rms, 1e-6))

    # Check if pause floor is already live (e.g. ElevenLabs or real studio mic > -68 dBFS)
    win = int(0.020 * SR)
    nf = len(y) // win
    rms = np.sqrt(np.mean(y[: nf * win].reshape(nf, win) ** 2, axis=1))
    thr = 0.0035
    voiced_idx = np.where(rms >= thr)[0]
    if len(voiced_idx) > 4 and mode == "auto":
        interior = rms[voiced_idx[0] + 2 : max(voiced_idx[0] + 3, voiced_idx[-1] - 2)]
        quiet = interior[interior < thr]
        if len(quiet) > 3 and 20.0 * math.log10(max(float(np.percentile(quiet, 65)), 1e-7)) > -68.0:
            # Already contains organic room/breath noise; add only -56 dBFS floor continuity, zero synthetic breaths
            pink_src = rng.normal(0.0, 1.0, len(y))
            bt = signal.sosfilt(signal.butter(2, [95.0, 2400.0], btype="bandpass", fs=SR, output="sos"), pink_src)
            bt *= (10.0 ** (-56.0 / 20.0)) / max(float(np.sqrt(np.mean(bt ** 2))), 1e-8)
            return y + bt, 0

    # Add ultra-subtle -53 dBFS warm treated-booth room tone across the stem (eliminates -inf vacuum)
    pink_src = rng.normal(0.0, 1.0, len(y))
    booth_tone = signal.sosfilt(signal.butter(2, [95.0, 2400.0], btype="bandpass", fs=SR, output="sos"), pink_src)
    bt_rms = max(float(np.sqrt(np.mean(booth_tone ** 2))), 1e-8)
    booth_tone *= (10.0 ** (-53.5 / 20.0)) / bt_rms
    out = y + booth_tone

    # Detect inter-sentence dead gaps >= 0.42 s and place a subtle 155 ms inhalation before speech onset
    breaths_added = 0
    is_quiet = rms < thr
    i = voiced_idx[0] if len(voiced_idx) else 0
    end_limit = voiced_idx[-1] if len(voiced_idx) else 0
    while i < end_limit:
        if is_quiet[i]:
            j = i
            while j < end_limit and is_quiet[j]:
                j += 1
            gap_s = (j - i) * 0.020
            if gap_s >= 0.44:
                b_dur = min(0.165, max(0.125, gap_s * 0.24))
                b_wav = _synthesize_soft_inhalation(b_dur, rng)
                # End breath 45 ms before next phrase consonant onset
                end_samp = max(0, j * win - int(0.045 * SR))
                start_samp = max(i * win + int(0.060 * SR), end_samp - len(b_wav))
                seg_len = end_samp - start_samp
                if seg_len > int(0.090 * SR):
                    out[start_samp:end_samp] += b_wav[:seg_len]
                    breaths_added += 1
            i = j
        else:
            i += 1
    return out, breaths_added


def stage4_split_band_deesser(x: np.ndarray, low_hz: float, high_hz: float, max_cut_db: float) -> Tuple[np.ndarray, float]:
    """Zero-phase-aligned split-band dynamic sibilance suppressor (6.0 - 8.5 kHz)."""
    sos_sib = signal.butter(3, [low_hz, high_hz], btype="bandpass", fs=SR, output="sos")
    sib_band = signal.sosfiltfilt(sos_sib, x)
    residual = x - sib_band

    # Fast RMS envelopes (5 ms sibilant vs 20 ms full-band reference)
    sib_sq = sib_band ** 2
    ref_sq = residual ** 2 + 1e-12
    a_fast = math.exp(-1.0 / (0.004 * SR))
    a_ref = math.exp(-1.0 / (0.018 * SR))
    sib_env = np.sqrt(signal.lfilter([1.0 - a_fast], [1.0, -a_fast], sib_sq) + 1e-12)
    ref_env = np.sqrt(signal.lfilter([1.0 - a_ref], [1.0, -a_ref], ref_sq) + 1e-12)

    # Trigger when sibilant band exceeds -5.5 dB relative to vocal body AND is above noise gate
    ratio_db = 20.0 * np.log10((sib_env + 1e-9) / (ref_env + 1e-4))
    over_db = np.maximum(0.0, ratio_db - (-5.5))
    raw_cut_db = np.minimum(max_cut_db, over_db * 0.72)

    # Smooth gain-reduction envelope: 0.8 ms attack, 45 ms release
    att_c = math.exp(-1.0 / (0.0008 * SR))
    rel_c = math.exp(-1.0 / (0.045 * SR))
    gr_db = np.zeros_like(raw_cut_db)
    cur = 0.0
    for idx in range(len(raw_cut_db)):
        t_db = float(raw_cut_db[idx])
        if t_db > cur:
            cur = att_c * cur + (1.0 - att_c) * t_db
        else:
            cur = rel_c * cur + (1.0 - rel_c) * t_db
        gr_db[idx] = cur

    gain_lin = 10.0 ** (-gr_db / 20.0)
    return residual + sib_band * gain_lin, float(np.percentile(gr_db[gr_db > 0.2], 95)) if np.any(gr_db > 0.2) else 0.0


def stage5_optical_compressor(
    x: np.ndarray, ratio: float, attack_ms: float, release_ms: float, knee_db: float, target_gr_db: float
) -> Tuple[np.ndarray, float]:
    """Slow-attack (22 ms), smooth-release (220 ms) 3:1 optical-style vocal leveler."""
    # Calibrate threshold automatically from active speech P82 level so ~3.5-4.5 dB peak GR is achieved
    win = int(0.015 * SR)
    rms_win = np.sqrt(signal.lfilter(np.ones(win) / win, [1.0], x ** 2) + 1e-12)
    active = rms_win[rms_win > np.max(rms_win) * 0.06]
    p85_db = 20.0 * math.log10(max(float(np.percentile(active, 85)) if len(active) else 0.08, 1e-6))
    thresh_db = p85_db - (target_gr_db * ratio / (ratio - 1.0))

    env_db = 20.0 * np.log10(rms_win + 1e-9)
    over = env_db - thresh_db
    half_k = knee_db / 2.0
    slope = 1.0 - 1.0 / ratio

    inst_gr_db = np.zeros_like(env_db)
    below = over <= -half_k
    above = over >= half_k
    in_knee = (~below) & (~above)
    inst_gr_db[above] = slope * over[above]
    inst_gr_db[in_knee] = slope * ((over[in_knee] + half_k) ** 2) / (2.0 * knee_db)

    # Block-decimated (0.5 ms = 24 samples) envelope follower for speed & exact time constants
    step = 24
    sr_blk = SR / step
    att_c = math.exp(-1.0 / (max(attack_ms, 0.5) * 0.001 * sr_blk))
    rel_c = math.exp(-1.0 / (max(release_ms, 5.0) * 0.001 * sr_blk))
    blk_in = inst_gr_db[::step]
    blk_gr = np.zeros_like(blk_in)
    cur = 0.0
    for i in range(len(blk_in)):
        v = float(blk_in[i])
        if v > cur:
            cur = att_c * cur + (1.0 - att_c) * v
        else:
            cur = rel_c * cur + (1.0 - rel_c) * v
        blk_gr[i] = cur

    smooth_gr_db = np.interp(np.arange(len(x)), np.arange(len(blk_gr)) * step, blk_gr)
    makeup_db = float(np.percentile(smooth_gr_db, 80)) * 0.65
    gain = 10.0 ** ((-smooth_gr_db + makeup_db) / 20.0)
    return x * gain, float(np.percentile(smooth_gr_db, 98))


def stage6_early_reflection_booth(x: np.ndarray, wet_db: float) -> np.ndarray:
    """
    7-tap wood-lined VO booth early-reflection cluster (8.7 ms - 23.8 ms), stereo micro-decorrelated.
    Damped > 4.8 kHz and < 180 Hz so sibilants never smear and low chest stays mono-tight.
    """
    ir_len = int(0.040 * SR)
    ir_l = np.zeros(ir_len, dtype=np.float64)
    ir_r = np.zeros(ir_len, dtype=np.float64)

    # (delay_ms_L, delay_ms_R, gain_linear, polarity)
    taps = [
        (8.7, 9.3, 0.52, +1.0),
        (11.4, 10.8, 0.41, -1.0),
        (13.9, 14.6, 0.34, +1.0),
        (16.8, 16.1, 0.27, +1.0),
        (19.2, 20.1, 0.21, -1.0),
        (21.7, 21.0, 0.16, +1.0),
        (23.8, 24.4, 0.12, -1.0),
    ]
    for dl, dr, g, pol in taps:
        il = min(ir_len - 1, int(round(dl * 0.001 * SR)))
        ir = min(ir_len - 1, int(round(dr * 0.001 * SR)))
        ir_l[il] += g * pol
        ir_r[ir] += g * pol

    sos_damp = signal.butter(2, [180.0, 4800.0], btype="bandpass", fs=SR, output="sos")
    wet_l = signal.sosfilt(sos_damp, signal.fftconvolve(x, ir_l, mode="same"))
    wet_r = signal.sosfilt(sos_damp, signal.fftconvolve(x, ir_r, mode="same"))

    # Normalize wet RMS to match dry RMS before applying wet_db blend (-21 dB)
    dry_rms = max(float(np.sqrt(np.mean(x ** 2))), 1e-8)
    wet_rms = max(float(np.sqrt(0.5 * (np.mean(wet_l ** 2) + np.mean(wet_r ** 2)))), 1e-8)
    scale = (dry_rms / wet_rms) * (10.0 ** (wet_db / 20.0))
    return np.column_stack([x + wet_l * scale, x + wet_r * scale])


def stage7_asymmetric_saturation(stereo: np.ndarray, drive: float, bias: float) -> np.ndarray:
    """Gentle transformer/tube soft-saturation adding subtle 2nd-harmonic warmth."""
    peak = max(float(np.max(np.abs(stereo))), 1e-6)
    norm = stereo / peak * 0.65
    dc = math.tanh(drive * bias)
    sat = (np.tanh(drive * (norm + bias)) - dc) / drive
    # Remove any residual sub-20 Hz DC shift
    sos_dc = signal.butter(1, 20.0, btype="highpass", fs=SR, output="sos")
    sat = signal.sosfilt(sos_dc, sat, axis=0)
    return sat * (peak / 0.65)


def stage8_loudnorm_two_pass(stereo: np.ndarray, target_lufs: float = -16.0, max_tp_dbtp: float = -1.5) -> np.ndarray:
    """Exact two-pass EBU R128 loudness normalization with transparent lookahead peak ceiling."""
    y = stereo.copy()
    # Pre-scale near target
    rms = max(float(np.sqrt(np.mean(y ** 2))), 1e-7)
    y *= (10.0 ** ((target_lufs + 1.5) / 20.0)) / rms

    for _ in range(2):
        m = measure_loudnorm_ebur128(y)
        err_db = target_lufs - m["integrated_lufs"]
        y *= 10.0 ** (err_db / 20.0)
        # Soft-ceiling true-peak guard at -2.08 dBFS so 4x inter-sample TP stays strictly <= -1.5 dBTP
        ceil_lin = 10.0 ** ((max_tp_dbtp - 0.58) / 20.0)
        abs_max = np.max(np.abs(y), axis=1)
        if float(np.max(abs_max)) > ceil_lin:
            # Smooth 1.5 ms lookahead peak limiter only on transient overs
            over_ratio = np.maximum(1.0, abs_max / ceil_lin)
            k = int(0.0015 * SR)
            env = signal.filtfilt(np.ones(k) / k, [1.0], over_ratio)
            env = np.maximum(env, over_ratio)
            y = y / env[:, None]

    # Final fine trim within +/- 0.08 LU if peak headroom allows
    m_fin = measure_loudnorm_ebur128(y)
    err_fin = target_lufs - m_fin["integrated_lufs"]
    if abs(err_fin) > 0.04 and (m_fin["true_peak_dbtp"] + err_fin) <= (max_tp_dbtp - 0.12):
        y *= 10.0 ** (err_fin / 20.0)
    return y


def process_vocal_chain(mono_48k: np.ndarray, cfg: Optional[ChainConfig] = None) -> Tuple[np.ndarray, Dict[str, object]]:
    if cfg is None:
        cfg = ChainConfig()

    raw_tilt, raw_cent, raw_sib, raw_air = measure_spectral_tilt_db_oct(mono_48k)

    # Stage 0: Breath & booth-air conditioner
    y, breaths_added = stage0_breath_and_booth_air(mono_48k, cfg.breath_conditioner, cfg.seed)

    # Stage 1: 80 Hz 4th-order Butterworth HPF + cardioid proximity warmth (+1.5 dB @ 135 Hz)
    sos_hpf = signal.butter(4, cfg.hpf_hz, btype="highpass", fs=SR, output="sos")
    y = signal.sosfilt(sos_hpf, y)
    y = peaking_biquad(y, cfg.proximity_hz, 1.05, cfg.proximity_gain_db)

    # Stage 2: Subtractive boxiness cut (355 Hz) + adaptive vocoder buzz tilt tamer
    y = peaking_biquad(y, cfg.boxiness_hz, cfg.boxiness_q, cfg.boxiness_gain_db)
    tilt_shelf_db = 0.0
    if raw_tilt > -3.60:
        # Tame flat neural vocoder upper-harmonic buzz (e.g. ChristopherNeural at -2.3 dB/oct)
        tilt_shelf_db = float(np.clip((cfg.adaptive_tilt_target_db_oct - raw_tilt) * 1.45, -3.8, 0.0))
        y = high_shelf_biquad(y, 3800.0, 0.68, tilt_shelf_db)

    # Stage 3: Gentle 3 kHz presence lift + 4.6 kHz harshness micro-dip
    y = peaking_biquad(y, cfg.presence_hz, cfg.presence_q, cfg.presence_gain_db)
    y = peaking_biquad(y, cfg.harsh_dip_hz, 2.2, cfg.harsh_dip_gain_db)

    # Stage 4: Split-band dynamic de-esser (6.0 - 8.5 kHz)
    y, deess_p95_db = stage4_split_band_deesser(y, cfg.deess_low_hz, cfg.deess_high_hz, cfg.deess_max_cut_db)

    # Stage 5: Slow 3:1 optical-style compressor
    y, comp_p98_gr_db = stage5_optical_compressor(
        y, cfg.comp_ratio, cfg.comp_attack_ms, cfg.comp_release_ms, cfg.comp_knee_db, cfg.comp_target_gr_db
    )

    # Stage 6: Subtle early-reflection studio booth IR (-21 dB wet)
    stereo = stage6_early_reflection_booth(y, cfg.er_wet_db)

    # Stage 7: Light asymmetric transformer/tube saturation
    stereo = stage7_asymmetric_saturation(stereo, cfg.sat_drive, cfg.sat_bias)

    # Stage 8: Two-pass EBU R128 -16.0 LUFS normalization
    stereo = stage8_loudnorm_two_pass(stereo, cfg.target_lufs, cfg.max_tp_dbtp)

    stage_diag = {
        "raw_spectral_tilt_db_oct": round(raw_tilt, 2),
        "adaptive_high_shelf_db": round(tilt_shelf_db, 2),
        "breaths_injected": breaths_added,
        "deesser_p95_cut_db": round(deess_p95_db, 2),
        "compressor_p98_gr_db": round(comp_p98_gr_db, 2),
        "config": asdict(cfg),
    }
    return stereo, stage_diag


def process_legacy_v07_chain(mono_48k: np.ndarray, normalize_to_minus16: bool = False) -> np.ndarray:
    """Exact reproduction of videos/team-b/grade-v07/build_audio_v07.py::process_voice_A_reel."""
    sos = signal.butter(3, [75.0 / (SR * 0.5), 8000.0 / (SR * 0.5)], btype="bandpass", output="sos")
    y = signal.sosfilt(sos, mono_48k)
    y = peaking_biquad(y, 128.0, 1.1, +1.8)
    y = peaking_biquad(y, 330.0, 1.5, -2.2)
    y = peaking_biquad(y, 2900.0, 1.2, +2.4)
    y = np.tanh(y * 1.18) / 1.12
    # v07 target_turn_rms = -20.8 dBFS with L/R pan (0.910, 0.470)
    voiced = y[np.abs(y) > 0.008]
    cur_rms = float(np.sqrt(np.mean(voiced ** 2))) if len(voiced) > 200 else 0.05
    y = y * ((10.0 ** (-20.8 / 20.0)) / max(cur_rms, 1e-4))
    stereo = np.column_stack([y * 0.910, y * 0.470])
    if normalize_to_minus16:
        stereo = stage8_loudnorm_two_pass(stereo, -16.0, -1.5)
    return stereo


def main() -> None:
    ap = argparse.ArgumentParser(description="Reusable documentary vocal mix chain (-16 LUFS).")
    ap.add_argument("input", help="Input audio file (WAV/FLAC/MP3)")
    ap.add_argument("output", help="Output audio file (.flac/.wav/.mp3)")
    ap.add_argument("--legacy-v07", action="store_true", help="Run legacy v07 chain instead of new chain")
    ap.add_argument("--breath-conditioner", choices=["auto", "on", "off"], default="auto")
    ap.add_argument("--target-lufs", type=float, default=-16.0)
    ap.add_argument("--report", help="Optional path to write JSON metrics report")
    args = ap.parse_args()

    mono = decode_mono_48k(args.input)
    if args.legacy_v07:
        stereo = process_legacy_v07_chain(mono, normalize_to_minus16=False)
        diag = {"chain": "legacy_v07"}
    else:
        cfg = ChainConfig(breath_conditioner=args.breath_conditioner, target_lufs=args.target_lufs)
        stereo, diag = process_vocal_chain(mono, cfg)

    sha = encode_audio(stereo, args.output)
    metrics = evaluate_stem(args.output)
    metrics["sha256"] = sha
    metrics["diagnostics"] = diag
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as f:
            json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
