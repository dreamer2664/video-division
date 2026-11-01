#!/usr/bin/env python3
"""Deterministic offline audio build from the committed Edge-TTS source MP3.
The separate synthesize_voiceover.py script is only needed to obtain a new voice take.
"""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt
from scipy.ndimage import uniform_filter1d

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
SR = 48_000
DURATION = 60.0
N = int(SR * DURATION)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def build_audio() -> dict:
    AUDIO.mkdir(parents=True, exist_ok=True)
    source = AUDIO / "narration_source.mp3"
    narration = AUDIO / "narration_stem_48k.flac"
    bed_path = AUDIO / "bed_stem_48k.flac"
    mix_path = AUDIO / "master_audio_48k.wav"
    if not source.exists():
        raise FileNotFoundError(source)

    # Keep 0.300 s head for breathing room; exactly 60 s lossless stereo stem.
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
         "-af", "adelay=300|300,apad=whole_dur=60,atrim=0:60",
         "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", "-c:a", "flac", str(narration)])

    # Deterministic nocturnal rain + low cello-like drone; all procedural, no music sample.
    rng = np.random.default_rng(1101)
    noise = rng.standard_normal((N, 2), dtype=np.float32)
    low_sos = butter(4, 900, btype="lowpass", fs=SR, output="sos")
    high_sos = butter(3, 1500, btype="highpass", fs=SR, output="sos")
    rain_low = sosfilt(low_sos, noise, axis=0).astype(np.float32)
    rain_high = sosfilt(high_sos, noise, axis=0).astype(np.float32)
    low_rms = float(np.sqrt(np.mean(rain_low * rain_low)))
    high_rms = float(np.sqrt(np.mean(rain_high * rain_high)))
    t = np.arange(N, dtype=np.float32) / np.float32(SR)
    swell = (0.72 + 0.18 * np.sin(2 * np.pi * t / 17.0) + 0.10 * np.sin(2 * np.pi * t / 31.0)).astype(np.float32)
    drone_l = (0.012 * np.sin(2 * np.pi * 43.7 * t) + 0.008 * np.sin(2 * np.pi * 55.0 * t + 0.7) + 0.0035 * np.sin(2 * np.pi * 65.4 * t + 1.2))
    drone_r = (0.011 * np.sin(2 * np.pi * 43.7 * t + 0.08) + 0.008 * np.sin(2 * np.pi * 55.0 * t + 0.9) + 0.003 * np.sin(2 * np.pi * 65.4 * t + 1.35))
    bed = np.empty((N, 2), dtype=np.float32)
    bed[:, 0] = (rain_low[:, 0] / low_rms * 0.013 + rain_high[:, 0] / high_rms * 0.0022 + drone_l) * swell
    bed[:, 1] = (rain_low[:, 1] / low_rms * 0.013 + rain_high[:, 1] / high_rms * 0.0022 + drone_r) * swell
    bed *= np.float32(2.5)  # keep the ominous bed roughly 8 dB below active speech before ducking
    sf.write(bed_path, np.clip(bed, -1, 1), SR, format="FLAC", subtype="PCM_16")
    del noise, rain_low, rain_high, t, swell, drone_l, drone_r, bed

    voice, sr = sf.read(narration, dtype="float32", always_2d=True)
    bed, sr_b = sf.read(bed_path, dtype="float32", always_2d=True)
    if sr != SR or sr_b != SR or voice.shape != (N, 2) or bed.shape != (N, 2):
        raise RuntimeError(f"Unexpected audio stem shapes/rates: voice={voice.shape}/{sr}, bed={bed.shape}/{sr_b}")
    voice_rms = np.sqrt(uniform_filter1d(np.mean(voice * voice, axis=1), size=SR // 3, mode="nearest"))
    duck = np.where(voice_rms > 0.0035, 10.0 ** (-4.0 / 20.0), 1.0).astype(np.float32)
    mix = voice * np.float32(0.94) + bed * duck[:, None]
    peak = float(np.max(np.abs(mix)))
    if peak > 0.89:
        mix *= np.float32(0.89 / peak)
    sf.write(mix_path, np.clip(mix, -1, 1), SR, subtype="PCM_16")

    info = {
        "voice_source_mp3": str(source.relative_to(HERE)),
        "voice_source_sha256": sha(source),
        "narration_stem": str(narration.relative_to(HERE)),
        "narration_stem_sha256": sha(narration),
        "bed_stem": str(bed_path.relative_to(HERE)),
        "bed_stem_sha256": sha(bed_path),
        "mix": str(mix_path.relative_to(HERE)),
        "mix_sha256": sha(mix_path),
        "sample_rate_hz": SR,
        "channels": 2,
        "duration_s": DURATION,
        "mix_peak_dbfs": 20 * np.log10(max(float(np.max(np.abs(mix))), 1e-9)),
        "narration_rms_dbfs": 20 * np.log10(max(float(np.sqrt(np.mean(voice * voice))), 1e-9)),
        "bed_rms_dbfs": 20 * np.log10(max(float(np.sqrt(np.mean(bed * bed))), 1e-9)),
        "sidechain_duck_db": -4.0,
        "bed_generator_seed": 1101,
    }
    (AUDIO / "gain_mapping.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return info

if __name__ == "__main__":
    result = build_audio()
    print(json.dumps(result, indent=2))
