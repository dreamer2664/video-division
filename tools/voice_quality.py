#!/usr/bin/env python3
"""File-in, numbers-out prosody analyser. No microphone/audio device is opened.

Usage:
  python3 tools/voice_quality.py narration.flac
  python3 tools/voice_quality.py take_a.wav take_b.mp3 --json
  python3 tools/voice_quality.py narration.flac --track-out f0.csv

Requires FFmpeg on PATH and NumPy. F0 is a simple framewise autocorrelation tracker;
syllable nuclei are estimated from peaks in the smoothed RMS envelope. The monotone
score is a transparent heuristic, not a learned or validated human-naturalness model.
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys
from pathlib import Path
import numpy as np

ANALYSIS_SR = 22050
FRAME_MS = 40
HOP_MS = 10
F0_MIN = 65.0
F0_MAX = 500.0
VAD_GAP_MIN_S = 0.12


def decode_audio(path: str | Path, sr: int = ANALYSIS_SR) -> np.ndarray:
    """Decode any FFmpeg-supported audio container to mono float32; no audio device."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn",
           "-ac", "1", "-ar", str(sr), "-f", "f32le", "pipe:1"]
    try:
        p = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as e:
        raise RuntimeError("FFmpeg is required for decoding; install it and put it on PATH") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr.decode("utf-8", "replace")[-1500:]) from e
    x = np.frombuffer(p.stdout, dtype="<f4").astype(np.float64)
    if x.size < sr // 4:
        raise ValueError(f"Audio is empty or shorter than 250 ms: {path}")
    return x


def frame_signal(x: np.ndarray, frame_len: int, hop: int) -> np.ndarray:
    if len(x) < frame_len:
        x = np.pad(x, (0, frame_len - len(x)))
    count = 1 + (len(x) - frame_len) // hop
    shape = (count, frame_len)
    strides = (x.strides[0] * hop, x.strides[0])
    return np.lib.stride_tricks.as_strided(x, shape=shape, strides=strides).copy()


def run_intervals(mask: np.ndarray) -> list[tuple[int, int]]:
    """Half-open runs of True sample/frame indices."""
    padded = np.r_[False, mask.astype(bool), False].astype(np.int8)
    edges = np.diff(padded)
    starts = np.flatnonzero(edges == 1)
    ends = np.flatnonzero(edges == -1)
    return list(zip(starts.tolist(), ends.tolist()))


def detect_activity(rms_db: np.ndarray) -> tuple[np.ndarray, float]:
    """Adaptive energy gate. This is not a neural VAD; background beds can fool it."""
    peak = float(np.max(rms_db))
    floor = float(np.percentile(rms_db, 20))
    threshold = max(-52.0, floor + 9.0, peak - 38.0)
    return rms_db > threshold, threshold


def autocorr_f0(frame: np.ndarray, sr: int = ANALYSIS_SR,
                f0_min: float = F0_MIN, f0_max: float = F0_MAX) -> tuple[float, float]:
    """Return (F0 Hz, normalized autocorrelation peak). 0 Hz means unvoiced/uncertain."""
    z = np.asarray(frame, dtype=np.float64)
    z = z - np.mean(z)
    if np.sqrt(np.mean(z * z)) < 1e-5:
        return 0.0, 0.0
    z = z * np.hanning(len(z))
    nfft = 1 << int(math.ceil(math.log2(2 * len(z))))
    spec = np.fft.rfft(z, n=nfft)
    ac = np.fft.irfft(spec * np.conjugate(spec), n=nfft)[:len(z)]
    if ac[0] <= 1e-12:
        return 0.0, 0.0
    ac /= ac[0]
    lo = max(1, int(sr / f0_max))
    hi = min(len(ac) - 2, int(sr / f0_min))
    if hi <= lo:
        return 0.0, 0.0
    candidates = np.arange(lo, hi + 1)
    local = candidates[(ac[candidates] >= ac[candidates - 1]) & (ac[candidates] >= ac[candidates + 1])]
    if local.size == 0:
        return 0.0, 0.0
    # First sufficiently strong local maximum suppresses common octave/subharmonic mistakes.
    peak = int(local[np.argmax(ac[local])])
    strength = float(ac[peak])
    if strength < 0.28:
        return 0.0, strength
    # Parabolic interpolation around the discrete ACF peak.
    a, b, c = ac[peak - 1], ac[peak], ac[peak + 1]
    denom = a - 2.0 * b + c
    offset = 0.5 * (a - c) / denom if abs(denom) > 1e-12 else 0.0
    lag = peak + float(np.clip(offset, -0.5, 0.5))
    return float(sr / lag), strength


