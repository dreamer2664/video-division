#!/usr/bin/env python3
"""Build CUT V11 audio-only balance correction from committed CUT V10 sources.

Only the bed contribution changes: -2.3 dB relative to the locked narration source.
The source MP4 video stream is copied, never decoded/re-encoded for output.
Requires FFmpeg/ffprobe, NumPy and SoundFile.
"""
from __future__ import annotations
import hashlib, json, math, os, re, shutil, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
V10 = HERE.parent / "cut-v10"
V10_AUDIO = V10 / "audio"
V11_AUDIO = HERE / "audio"
V10_VIDEO = V10 / "video.mp4"
V11_VIDEO = HERE / "video.mp4"
SR = 48_000
DURATION = 60.0
BED_ATTENUATION_DB = -2.3
TARGET_I = -16.0
TARGET_TP = -1.5
TARGET_LRA = 11.0
WORD_SHIFT_S = 0.300


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def parse_loudnorm(stderr: str) -> dict:
    chunks = re.findall(r"\{\s*\"input_i\".*?\}", stderr, re.S)
    if not chunks:
        raise RuntimeError("Could not parse FFmpeg loudnorm JSON")
    return json.loads(chunks[-1])


def frame_hashes(path: Path) -> list[str]:
    out = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
               "-map", "0:v:0", "-f", "framemd5", "-"], capture=True).stdout
    return [line.split(",")[-1].strip() for line in out.splitlines()
            if line and not line.startswith("#")]


def probe(path: Path) -> dict:
    result = run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
                  "-show_streams", str(path)], capture=True)
    return json.loads(result.stdout)


def loudnorm_measure(path: Path) -> dict:
    filt = f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json"
    result = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", filt,
                  "-f", "null", "-"], capture=True)
    return parse_loudnorm(result.stderr)


def fit_voice_bed(pre: np.ndarray, voice: np.ndarray, bed: np.ndarray) -> tuple[np.ndarray, float]:
    # Solve a 2x2 normal equation, avoiding a multi-GB flattened design matrix.
    vv = float(np.sum(voice * voice)); bb = float(np.sum(bed * bed)); vb = float(np.sum(voice * bed))
    vp = float(np.sum(voice * pre)); bp = float(np.sum(bed * pre))
    gains = np.linalg.solve(np.array([[vv, vb], [vb, bb]], dtype=np.float64),
                            np.array([vp, bp], dtype=np.float64))
    residual = pre - gains[0] * voice - gains[1] * bed
    residual_rms_dbfs = 20 * math.log10(float(np.sqrt(np.mean(residual * residual))) + 1e-15)
    return gains, residual_rms_dbfs


def db_rms(x: np.ndarray) -> float:
    return 20 * math.log10(float(np.sqrt(np.mean(np.square(x, dtype=np.float64)))) + 1e-15)


def margins(voice: np.ndarray, bed: np.ndarray, bed_after: np.ndarray, words: list[dict]) -> dict:
    n, channels = voice.shape
    rows = []
    all_mask = np.zeros(n, dtype=bool)
    for start_s in range(0, 60, 10):
        stop_s = start_s + 10
        mask = np.zeros(n, dtype=bool)
        for w in words:
            start = max(0.0, float(w["start_s"]) + WORD_SHIFT_S, float(start_s))
            end = min(DURATION, float(w["end_s"]) + WORD_SHIFT_S, float(stop_s))
            if end > start:
                mask[int(start * SR):min(n, int(end * SR))] = True
        all_mask |= mask
        v_rms = float(np.sqrt(np.mean(voice[mask] ** 2)))
        b_rms = float(np.sqrt(np.mean(bed[mask] ** 2)))
        b_after_rms = float(np.sqrt(np.mean(bed_after[mask] ** 2)))
        before = 20 * math.log10(v_rms / b_rms)
        after = 20 * math.log10(v_rms / b_after_rms)
        rows.append({"window_s": [start_s, stop_s], "speech_mask_samples": int(np.sum(mask)),
                     "voice_rms_dbfs": db_rms(voice[mask]), "bed_rms_before_dbfs": db_rms(bed[mask]),
                     "bed_rms_after_dbfs": db_rms(bed_after[mask]),
                     "margin_before_db": before, "margin_after_db": after})
    overall_before = 20 * math.log10(float(np.sqrt(np.mean(voice[all_mask] ** 2))) /
                                     float(np.sqrt(np.mean(bed[all_mask] ** 2))))
    overall_after = 20 * math.log10(float(np.sqrt(np.mean(voice[all_mask] ** 2))) /
                                    float(np.sqrt(np.mean(bed_after[all_mask] ** 2))))
    return {"method": "Direct RMS ratio of committed separated narration/bed stems, sampled only over union of WordBoundary word intervals, six 10-second bins; telemetry start/end shifted +0.300 s to match placed narration stem.",
            "word_interval_shift_s": WORD_SHIFT_S, "correction": "attenuate bed only; narration stem unchanged",
            "bed_gain_db": BED_ATTENUATION_DB, "bed_linear_gain": float(10 ** (BED_ATTENUATION_DB / 20.0)),
            "overall_active_speech_margin_before_db": overall_before,
            "overall_active_speech_margin_after_db": overall_after,
            "windows": rows,
            "all_windows_inside_8_to_12_db": all(8.0 <= r["margin_after_db"] <= 12.0 for r in rows)}


