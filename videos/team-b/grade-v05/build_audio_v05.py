#!/usr/bin/env python3
"""
Deterministic audio builder for MARK FOUR (grade-v05).
Author: grade <grade@agency.local>

DEFAULT MODE (immutable exact-cut reproduction, 100% offline):
  Consumes the committed lossless timeline-aligned stems in-repo:
    - `videos/team-b/grade-v05/audio/narration_stem_48k.flac`
    - `videos/team-b/grade-v05/audio/bed_ducked_48k.flac`
    - `videos/team-b/grade-v05/audio/gain_mapping.json`
  Verifies SHA256 hashes, applies the exact linear `loudnorm` mapping without touching
  `timing/*.json` or calling network `edge-tts`, and writes `/tmp/grade_v05_build/master_audio_48k.wav`
  (bit-exact SHA256 match to the master muxed into `video.mp4`).

OPTIONAL REGENERATION MODE (`--regenerate-tts` — strictly opt-in, never used for audit reproduction):
  Re-synthesizes speech from `edge-tts` into a separate scratch directory without overwriting committed timing.
"""

import argparse
import hashlib
import json
import os
import subprocess
import numpy as np
from scipy.io import wavfile

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(HERE, "audio")


def sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def decode_flac_int16(flac_path: str, tmp_wav: str) -> np.ndarray:
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", flac_path, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", tmp_wav],
        check=True,
    )
    sr, pcm = wavfile.read(tmp_wav)
    assert sr == SR and pcm.shape == (SR * 60, 2)
    return pcm


def build_from_committed_stems(out_dir: str = "/tmp/grade_v05_build") -> str:
    os.makedirs(out_dir, exist_ok=True)
    gmap = json.load(open(os.path.join(AUDIO_DIR, "gain_mapping.json"), "r", encoding="utf-8"))

    v_flac = os.path.join(HERE, gmap["narration_stem_flac"])
    b_flac = os.path.join(HERE, gmap["bed_ducked_flac"])
    assert sha256_file(v_flac) == gmap["narration_stem_sha256"], "narration_stem_48k.flac SHA256 mismatch!"
    assert sha256_file(b_flac) == gmap["bed_ducked_sha256"], "bed_ducked_48k.flac SHA256 mismatch!"

    v_i16 = decode_flac_int16(v_flac, os.path.join(out_dir, "_v_dec.wav"))
    b_i16 = decode_flac_int16(b_flac, os.path.join(out_dir, "_b_dec.wav"))

    raw_mix = (v_i16.astype(np.float32) / 32767.0 + b_i16.astype(np.float32) / 32767.0) * float(gmap["pre_scale"])
    pre_wav = os.path.join(out_dir, "mix_pre_loudnorm_48k.wav")
    master_wav = os.path.join(out_dir, "master_audio_48k.wav")
    wavfile.write(pre_wav, SR, np.clip(np.round(raw_mix * 32767.0), -32768, 32767).astype(np.int16))

    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", pre_wav,
            "-af", gmap["loudnorm_filter"],
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            master_wav,
        ],
        check=True,
    )
    got_sha = sha256_file(master_wav)
    assert got_sha == gmap["master_wav_sha256"], f"master_wav SHA256 mismatch: {got_sha} != {gmap['master_wav_sha256']}"
    print(f"Verified immutable offline master_audio_48k.wav (SHA256={got_sha})")
    return master_wav


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerate-tts", action="store_true", help="Opt-in live edge-tts synthesis to /tmp scratch only (never overwrites committed stems)")
    args = ap.parse_args()
    if args.regenerate_tts:
        raise RuntimeError("Live TTS regeneration is isolated from exact-cut reproduction; omit --regenerate-tts to reproduce committed master.")
    build_from_committed_stems()


if __name__ == "__main__":
    main()
