#!/usr/bin/env python3
"""
First-party spoken narration + sidechain-ducked nocturnal score & rain mixer for MARK FOUR (grade-v05).
Author: grade <grade@agency.local>

Pipeline:
  1. Synthesizes all 11 spoken lines with `edge-tts` (`en-US-ChristopherNeural`, `--rate=-12%`, `--pitch=-4Hz`)
     capturing exact 100ns `WordBoundary` events (or reuses cached stems in /tmp/grade_v05_build/narration if already built).
  2. Places lines onto a 60.000s 48kHz stereo master timeline with documentary-calm breaths and a deliberate
     1.120s pre-twist silence (43.473s -> 44.593s) before Line 09 ('Someone unbolted Mark Four...').
  3. Applies broadcast voice EQ (85Hz HPF, -2dB @ 320Hz mud cut, +2.6dB @ 3.0kHz phone-speaker intelligibility presence)
     and smooth soft-knee levelling -> `narration_stem_48k.wav`.
  4. Synthesizes original procedural stereo storm rain, dark bowed C-minor sub-cello harmonic drone, and frame-locked
     diegetic foley (2:17 bell, brass pocket-watch ticks, gauge needle arrest, pre-twist heartbeat, booth switch click
     at 52.45s, and open-sluice floodwater surge).
  5. Sidechain-ducks the music/rain bed by ~10.5 dB under active speech (rising smoothly during breath pauses) and
     masters the full 60.000s stereo mix via two-pass EBU R128 `loudnorm` to `-16.0 LUFS` (`TP <= -1.4 dBTP`).
"""

import asyncio
import json
import os
import re
import subprocess
import numpy as np
from scipy import signal
from scipy.io import wavfile
import edge_tts

SR = 48000
TOTAL_DUR = 60.0
N_SAMPLES = int(SR * TOTAL_DUR)

VOICE = "en-US-ChristopherNeural"
RATE = "-12%"
PITCH = "-4Hz"

LINES = [
    ("01", "At two seventeen in the morning, the old stone lock on the Blackwater has only one rule."),
    ("02", "Never open the sluice if the rain reaches Mark Four."),
    ("03", "For forty years, a night keeper has logged the water every fifteen minutes."),
    ("04", "One forty-five: Mark Two. Two o'clock: Mark Three."),
    ("05", "Outside, four inches of cold rain fall in twenty minutes. Yet the gauge stops moving."),
    ("06", "Three millimeters below the red line. Still as dark glass."),
    ("07", "So you carry the lantern out onto the catwalk to check for a jammed float."),
    ("08", "Your light hits the wet stone wall. And you see the empty bolt holes."),
    ("09", "Someone unbolted Mark Four, and moved the brass plate two feet higher."),
    ("10", "Behind you, the lamp in the keeper's booth clicks off."),
    ("11", "The river never stopped rising. The sluice gate behind you is already open."),
]

GAPS_BEFORE = [0.36, 0.38, 0.42, 0.38, 0.42, 0.40, 0.44, 0.42, 1.12, 0.46, 0.42]


async def ensure_tts_lines(narr_dir: str):
    manifest_path = os.path.join(narr_dir, "timing_manifest.json")
    if os.path.exists(manifest_path) and all(
        os.path.exists(os.path.join(narr_dir, f"line_{lid}_raw.wav")) for lid, _ in LINES
    ):
        return json.load(open(manifest_path))

    os.makedirs(narr_dir, exist_ok=True)
    results = []
    for lid, text in LINES:
        mp3_path = os.path.join(narr_dir, f"line_{lid}.mp3")
        raw_wav = os.path.join(narr_dir, f"line_{lid}_raw.wav")
        comm = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
        words = []
        with open(mp3_path, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append({
                        "start": round(chunk["offset"] / 1e7, 3),
                        "end": round((chunk["offset"] + chunk["duration"]) / 1e7, 3),
                        "text": chunk["text"],
                    })
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mp3_path, "-ar", str(SR), "-ac", "1", raw_wav],
            check=True,
        )
        dur = float(
            subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", raw_wav]
            ).decode().strip()
        )
        first_w = words[0]["start"]
        last_w = words[-1]["end"]
        results.append({
            "id": lid,
            "text": text,
            "raw_dur": round(dur, 3),
            "first_w": first_w,
            "last_w": last_w,
            "span": round(last_w - first_w, 3),
            "words": words,
        })
    json.dump(results, open(manifest_path, "w"), indent=2)
    return results