def smooth(x: np.ndarray, width: int) -> np.ndarray:
    if width <= 1:
        return x.copy()
    kernel = np.ones(width, dtype=np.float64) / width
    return np.convolve(x, kernel, mode="same")


def syllable_peaks(rms_db: np.ndarray, active: np.ndarray, hop_s: float) -> list[int]:
    """Crude syllabic-nucleus estimate from amplitude-envelope peaks."""
    env = smooth(rms_db, max(3, round(0.07 / hop_s)))
    peaks = []
    min_dist = max(1, round(0.12 / hop_s))
    for i in range(1, len(env) - 1):
        if active[i] and env[i] >= env[i-1] and env[i] > env[i+1]:
            lo, hi = max(0, i-min_dist), min(len(env), i+min_dist+1)
            if env[i] - np.min(env[lo:hi]) < 1.7:
                continue
            if peaks and i - peaks[-1] < min_dist:
                if env[i] > env[peaks[-1]]:
                    peaks[-1] = i
            else:
                peaks.append(i)
    return peaks


def feature_report(path: str | Path, track_out: str | Path | None = None) -> dict:
    x = decode_audio(path)
    sr = ANALYSIS_SR
    frame_len = round(sr * FRAME_MS / 1000)
    hop = round(sr * HOP_MS / 1000)
    hop_s = hop / sr
    frames = frame_signal(x, frame_len, hop)
    rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-16)
    rms_db = 20 * np.log10(rms + 1e-12)
    active, gate_db = detect_activity(rms_db)
    active_intervals = run_intervals(active)
    active_seconds = float(np.sum(active) * hop_s)
    if active_intervals:
        speech_span = (active_intervals[-1][1] - active_intervals[0][0]) * hop_s
    else:
        speech_span = 0.0
    gaps = [((b0-a1) * hop_s) for (_, a1), (b0, _) in zip(active_intervals, active_intervals[1:])
            if (b0-a1) * hop_s >= VAD_GAP_MIN_S]

    window = np.hanning(frame_len)
    f0 = np.zeros(len(frames), dtype=np.float64)
    periodicity = np.zeros(len(frames), dtype=np.float64)
    centroid = np.zeros(len(frames), dtype=np.float64)
    rolloff = np.zeros(len(frames), dtype=np.float64)
    nfft = 1 << int(math.ceil(math.log2(frame_len)))
    freq = np.fft.rfftfreq(nfft, 1/sr)
    for i, frame in enumerate(frames):
        if active[i]:
            f0[i], periodicity[i] = autocorr_f0(frame, sr)
        mag = np.abs(np.fft.rfft(frame * window, n=nfft))
        mass = float(np.sum(mag)) + 1e-12
        centroid[i] = float(np.sum(freq * mag) / mass)
        csum = np.cumsum(mag)
        rolloff[i] = float(freq[min(np.searchsorted(csum, 0.85 * mass), len(freq)-1)])

    voiced = active & (f0 > 0)
    # Remove isolated pitch outliers locally, then differentiate only within continuous voiced runs.
    f0_smooth = f0.copy()
    for start, end in run_intervals(voiced):
        segment = f0[start:end]
        if len(segment) >= 3:
            padded = np.pad(segment, (2, 2), mode="edge")
            f0_smooth[start:end] = np.array([np.median(padded[j:j+5]) for j in range(len(segment))])
    f0_values = f0_smooth[voiced]
    semi_track = 12.0 * np.log2(f0_values / np.median(f0_values)) if len(f0_values) else np.array([])
    f0_derivatives, semi_derivatives = [], []
    for start, end in run_intervals(voiced):
        if end - start >= 2:
            hz_delta = np.diff(f0_smooth[start:end])
            semi_delta = np.diff(12.0 * np.log2(f0_smooth[start:end]))
            # Discard residual octave/halving errors (>3 semitones per 10-ms hop).
            keep = np.abs(semi_delta) <= 3.0
            f0_derivatives.extend((hz_delta[keep] / hop_s).tolist())
            semi_derivatives.extend((semi_delta[keep] / hop_s).tolist())
    f0_derivative_sd = float(np.std(f0_derivatives)) if f0_derivatives else 0.0
    semi_derivative_sd = float(np.std(semi_derivatives)) if semi_derivatives else 0.0
    pitch_sd_semitones = float(np.std(semi_track)) if len(semi_track) else 0.0
    energy_sd_db = float(np.std(rms_db[active])) if np.any(active) else 0.0
    centroid_sd = float(np.std(centroid[active])) if np.any(active) else 0.0
    rolloff_sd = float(np.std(rolloff[active])) if np.any(active) else 0.0
    syllables = syllable_peaks(rms_db, active, hop_s)
    syllable_rate = len(syllables) / active_seconds if active_seconds else 0.0
    # Approximate lexical rate only: English averages around 1.5–1.7 syllables per word.
    words_per_min = syllable_rate * 60 / 1.55
    hnr_values = 10 * np.log10(np.maximum(periodicity[voiced], 1e-6) /
                               np.maximum(1 - periodicity[voiced], 1e-6)) if np.any(voiced) else np.array([])
    # Transparent 0–100 flatness heuristic; high = less prosodic movement.
    flatness_terms = [
        (0.40, np.clip(pitch_sd_semitones / 6.0, 0, 1)),
        (0.25, np.clip(semi_derivative_sd / 20.0, 0, 1)),
        (0.18, np.clip(energy_sd_db / 15.0, 0, 1)),
        (0.085, np.clip(centroid_sd / 2500.0, 0, 1)),
        (0.085, np.clip(rolloff_sd / 4000.0, 0, 1)),
    ]
    monotone_score = 100 * (1 - sum(w * float(v) for w, v in flatness_terms))
    voiced_ratio = float(np.mean(voiced)) if len(voiced) else 0.0
    report = {
        "file": str(path), "duration_s": len(x) / sr, "analysis_sample_rate_hz": sr,
        "speech_gate_dbfs": gate_db, "speech_active_s_est": active_seconds,
        "speech_span_s_est": speech_span,
        "f0": {"method": "windowed autocorrelation, 40 ms frames / 10 ms hop; 65–500 Hz",
               "voiced_frames": int(np.sum(voiced)), "voiced_ratio_of_frames": voiced_ratio,
               "mean_hz": float(np.mean(f0_values)) if len(f0_values) else None,
               "std_hz": float(np.std(f0_values)) if len(f0_values) else None,
               "std_derivative_hz_per_s": f0_derivative_sd,
               "std_derivative_semitones_per_s": semi_derivative_sd,
               "std_semitones": pitch_sd_semitones},
        "hnr_autocorrelation_proxy_db_mean": float(np.mean(hnr_values)) if len(hnr_values) else None,
        "speech_rate_est": {"syllabic_nuclei": len(syllables), "syllables_per_s_active": syllable_rate,
                             "words_per_min_approx": words_per_min, "assumed_syllables_per_word": 1.55},
        "pauses": {"count_ge_120ms": len(gaps), "gap_seconds": gaps,
                   "mean_s": float(np.mean(gaps)) if gaps else 0.0,
                   "median_s": float(np.median(gaps)) if gaps else 0.0,
                   "p90_s": float(np.percentile(gaps, 90)) if gaps else 0.0,
                   "max_s": float(np.max(gaps)) if gaps else 0.0},
        "energy": {"rms_dbfs_active_mean": float(np.mean(rms_db[active])) if np.any(active) else None,
                   "rms_db_std_active": energy_sd_db},
        "spectrum": {"centroid_hz_active_mean": float(np.mean(centroid[active])) if np.any(active) else None,
                     "centroid_hz_active_std": centroid_sd,
                     "rolloff85_hz_active_mean": float(np.mean(rolloff[active])) if np.any(active) else None,
                     "rolloff85_hz_active_std": rolloff_sd},
        "monotone_score_0_to_100": float(monotone_score),
        "score_definition": "weighted inverse of F0 spread, F0-slope spread, active RMS-dB spread, centroid spread, and rolloff spread; higher is flatter; heuristic, not human naturalness.",
        "limits": ["No ASR or transcript; syllables are RMS-envelope peak estimates and word rate assumes 1.55 syllables/word.",
                   "Energy gate can mistake music/noise for speech or miss quiet speech.",
                   "Autocorrelation can octave-error, especially on creaky, breathy, noisy, or polyphonic audio.",
                   "HNR is an autocorrelation periodicity proxy, not Praat's calibrated HNR.",
                   "Prosody metrics measure acoustic variation, not beauty, acting, intelligibility, or listener preference."],
    }
    if track_out:
        with Path(track_out).open("w", encoding="utf-8") as f:
            f.write("time_s,f0_hz,voiced,energy_dbfs,centroid_hz,rolloff85_hz\n")
            for i in range(len(frames)):
                f.write(f"{i*hop_s:.4f},{f0[i]:.3f},{int(voiced[i])},{rms_db[i]:.3f},{centroid[i]:.3f},{rolloff[i]:.3f}\n")
    return report