def main() -> None:
    V11_AUDIO.mkdir(parents=True, exist_ok=True)
    for p in (V10_VIDEO, V10_AUDIO / "master_audio_pre_loudnorm_48k.wav",
              V10_AUDIO / "narration_stem_48k.flac", V10_AUDIO / "bed_stem_48k.flac",
              V10 / "timing" / "word_telemetry.json"):
        if not p.exists(): raise FileNotFoundError(p)

    voice, sr = sf.read(V10_AUDIO / "narration_stem_48k.flac", dtype="float64", always_2d=True)
    bed, bsr = sf.read(V10_AUDIO / "bed_stem_48k.flac", dtype="float64", always_2d=True)
    pre, psr = sf.read(V10_AUDIO / "master_audio_pre_loudnorm_48k.wav", dtype="float64", always_2d=True)
    if any(x != SR for x in (sr, bsr, psr)) or voice.shape != bed.shape or voice.shape != pre.shape or voice.shape != (SR * 60, 2):
        raise RuntimeError(f"Expected matching 60 s / 48 kHz stereo stems; got voice={voice.shape}/{sr}, bed={bed.shape}/{bsr}, pre={pre.shape}/{psr}")

    fit, residual_db = fit_voice_bed(pre, voice, bed)
    bed_scale = 10 ** (BED_ATTENUATION_DB / 20.0)
    # Preserve the original pre-master exactly except for a -2.3 dB change to its fitted bed contribution.
    corrected_pre = pre + fit[1] * (bed_scale - 1.0) * bed
    corrected_bed = bed * bed_scale
    sf.write(V11_AUDIO / "bed_stem_48k.flac", corrected_bed.astype(np.float32), SR,
             format="FLAC", subtype="PCM_24")
    shutil.copy2(V10_AUDIO / "narration_stem_48k.flac", V11_AUDIO / "narration_stem_48k.flac")
    sf.write(V11_AUDIO / "master_audio_pre_loudnorm_48k.wav", corrected_pre.astype(np.float32), SR,
             format="WAV", subtype="PCM_16")

    p1_filter = f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json"
    p1 = run(["ffmpeg", "-hide_banner", "-i", str(V11_AUDIO / "master_audio_pre_loudnorm_48k.wav"),
              "-af", p1_filter, "-f", "null", "-"], capture=True)
    first = parse_loudnorm(p1.stderr)
    p2_filter = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
                 f"measured_I={first['input_i']}:measured_TP={first['input_tp']}:"
                 f"measured_LRA={first['input_lra']}:measured_thresh={first['input_thresh']}:"
                 f"offset={first['target_offset']}:linear=false:print_format=json,aresample={SR}")
    p2 = run(["ffmpeg", "-y", "-hide_banner", "-i", str(V11_AUDIO / "master_audio_pre_loudnorm_48k.wav"),
              "-af", p2_filter, "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le",
              str(V11_AUDIO / "master_audio_48k.wav")], capture=True)
    second = parse_loudnorm(p2.stderr)

    tmp = HERE / "video.v11.tmp.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(V10_VIDEO),
         "-i", str(V11_AUDIO / "master_audio_48k.wav"), "-map", "0:v:0", "-map", "1:a:0",
         "-map_metadata", "0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-ac", "2", "-movflags", "+faststart", str(tmp)])
    before_hashes = frame_hashes(V10_VIDEO)
    after_hashes = frame_hashes(tmp)
    if len(before_hashes) != 1800 or before_hashes != after_hashes:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Audio-only gate failed: video frames differ ({len(before_hashes)} before, {len(after_hashes)} after)")
    final_measure = loudnorm_measure(tmp)
    final_probe = probe(tmp)
    video = next(s for s in final_probe["streams"] if s.get("codec_type") == "video")
    audio = next(s for s in final_probe["streams"] if s.get("codec_type") == "audio")
    duration = float(final_probe["format"]["duration"])
    if (video.get("codec_name") != "h264" or video.get("nb_frames") != "1800" or
        video.get("width") != 1920 or video.get("height") != 1080 or video.get("avg_frame_rate") != "30/1" or
        audio.get("codec_name") != "aac" or audio.get("sample_rate") != "48000" or audio.get("channels") != 2 or
        abs(duration - DURATION) > .001):
        tmp.unlink(missing_ok=True)
        raise RuntimeError("Final stream gate failed: " + json.dumps(final_probe, indent=2))
    integrated = float(final_measure["input_i"]); true_peak = float(final_measure["input_tp"])
    if not (-16.5 <= integrated <= -15.5 and true_peak <= -1.0):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Loudness gate failed: {integrated} LUFS / {true_peak} dBTP")
    final_probe["format"]["filename"] = "videos/team-b/cut-v11/video.mp4"

    timing = json.loads((V10 / "timing" / "word_telemetry.json").read_text(encoding="utf-8"))
    voice_saved, _ = sf.read(V11_AUDIO / "narration_stem_48k.flac", dtype="float64", always_2d=True)
    bed_saved, _ = sf.read(V11_AUDIO / "bed_stem_48k.flac", dtype="float64", always_2d=True)
    balance = margins(voice_saved, bed, bed_saved, timing["words"])
    if not balance["all_windows_inside_8_to_12_db"]:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("Voice/bed source balance gate failed: " + json.dumps(balance, indent=2))
    caption_path = V10 / "timing" / "captions_locked.json"
    output_sha = sha(tmp)
    ledger = {
        "version": "cut/v11 audio-only correction", "source_cut_v10_commit": "f0032130e5fac0cdd4841dc6db69a533042b8561",
        "input_video_sha256": sha(V10_VIDEO),
        "input_premaster_sha256": sha(V10_AUDIO / "master_audio_pre_loudnorm_48k.wav"),
        "input_voice_stem_sha256": sha(V10_AUDIO / "narration_stem_48k.flac"),
        "input_bed_stem_sha256": sha(V10_AUDIO / "bed_stem_48k.flac"),
        "caption_source_sha256_unchanged": sha(caption_path),
        "fitted_original_mix_gains": {"voice_linear": float(fit[0]), "bed_linear": float(fit[1]),
                                       "voice_db": float(20*np.log10(abs(fit[0]))),
                                       "bed_db": float(20*np.log10(abs(fit[1]))),
                                       "residual_rms_dbfs": residual_db},
        "correction": {"component": "bed only", "gain_db": BED_ATTENUATION_DB,
                       "linear_gain": bed_scale, "reason": "move opening +5.872 dB voice/bed margin into the +8 to +12 dB target; also clear the other below-target 30–40 s window"},
        "voice_bed_balance": balance,
        "loudnorm_target": {"I": TARGET_I, "TP": TARGET_TP, "LRA": TARGET_LRA, "linear": False},
        "loudnorm_pass1_json": first, "loudnorm_pass2_json": second,
        "loudnorm_pass2_filter": p2_filter,
        "final_decoded_aac_loudnorm_json": final_measure,
        "final_probe": final_probe,
        "video_frame_hashes_identical": len(before_hashes),
        "output_video_sha256": output_sha,
        "picture_policy": "The v10 H.264 video stream is stream-copied; 1800/1800 decoded frame hashes match. Captions are baked into those same unchanged video frames."
    }
    (V11_AUDIO / "voice_bed_balance_ledger.json").write_text(json.dumps(ledger, indent=2)+"\n", encoding="utf-8")
    gain_mapping = {
        "source_pre_loudnorm": "../cut-v10/audio/master_audio_pre_loudnorm_48k.wav",
        "source_pre_loudnorm_sha256": sha(V10_AUDIO / "master_audio_pre_loudnorm_48k.wav"),
        "v11_pre_loudnorm": "audio/master_audio_pre_loudnorm_48k.wav",
        "v11_pre_loudnorm_sha256": sha(V11_AUDIO / "master_audio_pre_loudnorm_48k.wav"),
        "normalized_master": "audio/master_audio_48k.wav",
        "normalized_master_sha256": sha(V11_AUDIO / "master_audio_48k.wav"),
        "bed_attenuation_db": BED_ATTENUATION_DB,
        "loudnorm_target": ledger["loudnorm_target"],
        "loudnorm_pass1_json": first, "loudnorm_pass2_json": second,
        "loudnorm_pass2_filter": p2_filter,
        "final_decoded_aac_loudnorm_json": final_measure,
        "final_video_sha256": output_sha,
        "picture_policy": ledger["picture_policy"]
    }
    (V11_AUDIO / "gain_mapping.json").write_text(json.dumps(gain_mapping, indent=2)+"\n", encoding="utf-8")
    (V11_AUDIO / "final_loudnorm_analysis.json").write_text(json.dumps(final_measure, indent=2)+"\n", encoding="utf-8")
    (V11_AUDIO / "final_ffprobe.json").write_text(json.dumps(final_probe, indent=2)+"\n", encoding="utf-8")
    (V11_AUDIO / "frame_hashes.json").write_text(json.dumps({"v10_source_video_sha256": sha(V10_VIDEO),
        "v11_video_sha256": output_sha, "frame_count": len(before_hashes), "all_decoded_hashes_identical": True,
        "hash_list_sha256": hashlib.sha256(("\n".join(after_hashes)+"\n").encode()).hexdigest()}, indent=2)+"\n", encoding="utf-8")
    os.replace(tmp, V11_VIDEO)
    print(json.dumps({"output_video": str(V11_VIDEO), "sha256": sha(V11_VIDEO),
                      "integrated_lufs": integrated, "true_peak_dbtp": true_peak,
                      "opening_voice_bed_margin_db": balance["windows"][0]["margin_after_db"],
                      "overall_active_speech_margin_db": balance["overall_active_speech_margin_after_db"],
                      "frame_hashes_identical": len(before_hashes),
                      "margins_db": [r["margin_after_db"] for r in balance["windows"]]}, indent=2))

if __name__ == "__main__":
    main()