def peaking_eq(x: np.ndarray, f0: float, q: float, gain_db: float) -> np.ndarray:
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2.0 * q)
    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A
    b = np.array([b0, b1, b2]) / a0
    a = np.array([1.0, a1 / a0, a2 / a0])
    return signal.lfilter(b, a, x).astype(np.float32)


def build_voice_stem(manifest, narr_dir: str):
    mono = np.zeros(N_SAMPLES, dtype=np.float32)
    speech_gate = np.zeros(N_SAMPLES, dtype=np.float32)
    cursor = 0.0
    placed_lines = []

    for item, gap in zip(manifest, GAPS_BEFORE):
        lid = item["id"]
        sr_in, data = wavfile.read(os.path.join(narr_dir, f"line_{lid}_raw.wav"))
        assert sr_in == SR
        audio = data.astype(np.float32) / 32768.0

        t_in = max(0.0, item["first_w"] - 0.05)
        t_out = min(len(audio) / SR, item["last_w"] + 0.16)
        s_in = int(round(t_in * SR))
        s_out = int(round(t_out * SR))
        clip = audio[s_in:s_out].copy()
        fade_n = int(0.025 * SR)
        clip[:fade_n] *= np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
        clip[-fade_n:] *= np.linspace(1.0, 0.0, fade_n, dtype=np.float32)

        speech_start_global = cursor + gap
        clip_start_global = speech_start_global - (item["first_w"] - t_in)
        p0 = int(round(clip_start_global * SR))
        p1 = p0 + len(clip)
        mono[p0:p1] += clip

        offset_shift = speech_start_global - item["first_w"]
        line_words = []
        for w in item["words"]:
            ws = round(w["start"] + offset_shift, 3)
            we = round(w["end"] + offset_shift, 3)
            line_words.append({"line": lid, "text": w["text"], "start": ws, "end": we})
            g0 = max(0, int((ws - 0.04) * SR))
            g1 = min(N_SAMPLES, int((we + 0.06) * SR))
            speech_gate[g0:g1] = 1.0

        speech_end_global = line_words[-1]["end"]
        placed_lines.append({
            "id": lid,
            "text": item["text"],
            "speech_start": round(speech_start_global, 3),
            "speech_end": round(speech_end_global, 3),
            "words": line_words,
        })
        cursor = speech_end_global

    # Broadcast clarity & warmth EQ for phone-speaker + studio intelligibility:
    # 1. 85 Hz 2nd-order HPF (clean sub-rumble)
    sos_hp = signal.butter(2, 85.0 / (SR * 0.5), btype="highpass", output="sos")
    v = signal.sosfilt(sos_hp, mono).astype(np.float32)
    # 2. Warm low-chest anchor (+1.2 dB @ 135 Hz), mud cut (-2.2 dB @ 330 Hz), clear articulation (+2.8 dB @ 3100 Hz)
    v = peaking_eq(v, 135.0, 1.1, 1.2)
    v = peaking_eq(v, 330.0, 1.4, -2.2)
    v = peaking_eq(v, 3100.0, 1.0, 2.8)
    # 3. Gentle broadcast envelope levelling + soft saturation ceiling
    env = np.abs(v)
    sos_env = signal.butter(1, 12.0 / (SR * 0.5), btype="lowpass", output="sos")
    smooth_env = signal.sosfilt(sos_env, env) + 1e-5
    thresh = 0.16
    gain = np.where(smooth_env > thresh, (thresh / smooth_env) ** 0.42, 1.0)
    v = v * gain
    v = v / max(np.max(np.abs(v)), 1e-6) * 0.78
    v = np.tanh(v * 1.12) / np.tanh(1.12) * 0.80

    # Subtle early-reflection close room air (-28 dB stereo Haas micro-ambience so voice feels physical, never metallic)
    d_l = int(0.011 * SR)
    d_r = int(0.017 * SR)
    sos_room = signal.butter(2, [220.0 / (SR * 0.5), 4200.0 / (SR * 0.5)], btype="bandpass", output="sos")
    room = signal.sosfilt(sos_room, v).astype(np.float32) * 0.038
    vl = v.copy()
    vr = v.copy()
    vl[d_l:] += room[:-d_l]
    vr[d_r:] -= room[:-d_r]

    voice_stereo = np.column_stack([vl, vr]).astype(np.float32)
    return voice_stereo, speech_gate, placed_lines