def verdict(a: dict, b: dict) -> str:
    sa, sb = a["monotone_score_0_to_100"], b["monotone_score_0_to_100"]
    diff = abs(sa - sb)
    if diff < 0.5:
        return "VERDICT (prosody proxy): no meaningful separation on this heuristic (<0.5 monotone-score point); this does not mean listeners would rate them equally."
    varied, flat = (a, b) if sa < sb else (b, a)
    return (f"VERDICT (prosody proxy): {Path(varied['file']).name} has more acoustic prosodic motion than "
            f"{Path(flat['file']).name} by {diff:.1f} monotone-score points "
            f"(scores {sa:.1f} vs {sb:.1f}; lower = more motion). This is not a subjective human-naturalness verdict.")


def print_human(r: dict) -> None:
    f = r["f0"]; p = r["pauses"]; e = r["energy"]; s = r["spectrum"]
    print(f"FILE: {r['file']} ({r['duration_s']:.2f}s; no audio device used)")
    print(f"  F0 autocorrelation: mean {f['mean_hz'] if f['mean_hz'] is not None else float('nan'):.1f} Hz, "
          f"SD {f['std_hz'] if f['std_hz'] is not None else float('nan'):.1f} Hz, "
          f"derivative SD {f['std_derivative_hz_per_s']:.1f} Hz/s ({f['std_derivative_semitones_per_s']:.2f} st/s)")
    print(f"  Rate est: {r['speech_rate_est']['syllables_per_s_active']:.2f} syll/s; "
          f"{r['speech_rate_est']['words_per_min_approx']:.1f} words/min approx; "
          f"{r['speech_rate_est']['syllabic_nuclei']} nuclei")
    print(f"  Pauses >=120ms: {p['count_ge_120ms']} (median {p['median_s']:.2f}s, p90 {p['p90_s']:.2f}s, max {p['max_s']:.2f}s)")
    print(f"  Energy SD {e['rms_db_std_active']:.2f} dB; centroid {s['centroid_hz_active_mean'] or 0:.0f}±{s['centroid_hz_active_std']:.0f} Hz; "
          f"rolloff85 {s['rolloff85_hz_active_mean'] or 0:.0f}±{s['rolloff85_hz_active_std']:.0f} Hz")
    print(f"  HNR proxy {r['hnr_autocorrelation_proxy_db_mean'] if r['hnr_autocorrelation_proxy_db_mean'] is not None else float('nan'):.1f} dB; "
          f"monotone score {r['monotone_score_0_to_100']:.1f}/100 (higher = flatter)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", help="one audio file, or two files for an A/B prosody proxy")
    ap.add_argument("--json", action="store_true", help="print full JSON report")
    ap.add_argument("--track-out", help="write per-frame F0/energy/spectral CSV (one input only)")
    args = ap.parse_args()
    if len(args.files) not in (1, 2):
        ap.error("pass one file or exactly two files for an A/B comparison")
    if args.track_out and len(args.files) != 1:
        ap.error("--track-out supports one input file per invocation")
    reports = [feature_report(p, args.track_out if i == 0 else None) for i, p in enumerate(args.files)]
    if args.json:
        print(json.dumps({"reports": reports, "verdict": verdict(*reports) if len(reports)==2 else None}, indent=2))
    else:
        for r in reports:
            print_human(r)
        if len(reports) == 2:
            print(verdict(*reports))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
