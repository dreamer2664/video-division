#!/usr/bin/env python3
"""Offline two-pass loudnorm for CUT V10's locked pre-fix audio master.
No speech synthesis, picture rendering, or source-stem edits occur here.
"""
from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path
import soundfile as sf

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
SR = 48_000
DURATION = 60.0
LOUDNORM_I = -16.0
LOUDNORM_TP = -1.5  # AAC-safe margin; acceptance ceiling is -1.0 dBTP
LOUDNORM_LRA = 11.0


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_capture(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def loudnorm_json(stderr: str) -> dict:
    matches = re.findall(r"\{\s*\"input_i\".*?\}", stderr, re.S)
    if not matches:
        raise RuntimeError("FFmpeg loudnorm JSON missing:\n" + stderr[-3000:])
    return json.loads(matches[-1])


def build_audio() -> dict:
    source = AUDIO / "master_audio_pre_loudnorm_48k.wav"
    output = AUDIO / "master_audio_48k.wav"
    if not source.exists():
        raise FileNotFoundError(f"Missing locked pre-fix audio source: {source}")
    info = sf.info(source)
    if info.samplerate != SR or info.channels != 2 or abs(info.duration - DURATION) > 1e-6:
        raise RuntimeError(f"Expected 60.000 s / 48 kHz stereo source, got {info}")

    pass1_filter = f"loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}:LRA={LOUDNORM_LRA}:print_format=json"
    p1 = run_capture(["ffmpeg", "-hide_banner", "-i", str(source), "-af", pass1_filter, "-f", "null", "-"])
    first = loudnorm_json(p1.stderr)
    pass2_filter = (
        f"loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}:LRA={LOUDNORM_LRA}:"
        f"measured_I={first['input_i']}:measured_TP={first['input_tp']}:"
        f"measured_LRA={first['input_lra']}:measured_thresh={first['input_thresh']}:"
        f"offset={first['target_offset']}:linear=false:print_format=json,aresample={SR}"
    )
    p2 = run_capture(["ffmpeg", "-y", "-hide_banner", "-i", str(source), "-af", pass2_filter,
                      "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", str(output)])
    second = loudnorm_json(p2.stderr)
    result = {
        "source": str(source.relative_to(HERE)), "source_sha256": sha(source),
        "normalized_master": str(output.relative_to(HERE)), "normalized_master_sha256": sha(output),
        "sample_rate_hz": SR, "channels": 2, "duration_s": DURATION,
        "loudnorm_target": {"I": LOUDNORM_I, "TP": LOUDNORM_TP, "LRA": LOUDNORM_LRA, "linear": False},
        "loudnorm_pass1_json": first, "loudnorm_pass2_json": second,
        "loudnorm_pass2_filter": pass2_filter,
        "picture_policy": "Not used by this audio build; remux uses -c:v copy.",
    }
    (AUDIO / "gain_mapping.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(build_audio(), indent=2))