def build_score_and_foley(t: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(202605)

    # --- 1. Procedural Stereo Nocturnal Rain Bed ---
    wn_l = rng.normal(0.0, 1.0, N_SAMPLES).astype(np.float32)
    wn_r = rng.normal(0.0, 1.0, N_SAMPLES).astype(np.float32)
    # Mid storm wash (450 - 2600 Hz) + fine slate droplets (3200 - 7800 Hz), gently notched around 2.8kHz voice band
    sos_wash = signal.butter(2, [420.0 / (SR * 0.5), 2100.0 / (SR * 0.5)], btype="bandpass", output="sos")
    sos_patter = signal.butter(2, [4200.0 / (SR * 0.5), 8200.0 / (SR * 0.5)], btype="bandpass", output="sos")
    rain_l = signal.sosfilt(sos_wash, wn_l) * 0.055 + signal.sosfilt(sos_patter, wn_l) * 0.026
    rain_r = signal.sosfilt(sos_wash, wn_r) * 0.055 + signal.sosfilt(sos_patter, wn_r) * 0.026

    # Slow storm gust modulation + spatial scene curve (muffled inside glass booth Shot 04; eerie hush on Shot 06)
    gust = 0.86 + 0.14 * np.sin(2.0 * np.pi * 0.075 * t + 0.4)
    booth_muffle = 1.0 - 0.52 * np.exp(-((t - 17.6) / 2.6) ** 2)
    glass_stillness = 1.0 - 0.45 * np.exp(-((t - 30.4) / 2.4) ** 2)
    catwalk_swell = 1.0 + 0.28 * (1.0 / (1.0 + np.exp(-(t - 33.2) * 2.0)))
    rain_env = (gust * booth_muffle * glass_stillness * catwalk_swell).astype(np.float32)
    rain_l *= rain_env
    rain_r *= rain_env

    # --- 2. Dark Bowed C-Minor / Phrygian Sub-Cello & Low Brass Nocturne ---
    # Harmonic chapters:
    #   0-27.6s:  C1 (32.70Hz) + C2 (65.41Hz) + G2 (98.00Hz) + Eb3 (155.56Hz) slow bowed swell
    #   27.6-33.2s: Suspended high glassy harmonic G3 (196Hz) + C2 whisper ('Still as dark glass')
    #   33.2-44.2s: Poster & Lantern search — F1 (43.65Hz) + C2 (65.41Hz) + Ab2 (103.83Hz) rising dread
    #   44.2-60.0s: THE TURN — C1 (32.70Hz) + Db2 (69.30Hz Phrygian tension!) + G2 (98.00Hz)
    w_a = 1.0 / (1.0 + np.exp(np.clip((t - 27.6) * 2.5, -40.0, 40.0)))
    w_b = (1.0 / (1.0 + np.exp(np.clip(-(t - 27.6) * 2.5, -40.0, 40.0)))) * (1.0 / (1.0 + np.exp(np.clip((t - 33.2) * 2.5, -40.0, 40.0))))
    w_c = (1.0 / (1.0 + np.exp(np.clip(-(t - 33.2) * 2.5, -40.0, 40.0)))) * (1.0 / (1.0 + np.exp(np.clip((t - 44.3) * 3.5, -40.0, 40.0))))
    w_d = 1.0 / (1.0 + np.exp(np.clip(-(t - 44.3) * 3.5, -40.0, 40.0)))

    vib = 0.0025 * np.sin(2.0 * np.pi * 4.6 * t)

    def bowed_note(freq: float, detune: float = 0.0) -> np.ndarray:
        f = freq * (1.0 + detune)
        ph = 2.0 * np.pi * f * (t + vib / max(f, 30.0))
        sig = 0.68 * np.sin(ph) + 0.22 * np.sin(2.0 * ph + 0.3) + 0.08 * np.sin(3.0 * ph + 0.7)
        return sig.astype(np.float32)

    ch_a_l = 0.45 * bowed_note(32.703) + 0.40 * bowed_note(65.406, -0.0015) + 0.22 * bowed_note(97.999, 0.001) + 0.10 * bowed_note(155.563, -0.001)
    ch_a_r = 0.45 * bowed_note(32.703) + 0.40 * bowed_note(65.406, +0.0015) + 0.22 * bowed_note(97.999, -0.001) + 0.10 * bowed_note(155.563, +0.001)

    ch_b_l = 0.28 * bowed_note(65.406) + 0.14 * np.sin(2.0 * np.pi * 195.998 * t)
    ch_b_r = 0.28 * bowed_note(65.406) + 0.14 * np.sin(2.0 * np.pi * 196.400 * t + 0.5)

    ch_c_l = 0.48 * bowed_note(43.654) + 0.38 * bowed_note(87.307, -0.0018) + 0.24 * bowed_note(130.813) + 0.14 * bowed_note(207.652, -0.0012)
    ch_c_r = 0.48 * bowed_note(43.654) + 0.38 * bowed_note(87.307, +0.0018) + 0.24 * bowed_note(130.813) + 0.14 * bowed_note(207.652, +0.0012)

    ch_d_l = 0.55 * bowed_note(32.703) + 0.42 * bowed_note(65.406, -0.002) + 0.28 * bowed_note(69.296, 0.001) + 0.20 * bowed_note(97.999)
    ch_d_r = 0.55 * bowed_note(32.703) + 0.42 * bowed_note(65.406, +0.002) + 0.28 * bowed_note(69.296, -0.001) + 0.20 * bowed_note(97.999)

    bow_breath = 0.82 + 0.18 * np.sin(2.0 * np.pi * 0.11 * t - 0.6)
    score_l = (w_a * ch_a_l + w_b * ch_b_l + w_c * ch_c_l + w_d * ch_d_l) * bow_breath * 0.115
    score_r = (w_a * ch_a_r + w_b * ch_b_r + w_c * ch_c_r + w_d * ch_d_r) * bow_breath * 0.115

    # Lowpass score smoothly at 420 Hz so zero masking occurs in speech formants (500 Hz - 4 kHz)
    sos_score_lp = signal.butter(3, 420.0 / (SR * 0.5), btype="lowpass", output="sos")
    score_l = signal.sosfilt(sos_score_lp, score_l).astype(np.float32)
    score_r = signal.sosfilt(sos_score_lp, score_r).astype(np.float32)

    # --- 3. Frame-Locked Diegetic Nocturnal Foley ---
    foley_l = np.zeros(N_SAMPLES, dtype=np.float32)
    foley_r = np.zeros(N_SAMPLES, dtype=np.float32)

    def add_bell(t0: float, amp: float = 0.075):
        i0 = int(t0 * SR)
        dur_s = 3.2
        n = min(int(dur_s * SR), N_SAMPLES - i0)
        lt = np.arange(n, dtype=np.float32) / SR
        env = np.exp(-lt * 1.45) * (1.0 - np.exp(-lt * 80.0))
        # Dark weathered bronze lock bell partials (G3/D4/Bb4 inharmonic)
        bell = (0.55 * np.sin(2 * np.pi * 196.0 * lt)
                + 0.28 * np.sin(2 * np.pi * 293.7 * lt)
                + 0.14 * np.sin(2 * np.pi * 468.2 * lt) * np.exp(-lt * 2.6)) * env * amp
        foley_l[i0:i0 + n] += bell * 0.9
        foley_r[i0:i0 + n] += bell * 1.0

    def add_click(t0: float, freq: float, decay: float, amp: float):
        i0 = int(t0 * SR)
        n = min(int(0.18 * SR), N_SAMPLES - i0)
        lt = np.arange(n, dtype=np.float32) / SR
        burst = (np.sin(2 * np.pi * freq * lt) + 0.5 * np.sin(2 * np.pi * freq * 2.31 * lt)) * np.exp(-lt * decay) * amp
        foley_l[i0:i0 + n] += burst
        foley_r[i0:i0 + n] += burst * 0.92

    def add_sub_thump(t0: float, f_start: float, f_end: float, dur_s: float, amp: float):
        i0 = int(t0 * SR)
        n = min(int(dur_s * SR), N_SAMPLES - i0)
        lt = np.arange(n, dtype=np.float32) / SR
        inst_f = f_start + (f_end - f_start) * (lt / dur_s)
        ph = 2.0 * np.pi * np.cumsum(inst_f) / SR
        env = np.exp(-lt * (4.2 / dur_s)) * (1.0 - np.exp(-lt * 90.0))
        thump = np.sin(ph) * env * amp
        foley_l[i0:i0 + n] += thump
        foley_r[i0:i0 + n] += thump

    # 0.08s: Distant weathered Blackwater night bell
    add_bell(0.08, amp=0.060)
    # 14.95s & 18.18s: Subtle pocket-watch / log ticks before '1:45' and '2:00'
    add_click(14.92, 1650.0, 65.0, 0.032)
    add_click(18.14, 1650.0, 65.0, 0.032)
    # 26.40s: Metallic gauge needle arrest click ('stops moving')
    add_click(26.40, 1180.0, 48.0, 0.038)
    # 43.62s & 44.02s: Tense double heartbeat sub-pulse in the 1.12s pre-twist silence!
    add_sub_thump(43.62, 68.0, 38.0, 0.34, 0.14)
    add_sub_thump(43.98, 62.0, 34.0, 0.42, 0.18)
    # 44.56s: Deep tectonic turn impact ('Someone unbolted Mark Four')
    add_sub_thump(44.56, 78.0, 29.0, 1.35, 0.16)
    # 52.45s: Crisp physical Bakelite toggle switch CLICK as the booth lamp snaps off!
    add_click(52.44, 2350.0, 85.0, 0.075)
    add_click(52.47, 920.0, 55.0, 0.065)

    # 53.35s - 59.85s: Deep open-sluice floodwater roar surging underneath the final shot
    s_mask = np.clip((t - 53.2) / 1.4, 0.0, 1.0) * np.clip((59.95 - t) / 0.75, 0.0, 1.0)
    sos_roar = signal.butter(2, [65.0 / (SR * 0.5), 340.0 / (SR * 0.5)], btype="bandpass", output="sos")
    roar_l = signal.sosfilt(sos_roar, wn_l).astype(np.float32) * s_mask * 0.085
    roar_r = signal.sosfilt(sos_roar, wn_r).astype(np.float32) * s_mask * 0.085

    bed_l = rain_l + score_l + foley_l + roar_l
    bed_r = rain_r + score_r + foley_r + roar_r

    # Clean head/tail micro-fades (0.25s in, 0.35s out)
    fi = int(0.25 * SR)
    fo = int(0.35 * SR)
    bed_l[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    bed_r[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    bed_l[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    bed_r[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)

    return np.column_stack([bed_l, bed_r]).astype(np.float32)


def main():
    build_dir = "/tmp/grade_v05_build"
    narr_dir = os.path.join(build_dir, "narration")
    os.makedirs(narr_dir, exist_ok=True)

    manifest = asyncio.run(ensure_tts_lines(narr_dir))
    voice_stereo, speech_gate, placed_lines = build_voice_stem(manifest, narr_dir)

    # Save clean 48kHz stereo narration stem for ffprobe & QA verification
    narr_stem_path = os.path.join(narr_dir, "narration_stem_48k.wav")
    wavfile.write(narr_stem_path, SR, np.clip(voice_stereo * 32767.0, -32768, 32767).astype(np.int16))

    t = np.arange(N_SAMPLES, dtype=np.float32) / SR
    bed_stereo = build_score_and_foley(t)

    # Smooth sidechain ducking envelope:
    # Under active speech (speech_gate == 1), duck bed by -10.5 dB (factor 0.298) relative to its un-ducked swell,
    # and calibrate overall bed gain so active bed sits ~10.5 dB RMS below active voice!
    sos_duck = signal.butter(1, 3.2 / (SR * 0.5), btype="lowpass", output="sos")
    duck_curve = signal.sosfilt(sos_duck, speech_gate).astype(np.float32)
    duck_curve = np.clip(duck_curve, 0.0, 1.0)

    # Compute active RMS of voice vs bed to lock exact 10.5 dB ducking margin under speech!
    active_idx = speech_gate > 0.5
    v_rms = float(np.sqrt(np.mean(voice_stereo[active_idx] ** 2)))
    b_rms_raw = float(np.sqrt(np.mean(bed_stereo[active_idx] ** 2)))
    # Target bed RMS during speech = v_rms * 10^(-10.5 / 20) (~ -10.5 dB below voice!)
    target_ducked_rms = v_rms * (10.0 ** (-10.5 / 20.0))
    base_bed_scale = target_ducked_rms / max(b_rms_raw, 1e-6)
    # In pauses (duck_curve -> 0), allow bed to breathe up by +4.5 dB (factor 1.68x), while during speech it sits at 1.0x (-10.5 dB below voice)
    dynamic_mult = 1.68 - 0.68 * duck_curve
    bed_ducked = bed_stereo * (base_bed_scale * dynamic_mult[:, None])

    actual_duck_db = 20.0 * np.log10(
        float(np.sqrt(np.mean(voice_stereo[active_idx] ** 2)))
        / float(np.sqrt(np.mean(bed_ducked[active_idx] ** 2)))
    )
    print(f"Measured voice-to-bed RMS margin during speech: +{actual_duck_db:.2f} dB (spec: 8-12 dB)")

    raw_mix = voice_stereo + bed_ducked
    peak = float(np.max(np.abs(raw_mix)))
    if peak > 0.89:
        raw_mix *= 0.89 / peak

    pre_loudnorm_path = os.path.join(build_dir, "mix_pre_loudnorm_48k.wav")
    master_wav_path = os.path.join(build_dir, "master_audio_48k.wav")
    wavfile.write(pre_loudnorm_path, SR, np.clip(raw_mix * 32767.0, -32768, 32767).astype(np.int16))

    # Two-pass EBU R128 loudness normalization to exact -16.0 LUFS, TP <= -1.5 dBTP
    p1 = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", pre_loudnorm_path,
            "-af", "loudnorm=I=-16.0:TP=-1.5:LRA=9.0:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    m = re.search(r"\{\s*\"input_i\".*?\}", p1.stderr, re.DOTALL)
    stats = json.loads(m.group(0))
    ln_filter = (
        f"loudnorm=I=-16.0:TP=-1.5:LRA=9.0:"
        f"measured_I={stats['input_i']}:"
        f"measured_LRA={stats['input_lra']}:"
        f"measured_TP={stats['input_tp']}:"
        f"measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true:print_format=summary,"
        f"aresample=48000"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", pre_loudnorm_path,
            "-af", ln_filter,
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            master_wav_path,
        ],
        check=True,
    )

    # Verify post-master loudness
    p2 = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", master_wav_path,
            "-af", "loudnorm=I=-16.0:TP=-1.5:LRA=9.0:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    m2 = re.search(r"\{\s*\"input_i\".*?\}", p2.stderr, re.DOTALL)
    post = json.loads(m2.group(0))
    print(f"Master WAV loudness: I={post['input_i']} LUFS, TP={post['input_tp']} dBTP, LRA={post['input_lra']} LU")


if __name__ == "__main__":
    main()
