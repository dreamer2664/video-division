#!/usr/bin/env python3
"""
Deterministic, offline-by-default 48 kHz stereo audio builder for MARK SEVEN (videos/team-b/grade-v08).

- When committed lossless stems exist in audio/*.flac (default), reproduces /tmp/grade_v08_build/master_audio_48k.wav
  100% offline with zero network/TTS calls using the exact two-pass EBU R128 loudnorm + alimiter filter stored in
  audio/gain_mapping.json.
- With --rebuild-stems (or on initial stem creation), builds timeline-aligned 48 kHz stereo 16-bit lossless FLAC stems
  from committed audio/tts_turns/*.mp3 + timing/tts_source_manifest.json + procedural canyon rain, spillway roar,
  <320 Hz bowed C-Phrygian sub-cello score, and spatialized relay/VHF/water foley.
"""

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR_S = 60.0
N_SAMPLES = int(SR * DUR_S)

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "audio")
TIMING_DIR = os.path.join(HERE, "timing")
TMP_DIR = "/tmp/grade_v08_build"
MASTER_WAV = os.path.join(TMP_DIR, "master_audio_48k.wav")

STEM_NAMES = [
    "voice_A_crest_48k.flac",
    "voice_B_levee_48k.flac",
    "dialogue_stem_48k.flac",
    "bed_ducked_48k.flac",
]


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def decode_mono_f64(path: str, sr: int = SR) -> np.ndarray:
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ar", str(sr), "-ac", "1", "-f", "f32le", "-"]
    )
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)


def decode_stereo_i16(path: str) -> np.ndarray:
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-ar", str(SR), "-ac", "2", "-f", "s16le", "-"]
    )
    return np.frombuffer(raw, dtype="<i2").reshape(-1, 2)


def encode_flac_i16(path: str, pcm_i16: np.ndarray) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_wav = os.path.join(TMP_DIR, "_" + os.path.basename(path) + ".wav")
    wavfile.write(tmp_wav, SR, pcm_i16.astype(np.int16))
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", tmp_wav, "-c:a", "flac", "-compression_level", "8", path],
        check=True,
    )
    os.remove(tmp_wav)


def rms_dbfs(arr_f64: np.ndarray) -> float:
    return float(20.0 * np.log10(np.sqrt(np.mean(arr_f64 ** 2)) + 1e-12))


def lux_acoustic_metrics(pcm_f64: np.ndarray) -> dict:
    mono = signal.resample_poly(pcm_f64.mean(axis=1), 1, 6)
    lp = signal.sosfilt(signal.butter(3, 450, fs=8000, output="sos"), mono)
    f0s = []
    for i in range(0, len(lp) - 480, 320):
        zz = lp[i:i + 480]
        orig = mono[i:i + 480]
        if np.sqrt(np.mean(orig ** 2)) < 0.01:
            continue
        zz = (zz - zz.mean()) * np.hanning(480)
        ac = signal.correlate(zz, zz, mode="full", method="fft")[479:]
        peaks, _ = signal.find_peaks(ac[23:115])
        if len(peaks):
            pk = int(peaks[np.argmax(ac[23:115][peaks])] + 23)
            if ac[pk] / max(ac[0], 1e-16) > 0.3:
                f0s.append(8000.0 / pk)
    active = np.max(np.abs(pcm_f64), axis=1) > (4.0 / 32768.0)
    m_act = pcm_f64[active].mean(axis=1)
    freqs, psd = signal.welch(m_act, fs=SR, nperseg=2048)
    psd_centroid = float(np.sum(freqs * psd) / (np.sum(psd) + 1e-18))
    lr_db = float(10.0 * np.log10((np.mean(pcm_f64[:, 0] ** 2) + 1e-18) / (np.mean(pcm_f64[:, 1] ** 2) + 1e-18)))
    return {
        "lux_autocorr_f0_median_hz": round(float(np.median(f0s)), 2) if f0s else 0.0,
        "voiced_windows": len(f0s),
        "welch_psd_centroid_hz": round(psd_centroid, 1),
        "L_minus_R_rms_db": round(lr_db, 2),
    }


def pan_gains(pan: float) -> tuple[float, float]:
    """Constant-power stereo pan in [-1.0, +1.0]."""
    theta = (pan + 1.0) * (math.pi / 4.0)
    return math.cos(theta), math.sin(theta)


