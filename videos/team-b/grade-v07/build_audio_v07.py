#!/usr/bin/env python3
"""
MARK SIX (videos/team-b/grade-v07) — Three-Voice 48 kHz Stereo Audio Engine.

Three acoustically, spectrally, and spatially distinct non-overlapping voices:
  - Voice A [REEL] : en-US-ChristopherNeural (-10%, -6Hz) | 75-8000 Hz magnetic oxide | Left (-38%, +5.74 dB L)
  - Voice C [HORN] : en-IE-ConnorNeural      (+2%,  +6Hz) | 850-6800 Hz VHF brass horn | Center (0%, 0.00 dB)
  - Voice B [LINE] : en-GB-SoniaNeural       (+5%,  +4Hz) | 340-3100 Hz copper handset | Right (+38%, +5.74 dB R)

Offline-by-default: consumes committed lossless FLAC stems in audio/ unless --rebuild-stems is passed.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DURATION_S = 60
N_SAMPLES = SR * DURATION_S


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def decode_audio_mono_48k(src_path: str, tmp_wav: str) -> np.ndarray:
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src_path, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", tmp_wav],
        check=True,
    )
    _, pcm = wavfile.read(tmp_wav)
    os.remove(tmp_wav)
    return pcm.astype(np.float32) / 32768.0


def decode_flac_stereo_f32(path: str, tmp_dir: str) -> np.ndarray:
    tw = os.path.join(tmp_dir, f"_dec_{os.path.basename(path)}.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", path, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", tw],
        check=True,
    )
    _, pcm = wavfile.read(tw)
    os.remove(tw)
    return pcm.astype(np.float32) / 32767.0


def write_flac_s16(path: str, arr_i16: np.ndarray, tmp_dir: str) -> str:
    tw = os.path.join(tmp_dir, f"_enc_{os.path.basename(path)}.wav")
    wavfile.write(tw, SR, arr_i16)
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", tw, "-c:a", "flac", "-compression_level", "12", path],
        check=True,
    )
    os.remove(tw)
    return sha256_file(path)


def estimate_f0_median(mono: np.ndarray) -> float:
    sos = signal.butter(2, [70.0 / (SR * 0.5), 420.0 / (SR * 0.5)], btype="bandpass", output="sos")
    bp = signal.sosfilt(sos, mono)
    win = int(0.040 * SR)
    step = int(0.015 * SR)
    lo, hi = int(SR / 340.0), int(SR / 72.0)
    f0s = []
    for i in range(0, len(bp) - win, step):
        seg = bp[i : i + win]
        if float(np.sqrt(np.mean(seg ** 2))) < 0.018:
            continue
        ac = np.correlate(seg, seg, mode="full")[win - 1 :]
        pk = lo + int(np.argmax(ac[lo:hi]))
        if ac[pk] > 0.35 * ac[0]:
            f0s.append(SR / float(pk))
    return float(np.median(f0s)) if f0s else 0.0


def spectral_centroid_hz(mono: np.ndarray) -> float:
    active = mono[np.abs(mono) > 0.004]
    if len(active) < 4096:
        return 0.0
    freqs, psd = signal.welch(active, SR, nperseg=4096)
    return float(np.sum(freqs * psd) / np.maximum(np.sum(psd), 1e-12))


def peaking_eq(x: np.ndarray, f0: float, q: float, gain_db: float) -> np.ndarray:
    a = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2.0 * q)
    b0 = 1.0 + alpha * a
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * a
    a0 = 1.0 + alpha / a
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / a
    b = np.array([b0 / a0, b1 / a0, b2 / a0], dtype=np.float64)
    aa = np.array([1.0, a1 / a0, a2 / a0], dtype=np.float64)
    return signal.lfilter(b, aa, x).astype(np.float32)


def process_voice_A_reel(x: np.ndarray) -> np.ndarray:
    # 75 Hz - 8000 Hz warm 1/4" ferric-oxide magnetic tape deck
    sos = signal.butter(3, [75.0 / (SR * 0.5), 8000.0 / (SR * 0.5)], btype="bandpass", output="sos")
    y = signal.sosfilt(sos, x).astype(np.float32)
    y = peaking_eq(y, 128.0, 1.1, +1.8)
    y = peaking_eq(y, 330.0, 1.5, -2.2)
    y = peaking_eq(y, 2900.0, 1.2, +2.4)
    y = np.tanh(y * 1.18).astype(np.float32) / 1.12
    return y


def process_voice_B_line(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    # 340 Hz - 3100 Hz narrow Bakelite copper telephone handset + carbon-capsule drive
    sos = signal.butter(4, [340.0 / (SR * 0.5), 3100.0 / (SR * 0.5)], btype="bandpass", output="sos")
    y = signal.sosfilt(sos, x).astype(np.float32)
    y = peaking_eq(y, 1450.0, 1.5, +3.6)
    y = np.tanh(y * 1.65).astype(np.float32) / 1.40
    y = signal.sosfilt(sos, y).astype(np.float32)
    wire_hiss = signal.sosfilt(sos, rng.normal(0.0, 0.0018, len(y)).astype(np.float32)).astype(np.float32)
    return y + wire_hiss


def process_voice_C_horn(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    # 850 Hz - 6800 Hz ceiling cast-brass marine VHF horn speaker
    sos = signal.butter(4, [850.0 / (SR * 0.5), 6800.0 / (SR * 0.5)], btype="bandpass", output="sos")
    y = signal.sosfilt(sos, x).astype(np.float32)
    y = peaking_eq(y, 3350.0, 1.4, +3.8)
    y = np.tanh(y * 1.32).astype(np.float32) / 1.22
    vhf_air = signal.sosfilt(sos, rng.normal(0.0, 0.0015, len(y)).astype(np.float32)).astype(np.float32)
    return y + vhf_air


def build_three_voice_stems(tts_manifest: list, repo_dir: str, tmp_dir: str):
    rng = np.random.default_rng(20260701)
    mono = {k: np.zeros(N_SAMPLES, dtype=np.float32) for k in ("A", "B", "C")}
    raw_f0 = {k: [] for k in ("A", "B", "C")}
    gate = {k: np.zeros(N_SAMPLES, dtype=np.float32) for k in ("A", "B", "C")}

    target_turn_rms = 10.0 ** (-20.8 / 20.0)

    for rec in tts_manifest:
        spk = rec["speaker"]
        mp3_path = os.path.join(repo_dir, rec["rel_mp3"])
        x_full = decode_audio_mono_48k(mp3_path, os.path.join(tmp_dir, f"_turn_{rec['turn']}.wav"))
        raw_f0[spk].append(x_full)

        i_in = max(0, int(round(rec["trim_in_s"] * SR)))
        i_out = min(len(x_full), int(round(rec["trim_out_s"] * SR)))
        seg = x_full[i_in:i_out].copy()

        # Smooth 18ms cosine fades on trimmed turn edges
        f_in = min(int(0.018 * SR), len(seg) // 4)
        f_out = min(int(0.028 * SR), len(seg) // 4)
        seg[:f_in] *= 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, f_in, dtype=np.float32)))
        seg[-f_out:] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, np.pi, f_out, dtype=np.float32)))

        if spk == "A":
            proc = process_voice_A_reel(seg)
        elif spk == "B":
            proc = process_voice_B_line(seg, rng)
        else:
            proc = process_voice_C_horn(seg, rng)

        proc[:f_in] *= np.linspace(0.0, 1.0, f_in, dtype=np.float32)
        proc[-f_out:] *= np.linspace(1.0, 0.0, f_out, dtype=np.float32)

        voiced = proc[np.abs(proc) > 0.008]
        cur_rms = float(np.sqrt(np.mean(voiced ** 2))) if len(voiced) > 200 else 0.05
        proc *= target_turn_rms / max(cur_rms, 1e-4)

        # Place on timeline so first word aligns with timeline_start_s
        lead = rec["first_word_offset_s"] - rec["trim_in_s"]
        dst0 = max(0, int(round((rec["timeline_start_s"] - lead) * SR)))
        dst1 = min(N_SAMPLES, dst0 + len(proc))
        n = dst1 - dst0

        # Strictly enforce zero sample overlap with other speakers
        mono[spk][dst0:dst1] = proc[:n]
        gate[spk][dst0:dst1] = 1.0

    # Verify zero overlap across all three speaker pairs
    ov_ab = int(np.sum((gate["A"] > 0.5) & (gate["B"] > 0.5)))
    ov_ac = int(np.sum((gate["A"] > 0.5) & (gate["C"] > 0.5)))
    ov_bc = int(np.sum((gate["B"] > 0.5) & (gate["C"] > 0.5)))
    assert ov_ab == 0 and ov_ac == 0 and ov_bc == 0, f"Overlap detected: AB={ov_ab}, AC={ov_ac}, BC={ov_bc}"

    # Equal-power-matched stereo panning across Left (-38%), Center (0%), Right (+38%)
    pan = {
        "A": (0.910, 0.470),  # +5.74 dB Left bias  (sqrt(0.91^2+0.47^2)=1.024)
        "C": (0.724, 0.724),  #  0.00 dB Dead Center (sqrt(0.724^2*2)=1.024)
        "B": (0.470, 0.910),  # +5.74 dB Right bias (sqrt(0.47^2+0.91^2)=1.024)
    }

    stereo = {}
    for k in ("A", "B", "C"):
        gL, gR = pan[k]
        stereo[k] = np.column_stack([mono[k] * gL, mono[k] * gR]).astype(np.float32)

    sep_stats = {
        "overlap_samples_AB": ov_ab,
        "overlap_samples_AC": ov_ac,
        "overlap_samples_BC": ov_bc,
        "overlap_seconds_total": 0.0,
        "voice_A_reel": {
            "engine": "en-US-ChristopherNeural",
            "rate": "-10%",
            "pitch": "-6Hz",
            "band_hz": "75-8000",
            "median_f0_hz": round(estimate_f0_median(np.concatenate(raw_f0["A"])), 1),
            "spectral_centroid_hz": round(spectral_centroid_hz(mono["A"]), 1),
            "pan_LR_db": round(float(20.0 * np.log10(pan["A"][0] / pan["A"][1])), 2),
        },
        "voice_C_horn": {
            "engine": "en-IE-ConnorNeural",
            "rate": "+2%",
            "pitch": "+6Hz",
            "band_hz": "850-6800",
            "median_f0_hz": round(estimate_f0_median(np.concatenate(raw_f0["C"])), 1),
            "spectral_centroid_hz": round(spectral_centroid_hz(mono["C"]), 1),
            "pan_LR_db": round(float(20.0 * np.log10(pan["C"][0] / pan["C"][1])), 2),
        },
        "voice_B_line": {
            "engine": "en-GB-SoniaNeural",
            "rate": "+5%",
            "pitch": "+4Hz",
            "band_hz": "340-3100",
            "median_f0_hz": round(estimate_f0_median(np.concatenate(raw_f0["B"])), 1),
            "spectral_centroid_hz": round(spectral_centroid_hz(mono["B"]), 1),
            "pan_LR_db": round(float(20.0 * np.log10(pan["B"][0] / pan["B"][1])), 2),
        },
    }
    active_gate = np.maximum(gate["A"], np.maximum(gate["B"], gate["C"]))
    return stereo["A"], stereo["B"], stereo["C"], active_gate, sep_stats


def build_score_and_foley(t: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(20260702)

    # 1. Stereo storm rain bed (swells on exterior river Shots 04, 05, 08 and surge breach Shot 10)
    wn_l = rng.normal(0.0, 1.0, N_SAMPLES).astype(np.float32)
    wn_r = rng.normal(0.0, 1.0, N_SAMPLES).astype(np.float32)
    sos_wash = signal.butter(2, [400.0 / (SR * 0.5), 1900.0 / (SR * 0.5)], btype="bandpass", output="sos")
    sos_pat = signal.butter(2, [4200.0 / (SR * 0.5), 8600.0 / (SR * 0.5)], btype="bandpass", output="sos")
    rain_l = signal.sosfilt(sos_wash, wn_l) * 0.048 + signal.sosfilt(sos_pat, wn_l) * 0.023
    rain_r = signal.sosfilt(sos_wash, wn_r) * 0.048 + signal.sosfilt(sos_pat, wn_r) * 0.023

    ext_env = (
        1.0
        + 0.30 * np.exp(-((t - 23.8) / 4.8) ** 2)
        + 0.26 * np.exp(-((t - 41.2) / 3.0) ** 2)
        + 0.36 * (1.0 / (1.0 + np.exp(-np.clip((t - 52.2) * 2.2, -30.0, 30.0))))
    )
    gust = 0.87 + 0.13 * np.sin(2.0 * np.pi * 0.09 * t + 0.4)
    rain_l *= (gust * ext_env).astype(np.float32)
    rain_r *= (gust * ext_env).astype(np.float32)

    # 2. Dark bowed C-minor / Phrygian sub-cello score (< 330 Hz -> zero masking of any of the 3 voices!)
    w1 = 1.0 / (1.0 + np.exp(np.clip((t - 24.0) * 2.4, -40.0, 40.0)))
    w2 = (1.0 / (1.0 + np.exp(np.clip(-(t - 24.0) * 2.4, -40.0, 40.0)))) * (1.0 / (1.0 + np.exp(np.clip((t - 43.8) * 3.5, -40.0, 40.0))))
    w3 = 1.0 / (1.0 + np.exp(np.clip(-(t - 43.8) * 3.5, -40.0, 40.0)))
    vib = 0.0020 * np.sin(2.0 * np.pi * 4.3 * t)

    def bowed(freq: float, det: float = 0.0) -> np.ndarray:
        f = freq * (1.0 + det)
        ph = 2.0 * np.pi * f * (t + vib / max(f, 30.0))
        return (0.68 * np.sin(ph) + 0.23 * np.sin(2.0 * ph + 0.35) + 0.09 * np.sin(3.0 * ph + 0.7)).astype(np.float32)

    # C1 (32.70Hz) + G1 (49.00Hz) + C2 (65.41Hz) -> F1/Ab1 -> C1 + Db2 (69.30Hz Phrygian tension)
    s1_l = 0.46 * bowed(32.703) + 0.38 * bowed(65.406, -0.0015) + 0.24 * bowed(97.999, +0.001)
    s1_r = 0.46 * bowed(32.703) + 0.38 * bowed(65.406, +0.0015) + 0.24 * bowed(97.999, -0.001)

    s2_l = 0.48 * bowed(43.654) + 0.36 * bowed(87.307, -0.0018) + 0.22 * bowed(130.813)
    s2_r = 0.48 * bowed(43.654) + 0.36 * bowed(87.307, +0.0018) + 0.22 * bowed(130.813)

    s3_l = 0.56 * bowed(32.703) + 0.42 * bowed(65.406, -0.002) + 0.31 * bowed(69.296, +0.001) + 0.20 * bowed(97.999)
    s3_r = 0.56 * bowed(32.703) + 0.42 * bowed(65.406, +0.002) + 0.31 * bowed(69.296, -0.001) + 0.20 * bowed(97.999)

    breath = 0.84 + 0.16 * np.sin(2.0 * np.pi * 0.11 * t - 0.3)
    sos_lp = signal.butter(3, 330.0 / (SR * 0.5), btype="lowpass", output="sos")
    sc_l = signal.sosfilt(sos_lp, (w1 * s1_l + w2 * s2_l + w3 * s3_l) * breath * 0.118).astype(np.float32)
    sc_r = signal.sosfilt(sos_lp, (w1 * s1_r + w2 * s2_r + w3 * s3_r) * breath * 0.118).astype(np.float32)

    # 3. Spatialized Transducer & Structural Foley (panned to match Left Reel / Center Horn / Right Line)
    fl_l = np.zeros(N_SAMPLES, dtype=np.float32)
    fl_r = np.zeros(N_SAMPLES, dtype=np.float32)

    def add_click(t0: float, freq: float, decay: float, amp: float, pan_lr: tuple):
        i0 = int(t0 * SR)
        n = min(int(0.16 * SR), N_SAMPLES - i0)
        if n <= 0:
            return
        lt = np.arange(n, dtype=np.float32) / SR
        c = (np.sin(2 * np.pi * freq * lt) + 0.42 * np.sin(2 * np.pi * freq * 2.14 * lt)) * np.exp(-lt * decay) * amp
        fl_l[i0 : i0 + n] += c * pan_lr[0]
        fl_r[i0 : i0 + n] += c * pan_lr[1]

    def add_vhf_squelch(t0: float, amp: float = 0.046):
        i0 = int(t0 * SR)
        n = min(int(0.085 * SR), N_SAMPLES - i0)
        if n <= 0:
            return
        lt = np.arange(n, dtype=np.float32) / SR
        burst = rng.normal(0.0, 1.0, n).astype(np.float32)
        sos_sq = signal.butter(3, [1200.0 / (SR * 0.5), 4800.0 / (SR * 0.5)], btype="bandpass", output="sos")
        pip = 0.45 * np.sin(2 * np.pi * 2150.0 * lt) + 0.55 * signal.sosfilt(sos_sq, burst).astype(np.float32)
        env = np.exp(-lt * 36.0)
        fl_l[i0 : i0 + n] += pip * env * amp * 0.72
        fl_r[i0 : i0 + n] += pip * env * amp * 0.72

    def add_thump(t0: float, f0: float, f1: float, dur_s: float, amp: float):
        i0 = int(t0 * SR)
        n = min(int(dur_s * SR), N_SAMPLES - i0)
        if n <= 0:
            return
        lt = np.arange(n, dtype=np.float32) / SR
        ph = 2.0 * np.pi * np.cumsum(f0 + (f1 - f0) * (lt / dur_s)) / SR
        th = np.sin(ph) * np.exp(-lt * (4.0 / dur_s)) * (1.0 - np.exp(-lt * 90.0)) * amp
        fl_l[i0 : i0 + n] += th
        fl_r[i0 : i0 + n] += th

    # Left Reel solenoid engage (0.22s), splice tick (29.62s), and end-of-tape stop click (59.05s)
    add_click(0.22, 860.0, 52.0, 0.065, (0.92, 0.45))
    add_click(0.26, 1340.0, 68.0, 0.050, (0.92, 0.45))
    add_click(29.62, 980.0, 60.0, 0.052, (0.92, 0.45))
    add_click(59.05, 920.0, 50.0, 0.072, (0.92, 0.45))
    add_click(59.11, 540.0, 44.0, 0.060, (0.92, 0.45))

    # Right Bakelite handset line clicks (7.02s, 18.48s, 34.56s, and disconnect at 55.66s)
    add_click(7.02, 1480.0, 64.0, 0.058, (0.45, 0.92))
    add_click(18.48, 1390.0, 66.0, 0.045, (0.45, 0.92))
    add_click(55.66, 1680.0, 70.0, 0.068, (0.45, 0.92))

    # Center ceiling VHF horn squelch open/close pips
    for sq_t in (12.33, 18.14, 24.16, 38.36, 50.28):
        add_vhf_squelch(sq_t, amp=0.044)

    # Pre-twist submarine glass groan + double pulse in the 1.20s pause (43.57s -> 44.77s)
    add_thump(43.82, 68.0, 35.0, 0.34, 0.14)
    add_thump(44.24, 60.0, 31.0, 0.44, 0.18)

    # Window shear-bolt detonation at 50.15s & glass fracture + floor surge 52.1s - 59.9s
    add_thump(50.15, 105.0, 34.0, 0.55, 0.19)
    add_click(50.16, 2240.0, 58.0, 0.065, (0.72, 0.72))
    add_click(52.38, 2860.0, 48.0, 0.058, (0.72, 0.72))

    surge_mask = np.clip((t - 51.8) / 1.4, 0.0, 1.0) * np.clip((59.96 - t) / 0.65, 0.0, 1.0)
    sos_water = signal.butter(2, [75.0 / (SR * 0.5), 320.0 / (SR * 0.5)], btype="bandpass", output="sos")
    fl_l += signal.sosfilt(sos_water, wn_l).astype(np.float32) * surge_mask * 0.082
    fl_r += signal.sosfilt(sos_water, wn_r).astype(np.float32) * surge_mask * 0.082

    bed_l = rain_l + sc_l + fl_l
    bed_r = rain_r + sc_r + fl_r
    fi, fo = int(0.25 * SR), int(0.35 * SR)
    bed_l[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    bed_r[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    bed_l[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    bed_r[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    return np.column_stack([bed_l, bed_r]).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MARK SIX (v07) three-voice 48 kHz master audio.")
    parser.add_argument(
        "--rebuild-stems",
        action="store_true",
        help="Rebuild the five lossless FLAC stems from committed audio/tts_turns/*.mp3 sources.",
    )
    args = parser.parse_args()

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(repo_dir, "audio")
    timing_dir = os.path.join(repo_dir, "timing")
    os.makedirs(audio_dir, exist_ok=True)

    build_dir = "/tmp/grade_v07_build"
    os.makedirs(build_dir, exist_ok=True)

    va_flac = os.path.join(audio_dir, "voice_A_reel_48k.flac")
    vb_flac = os.path.join(audio_dir, "voice_B_line_48k.flac")
    vc_flac = os.path.join(audio_dir, "voice_C_horn_48k.flac")
    vd_flac = os.path.join(audio_dir, "dialogue_stem_48k.flac")
    bed_flac = os.path.join(audio_dir, "bed_ducked_48k.flac")
    gmap_json = os.path.join(audio_dir, "gain_mapping.json")

    if not args.rebuild_stems and all(os.path.exists(p) for p in (va_flac, vb_flac, vc_flac, vd_flac, bed_flac, gmap_json)):
        print("Reproducing exact v07 master audio OFFLINE from committed lossless FLAC stems...")
        gmap = json.load(open(gmap_json))
        a_f = decode_flac_stereo_f32(va_flac, build_dir)
        b_f = decode_flac_stereo_f32(vb_flac, build_dir)
        c_f = decode_flac_stereo_f32(vc_flac, build_dir)
        bed_f = decode_flac_stereo_f32(bed_flac, build_dir)
        raw_mix = (a_f + b_f + c_f + bed_f) * float(gmap.get("pre_scale", 1.0))
        pre_wav = os.path.join(build_dir, "mix_pre_loudnorm_48k.wav")
        master_wav = os.path.join(build_dir, "master_audio_48k.wav")
        wavfile.write(pre_wav, SR, np.clip(np.round(raw_mix * 32767.0), -32768, 32767).astype(np.int16))
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", pre_wav, "-af", gmap["loudnorm_filter"], "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", master_wav],
            check=True,
        )
        print(f"Offline master_audio_48k.wav SHA256: {sha256_file(master_wav)}")
        return

    tts_manifest = json.load(open(os.path.join(timing_dir, "tts_source_manifest.json")))["turns"]
    st_A, st_B, st_C, active_gate, sep_stats = build_three_voice_stems(tts_manifest, repo_dir, build_dir)

    a_i16 = np.clip(np.round(st_A * 32767.0), -32768, 32767).astype(np.int16)
    b_i16 = np.clip(np.round(st_B * 32767.0), -32768, 32767).astype(np.int16)
    c_i16 = np.clip(np.round(st_C * 32767.0), -32768, 32767).astype(np.int16)
    d_i16 = np.clip(a_i16.astype(np.int32) + b_i16.astype(np.int32) + c_i16.astype(np.int32), -32768, 32767).astype(np.int16)

    d_f = d_i16.astype(np.float32) / 32767.0
    t = np.arange(N_SAMPLES, dtype=np.float32) / SR
    bed_stereo = build_score_and_foley(t)

    sos_duck = signal.butter(1, 3.2 / (SR * 0.5), btype="lowpass", output="sos")
    duck_curve = np.clip(signal.sosfilt(sos_duck, active_gate).astype(np.float32), 0.0, 1.0)
    act = active_gate > 0.5
    d_rms = float(np.sqrt(np.mean(d_f[act] ** 2)))
    b_rms = float(np.sqrt(np.mean(bed_stereo[act] ** 2)))
    base_scale = (d_rms * (10.0 ** (-10.5 / 20.0))) / max(b_rms, 1e-6)
    bed_ducked = bed_stereo * (base_scale * (1.65 - 0.65 * duck_curve)[:, None])
    bed_i16 = np.clip(np.round(bed_ducked * 32767.0), -32768, 32767).astype(np.int16)
    bed_f = bed_i16.astype(np.float32) / 32767.0

    flacs = {
        "voice_A_reel_48k.flac": write_flac_s16(va_flac, a_i16, build_dir),
        "voice_B_line_48k.flac": write_flac_s16(vb_flac, b_i16, build_dir),
        "voice_C_horn_48k.flac": write_flac_s16(vc_flac, c_i16, build_dir),
        "dialogue_stem_48k.flac": write_flac_s16(vd_flac, d_i16, build_dir),
        "bed_ducked_48k.flac": write_flac_s16(bed_flac, bed_i16, build_dir),
    }

    a_f = a_i16.astype(np.float32) / 32767.0
    b_f = b_i16.astype(np.float32) / 32767.0
    c_f = c_i16.astype(np.float32) / 32767.0
    raw_mix = a_f + b_f + c_f + bed_f
    pk = float(np.max(np.abs(raw_mix)))
    pre_scale = 1.0
    if pk > 0.89:
        pre_scale = 0.89 / pk
        raw_mix = raw_mix * pre_scale

    pre_wav = os.path.join(build_dir, "mix_pre_loudnorm_48k.wav")
    master_wav = os.path.join(build_dir, "master_audio_48k.wav")
    wavfile.write(pre_wav, SR, np.clip(np.round(raw_mix * 32767.0), -32768, 32767).astype(np.int16))

    p1 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", pre_wav, "-af", "loudnorm=I=-16.0:TP=-2.2:LRA=9.0:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    ln_stats = json.loads(re.search(r"\{\s*\"input_i\".*?\}", p1.stderr, re.DOTALL).group(0))
    ln_af = (
        f"loudnorm=I=-16.0:TP=-2.2:LRA=9.0:"
        f"measured_I={ln_stats['input_i']}:measured_LRA={ln_stats['input_lra']}:"
        f"measured_TP={ln_stats['input_tp']}:measured_thresh={ln_stats['input_thresh']}:"
        f"offset={ln_stats['target_offset']}:linear=true:print_format=summary,"
        f"alimiter=limit=0.775:attack=3:release=40:level=false,aresample=48000"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", pre_wav, "-af", ln_af, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", master_wav],
        check=True,
    )

    act_d_db = float(20.0 * np.log10(np.sqrt(np.mean(d_f[act] ** 2))))
    act_b_db = float(20.0 * np.log10(np.sqrt(np.mean(bed_f[act] ** 2))))

    windows = []
    for w0 in range(0, 60, 10):
        i0, i1 = w0 * SR, (w0 + 10) * SR
        windows.append({
            "window_s": f"{w0:02d}-{w0+10:02d}s",
            "speech_duty_pct": round(float(np.mean(active_gate[i0:i1] > 0.5) * 100.0), 1),
            "voice_A_rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(a_f[i0:i1] ** 2)) + 1e-12)), 2),
            "voice_B_rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(b_f[i0:i1] ** 2)) + 1e-12)), 2),
            "voice_C_rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(c_f[i0:i1] ** 2)) + 1e-12)), 2),
            "dialogue_stem_rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(d_f[i0:i1] ** 2)) + 1e-12)), 2),
            "bed_ducked_rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(bed_f[i0:i1] ** 2)) + 1e-12)), 2),
        })

    gmap = {
        "stems_sha256": flacs,
        "master_wav_sha256": sha256_file(master_wav),
        "pre_scale": round(pre_scale, 8),
        "loudnorm_pass1_stats": ln_stats,
        "loudnorm_filter": ln_af,
        "voice_separation": sep_stats,
        "active_speech_duty_pct": round(float(np.mean(act) * 100.0), 2),
        "active_window_dialogue_rms_dbfs": round(act_d_db, 2),
        "active_window_bed_rms_dbfs": round(act_b_db, 2),
        "active_speech_to_bed_margin_db": round(act_d_db - act_b_db, 2),
        "body_windows_10s": windows,
    }
    json.dump(gmap, open(gmap_json, "w"), indent=2)
    print(json.dumps(gmap, indent=2))


if __name__ == "__main__":
    main()