def build_stems_from_manifest() -> None:
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    manifest = json.load(open(os.path.join(TIMING_DIR, "tts_source_manifest.json")))["turns"]
    voice_a = np.zeros((N_SAMPLES, 2), dtype=np.float64)
    voice_b = np.zeros((N_SAMPLES, 2), dtype=np.float64)

    sos_a_bp = signal.butter(4, [75.0, 8000.0], btype="bandpass", fs=SR, output="sos")
    b_a_pk, a_a_pk = signal.iirpeak(125.0, Q=1.4, fs=SR)

    # Keep 310 Hz lower cutoff + 2.25 kHz VHF presence peak so <450 Hz F0 (~200 Hz) AND crisp VHF centroid both shine!
    sos_b_bp = signal.butter(4, [310.0, 3600.0], btype="bandpass", fs=SR, output="sos")
    b_b_pk, a_b_pk = signal.iirpeak(2250.0, Q=1.3, fs=SR)

    ga_l, ga_r = pan_gains(-0.36)  # +5.42 dB Left
    gb_l, gb_r = pan_gains(+0.36)  # +5.42 dB Right

    foley_events = []

    for m in manifest:
        mp3_path = os.path.join(HERE, m["rel_mp3"])
        assert sha256_file(mp3_path) == m["sha256"], f"MP3 hash mismatch: {mp3_path}"
        raw_mono = decode_mono_f64(mp3_path)
        i0 = int(round(m["trim_in_s"] * SR))
        i1 = int(round(m["trim_out_s"] * SR))
        seg = raw_mono[i0:min(len(raw_mono), i1)].copy()

        fade_n = min(int(0.018 * SR), len(seg) // 4)
        seg[:fade_n] *= np.linspace(0.0, 1.0, fade_n)
        seg[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)

        if m["speaker"] == "A":
            y = signal.sosfilt(sos_a_bp, seg)
            y = y + 0.24 * signal.lfilter(b_a_pk, a_a_pk, y)
            y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.095
            dst = voice_a
            gl, gr = ga_l, ga_r
            foley_events.append(("relay_key", m["timeline_start_s"] - 0.11, -0.36))
        else:
            y = signal.sosfilt(sos_b_bp, seg)
            y = np.tanh((y + 0.95 * signal.lfilter(b_b_pk, a_b_pk, y)) * 2.1) / 2.1
            y = y / (np.sqrt(np.mean(y ** 2)) + 1e-9) * 0.095
            dst = voice_b
            gl, gr = gb_l, gb_r
            foley_events.append(("vhf_pip_in", m["timeline_start_s"] - 0.10, +0.36))
            foley_events.append(("vhf_pip_out", m["timeline_end_s"] + 0.05, +0.36))

        st_idx = int(round(m["timeline_start_s"] * SR))
        ed_idx = min(N_SAMPLES, st_idx + len(y))
        n_copy = ed_idx - st_idx
        dst[st_idx:ed_idx, 0] = y[:n_copy] * gl
        dst[st_idx:ed_idx, 1] = y[:n_copy] * gr

    # Quantize voices to int16 first so dialogue_stem == A + B bit-for-bit with zero overlap!
    va_i16 = np.clip(np.round(voice_a * 32767.0), -32000, 32000).astype(np.int16)
    vb_i16 = np.clip(np.round(voice_b * 32767.0), -32000, 32000).astype(np.int16)
    assert int(np.sum((np.max(np.abs(va_i16), axis=1) > 0) & (np.max(np.abs(vb_i16), axis=1) > 0))) == 0
    vd_i16 = (va_i16.astype(np.int32) + vb_i16.astype(np.int32)).astype(np.int16)

    # Procedural Valley Storm + Spillway Roar + <320 Hz Bowed Sub-Cello + Dry Foley
    rng = np.random.default_rng(20261108)
    t = np.arange(N_SAMPLES, dtype=np.float64) / SR

    # 1. Decorrelated stereo canyon rain & distant spillway roar (eases softly after 53s)
    w_l = rng.standard_normal(N_SAMPLES)
    w_r = rng.standard_normal(N_SAMPLES)
    sos_rain_hi = signal.butter(3, [1600.0, 7200.0], btype="bandpass", fs=SR, output="sos")
    sos_spill_lo = signal.butter(4, [42.0, 185.0], btype="bandpass", fs=SR, output="sos")
    rain_env = np.where(t < 53.0, 1.0, 1.0 - 0.38 * np.clip((t - 53.0) / 6.8, 0.0, 1.0))
    spill_env = 0.78 + 0.35 * np.exp(-((t - 18.5) / 9.5) ** 2) - 0.25 * np.clip((t - 45.0) / 14.0, 0.0, 1.0)

    rain_l = signal.sosfilt(sos_rain_hi, w_l) * 0.0082 * rain_env
    rain_r = signal.sosfilt(sos_rain_hi, w_r) * 0.0082 * rain_env
    roar_l = signal.sosfilt(sos_spill_lo, w_l) * 0.032 * spill_env
    roar_r = signal.sosfilt(sos_spill_lo, w_r) * 0.032 * spill_env

    # 2. <320 Hz bowed C-Phrygian sub-cello & low horn drone (C1 32.70, G1 49.00, C2 65.41, Db2->G2 resolution)
    vib = 0.0025 * np.sin(2.0 * np.pi * 4.3 * t)
    c1 = np.sin(2.0 * np.pi * 32.703 * t)
    g1 = np.sin(2.0 * np.pi * 48.999 * (t + vib))
    c2 = 0.65 * np.sin(2.0 * np.pi * 65.406 * (t - vib)) + 0.25 * np.sin(2.0 * np.pi * 130.81 * t)
    # Dark Phrygian Db2 (69.30 Hz) before 41.3s, resolving to open noble G2 (98.00 Hz) at Shot 08 Wall-Frame!
    resolve_w = np.clip((t - 41.0) / 2.5, 0.0, 1.0)
    color_note = (1.0 - resolve_w) * np.sin(2.0 * np.pi * 69.296 * t) + resolve_w * np.sin(2.0 * np.pi * 97.999 * t)
    swell = 0.80 + 0.35 * np.exp(-((t - 46.8) / 3.2) ** 2)  # Swell inside the 46.35-47.48s Wall-Frame breath!
    drone_raw = (0.44 * c1 + 0.32 * g1 + 0.26 * c2 + 0.18 * color_note) * swell
    sos_drone_lp = signal.butter(4, 310.0, btype="lowpass", fs=SR, output="sos")
    drone = signal.sosfilt(sos_drone_lp, drone_raw) * 0.036

    bed = np.zeros((N_SAMPLES, 2), dtype=np.float64)
    bed[:, 0] = rain_l + roar_l + drone * 1.03
    bed[:, 1] = rain_r + roar_r + drone * 0.97

    # 3. Spatialized dry foley (relay keys, VHF squelch pips, opening gorge thunder, town waterline lap)
    for kind, t0, pan in foley_events:
        if t0 < 0.02 or t0 >= DUR_S - 0.15:
            continue
        idx = int(round(t0 * SR))
        gl, gr = pan_gains(pan)
        if kind == "relay_key":
            ln = int(0.028 * SR)
            tt = np.arange(ln) / SR
            cl = np.exp(-tt / 0.005) * np.sin(2.0 * np.pi * 1420.0 * tt) * 0.028
            bed[idx:idx + ln, 0] += cl * gl
            bed[idx:idx + ln, 1] += cl * gr
        elif kind.startswith("vhf_pip"):
            ln = int(0.042 * SR)
            tt = np.arange(ln) / SR
            freq = 2480.0 if kind.endswith("in") else 1980.0
            pip = (np.sin(2.0 * np.pi * freq * tt) * np.exp(-tt / 0.014) + 0.35 * rng.standard_normal(ln) * np.exp(-tt / 0.010)) * 0.020
            bed[idx:idx + ln, 0] += pip * gl
            bed[idx:idx + ln, 1] += pip * gr

    # Opening canyon sub-thud at 0.14s & gentle water lap in the 46.45s Wall-Frame breath
    for t_hit, amp in ((0.14, 0.055), (46.52, 0.042)):
        idx = int(round(t_hit * SR))
        ln = int(0.85 * SR)
        tt = np.arange(ln) / SR
        sub = np.sin(2.0 * np.pi * (54.0 * np.exp(-tt * 1.8) + 28.0) * tt) * np.exp(-tt / 0.28) * amp
        bed[idx:idx + ln, 0] += sub
        bed[idx:idx + ln, 1] += sub

    # Smooth sidechain ducking from dialogue envelope (+10.5 dB active speech-over-bed dominance)
    dlg_f64 = vd_i16.astype(np.float64) / 32768.0
    dlg_pwr = np.mean(dlg_f64 ** 2, axis=1)
    win = int(0.085 * SR)
    env = np.sqrt(np.convolve(dlg_pwr, np.ones(win) / win, mode="same"))
    duck = 1.0 / (1.0 + (env / 0.018) ** 1.35)
    duck = np.clip(duck, 0.30, 1.0)
    duck_smooth = np.convolve(duck, np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    bed *= duck_smooth[:, None]

    # Calibrate bed gain so active-turn speech-over-bed RMS margin is ~ +10.55 dB
    tl = json.load(open(os.path.join(TIMING_DIR, "timeline_locked.json")))
    turn_mask = np.zeros(N_SAMPLES, dtype=bool)
    for tr in tl["turns"]:
        turn_mask[int(round(tr["start"] * SR)):int(round(tr["end"] * SR))] = True
    cur_dlg_rms = np.sqrt(np.mean(dlg_f64[turn_mask] ** 2))
    cur_bed_rms = np.sqrt(np.mean(bed[turn_mask] ** 2))
    target_bed_rms = cur_dlg_rms / (10.0 ** (10.55 / 20.0))
    bed *= (target_bed_rms / max(cur_bed_rms, 1e-12))

    # Gentle fade-in / fade-out on bed
    fi = int(0.22 * SR)
    fo = int(0.35 * SR)
    bed[:fi] *= np.linspace(0.15, 1.0, fi)[:, None]
    bed[-fo:] *= np.linspace(1.0, 0.08, fo)[:, None]

    bed_i16 = np.clip(np.round(bed * 32767.0), -32000, 32000).astype(np.int16)

    encode_flac_i16(os.path.join(AUDIO_DIR, "voice_A_crest_48k.flac"), va_i16)
    encode_flac_i16(os.path.join(AUDIO_DIR, "voice_B_levee_48k.flac"), vb_i16)
    encode_flac_i16(os.path.join(AUDIO_DIR, "dialogue_stem_48k.flac"), vd_i16)
    encode_flac_i16(os.path.join(AUDIO_DIR, "bed_ducked_48k.flac"), bed_i16)

    # Pre-sum raw mix and measure Pass 1 EBU R128 loudnorm stats
    pre_scale = 0.85
    raw_sum = np.clip(
        np.round((vd_i16.astype(np.float64) + bed_i16.astype(np.float64)) * pre_scale),
        -32767, 32767,
    ).astype(np.int16)
    raw_wav = os.path.join(TMP_DIR, "_raw_sum_48k.wav")
    wavfile.write(raw_wav, SR, raw_sum)

    p1 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", raw_wav, "-af", "loudnorm=I=-16.0:TP=-2.2:LRA=9.0:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    os.remove(raw_wav)
    m_json = re.search(r"\{\s*\"input_i\".*?\}", p1.stderr, re.DOTALL)
    stats = json.loads(m_json.group(0))

    ln_filter = (
        f"loudnorm=I=-16.0:TP=-2.2:LRA=9.0:"
        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true,"
        f"alimiter=limit=0.775:attack=3:release=40:level=false"
    )

    va_f = va_i16.astype(np.float64) / 32768.0
    vb_f = vb_i16.astype(np.float64) / 32768.0
    vd_f = vd_i16.astype(np.float64) / 32768.0
    bd_f = bed_i16.astype(np.float64) / 32768.0

    windows_10s = []
    for w_idx in range(6):
        s0, s1 = w_idx * 10 * SR, (w_idx + 1) * 10 * SR
        act_20ms = np.sqrt(np.mean(vd_f[s0:s1].reshape(-1, 960, 2) ** 2, axis=(1, 2))) > 0.002
        windows_10s.append({
            "window": f"{w_idx*10:02d}-{(w_idx+1)*10:02d}s",
            "speech_duty_pct": round(float(act_20ms.mean() * 100.0), 1),
            "voice_A_dbfs": round(rms_dbfs(va_f[s0:s1]), 2) if np.max(np.abs(va_i16[s0:s1])) > 0 else None,
            "voice_B_dbfs": round(rms_dbfs(vb_f[s0:s1]), 2) if np.max(np.abs(vb_i16[s0:s1])) > 0 else None,
            "dialogue_stem_dbfs": round(rms_dbfs(vd_f[s0:s1]), 2),
            "bed_ducked_dbfs": round(rms_dbfs(bd_f[s0:s1]), 2),
        })

    gmap = {
        "stems_sha256": {name: sha256_file(os.path.join(AUDIO_DIR, name)) for name in STEM_NAMES},
        "pre_scale": pre_scale,
        "loudnorm_pass1_stats": stats,
        "loudnorm_filter": ln_filter,
        "voice_separation": {
            "A_crest": lux_acoustic_metrics(va_f),
            "B_levee": lux_acoustic_metrics(vb_f),
            "overlap_samples_above_1lsb": 0,
        },
        "active_speech_duty_pct": round(float(turn_mask.mean() * 100.0), 2),
        "active_window_dialogue_rms_dbfs": round(rms_dbfs(vd_f[turn_mask]), 2),
        "active_window_bed_rms_dbfs": round(rms_dbfs(bd_f[turn_mask]), 2),
        "active_speech_to_bed_margin_db": round(rms_dbfs(vd_f[turn_mask]) - rms_dbfs(bd_f[turn_mask]), 2),
        "body_windows_10s": windows_10s,
    }
    json.dump(gmap, open(os.path.join(AUDIO_DIR, "gain_mapping.json"), "w"), indent=2)
    print("Built and verified 4 lossless 48 kHz FLAC stems in", AUDIO_DIR)


def reproduce_master_offline() -> str:
    os.makedirs(TMP_DIR, exist_ok=True)
    gmap_path = os.path.join(AUDIO_DIR, "gain_mapping.json")
    gmap = json.load(open(gmap_path))
    for name, want_sha in gmap["stems_sha256"].items():
        p = os.path.join(AUDIO_DIR, name)
        got = sha256_file(p)
        assert got == want_sha, f"SHA256 mismatch on {name}: {got} != {want_sha}"

    vd = decode_stereo_i16(os.path.join(AUDIO_DIR, "dialogue_stem_48k.flac"))
    bd = decode_stereo_i16(os.path.join(AUDIO_DIR, "bed_ducked_48k.flac"))
    raw_sum = np.clip(
        np.round((vd.astype(np.float64) + bd.astype(np.float64)) * float(gmap["pre_scale"])),
        -32767, 32767,
    ).astype(np.int16)

    raw_wav = os.path.join(TMP_DIR, "_offline_sum_48k.wav")
    wavfile.write(raw_wav, SR, raw_sum)
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", raw_wav,
            "-af", gmap["loudnorm_filter"],
            "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le",
            MASTER_WAV,
        ],
        check=True,
    )
    os.remove(raw_wav)
    m_sha = sha256_file(MASTER_WAV)
    if gmap.get("master_wav_sha256") and gmap["master_wav_sha256"] != m_sha:
        raise RuntimeError(f"Offline master WAV SHA256 drift: {m_sha} != {gmap['master_wav_sha256']}")
    if "master_wav_sha256" not in gmap:
        gmap["master_wav_sha256"] = m_sha
        json.dump(gmap, open(gmap_path, "w"), indent=2)
    return m_sha


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild-stems", action="store_true")
    args = ap.parse_args()

    have_all = all(os.path.exists(os.path.join(AUDIO_DIR, n)) for n in STEM_NAMES) and os.path.exists(os.path.join(AUDIO_DIR, "gain_mapping.json"))
    if args.rebuild_stems or not have_all:
        build_stems_from_manifest()
    else:
        print("Reproducing exact v08 master audio OFFLINE from committed lossless FLAC stems...")

    sha = reproduce_master_offline()
    print(f"Offline master_audio_48k.wav SHA256: {sha}")


if __name__ == "__main__":
    main()
