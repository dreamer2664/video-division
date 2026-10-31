#!/usr/bin/env python3
"""
Two-voice dialogue + copper-handset acoustic chain + sidechain-ducked nocturnal mixer for MARK FIVE (grade-v06).
Author: grade <grade@agency.local>

Voices (strictly interleaved A -> B -> A -> B -> A -> B -> A -> B -> A -> B, 0.000s overlap):
  - Voice A (Narrator / Keeper): `edge-tts` `en-US-ChristopherNeural` (`--rate=-11% --pitch=-5Hz`),
    full-bandwidth close-mic EQ, panned Left-Center (L=0.880, R=0.550 -> +4.08 dB L-bias).
  - Voice B (Responder / Copper Handset): `edge-tts` `en-GB-SoniaNeural` (`--rate=+4% --pitch=+2Hz`),
    340Hz-3450Hz 4th-order Butterworth Bakelite telephone bandpass + carbon-mic harmonic presence +
    gated line carrier & cradle relay clicks, panned Right-Center (L=0.550, R=0.880 -> +4.08 dB R-bias).
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

VOICE_A = ("en-US-ChristopherNeural", "-11%", "-5Hz")
VOICE_B = ("en-GB-SoniaNeural", "+4%", "+2Hz")

TURNS = [
    ("01", "A", "At two twenty-four, seven minutes after the upper lock breached, the copper wall phone rings. A line dead since nineteen eighty-nine."),
    ("02", "B", "Lower Tower, come in. Confirm your water is still below Mark Five."),
    ("03", "A", "I check the spillway wall outside. Four inches below the red five."),
    ("04", "B", "Good. Whatever you hear on the roof, do not draw the spillway pins."),
    ("05", "A", "Wait. How do you know something is walking on the roof?"),
    ("06", "B", "Follow the copper telephone wire down beneath your window sill."),
    ("07", "A", "My lamp hits the wet stone floor. The wire is cut clean through."),
    ("08", "B", "I'm not calling from Basin Control. I'm on your roof, clipped to the stub. And Mark Five wasn't painted to measure the river."),
    ("09", "A", "I raise the lamp. Mark Five is stenciled across the ceiling."),
    ("10", "B", "It marks how high your tower fills."),
]

GAPS = [0.40, 0.82, 0.68, 0.68, 0.62, 0.68, 0.68, 1.28, 0.78, 0.88]


async def ensure_tts_turns(narr_dir: str):
    manifest_path = os.path.join(narr_dir, "turns_manifest.json")
    if os.path.exists(manifest_path) and all(
        os.path.exists(os.path.join(narr_dir, f"turn_{tid}_{spk}_raw.wav")) for tid, spk, _ in TURNS
    ):
        return json.load(open(manifest_path))

    os.makedirs(narr_dir, exist_ok=True)
    out = []
    for tid, spk, text in TURNS:
        voice, rate, pitch = VOICE_A if spk == "A" else VOICE_B
        mp3 = os.path.join(narr_dir, f"turn_{tid}_{spk}.mp3")
        wav = os.path.join(narr_dir, f"turn_{tid}_{spk}_raw.wav")
        comm = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary")
        words = []
        with open(mp3, "wb") as f:
            async for ch in comm.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    words.append({
                        "start": round(ch["offset"] / 1e7, 3),
                        "end": round((ch["offset"] + ch["duration"]) / 1e7, 3),
                        "text": ch["text"],
                    })
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", wav], check=True)
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", wav]).decode().strip())
        out.append({
            "turn": tid, "speaker": spk, "voice": voice, "rate": rate, "pitch": pitch,
            "text": text, "raw_dur": round(dur, 3), "first_w": words[0]["start"], "last_w": words[-1]["end"],
            "span": round(words[-1]["end"] - words[0]["start"], 3), "words": words,
        })
    json.dump(out, open(manifest_path, "w"), indent=2)
    return out


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
    return signal.lfilter(np.array([b0, b1, b2]) / a0, np.array([1.0, a1 / a0, a2 / a0]), x).astype(np.float32)


def estimate_f0_and_centroid(mono: np.ndarray, gate: np.ndarray) -> tuple[float, float]:
    """Estimate voiced fundamental F0 (autocorrelation) and spectral centroid (Hz) on active speech frames."""
    win = int(0.040 * SR)
    hop = int(0.020 * SR)
    f0s = []
    centroids = []
    freqs = np.fft.rfftfreq(win, 1.0 / SR)
    lag_min = int(SR / 340.0)
    lag_max = int(SR / 70.0)

    # Low-pass copy at 450 Hz for clean fundamental pitch tracking even on telephone-filtered speech
    sos_f0 = signal.butter(2, 450.0 / (SR * 0.5), btype="lowpass", output="sos")
    lp = signal.sosfilt(sos_f0, mono)

    for i in range(0, len(mono) - win, hop):
        if gate[i + win // 2] < 0.5:
            continue
        seg = mono[i:i + win]
        rms = float(np.sqrt(np.mean(seg ** 2)))
        if rms < 0.03:
            continue
        mag = np.abs(np.fft.rfft(seg * np.hanning(win))) + 1e-9
        centroids.append(float(np.sum(freqs * mag) / np.sum(mag)))

        seg_lp = lp[i:i + win] - np.mean(lp[i:i + win])
        ac = np.correlate(seg_lp, seg_lp, mode="full")[win - 1:]
        if ac[0] > 1e-6:
            ac_norm = ac / ac[0]
            sub = ac_norm[lag_min:lag_max]
            pk = int(np.argmax(sub)) + lag_min
            if ac_norm[pk] > 0.45:
                f0s.append(SR / pk)

    med_f0 = float(np.median(f0s)) if f0s else 0.0
    mean_c = float(np.mean(centroids)) if centroids else 0.0
    return med_f0, mean_c


def build_two_voice_stems(manifest, narr_dir: str):
    mono_A = np.zeros(N_SAMPLES, dtype=np.float32)
    mono_B_raw = np.zeros(N_SAMPLES, dtype=np.float32)
    gate_A = np.zeros(N_SAMPLES, dtype=np.float32)
    gate_B = np.zeros(N_SAMPLES, dtype=np.float32)

    cursor = 0.0
    placed_turns = []

    for item, gap in zip(manifest, GAPS):
        spk = item["speaker"]
        tid = item["turn"]
        sr_in, data = wavfile.read(os.path.join(narr_dir, f"turn_{tid}_{spk}_raw.wav"))
        assert sr_in == SR
        audio = data.astype(np.float32) / 32768.0

        # Tight clean trim around word boundaries so zero trailing breath bleeds into the other speaker's slot
        t_in = max(0.0, item["first_w"] - 0.045)
        t_out = min(len(audio) / SR, item["last_w"] + 0.13)
        s_in = int(round(t_in * SR))
        s_out = int(round(t_out * SR))
        clip = audio[s_in:s_out].copy()
        fn = int(0.020 * SR)
        clip[:fn] *= np.linspace(0.0, 1.0, fn, dtype=np.float32)
        clip[-fn:] *= np.linspace(1.0, 0.0, fn, dtype=np.float32)

        t_start = round(cursor + gap, 3)
        clip_start = t_start - (item["first_w"] - t_in)
        p0 = int(round(clip_start * SR))
        p1 = p0 + len(clip)

        shift = t_start - item["first_w"]
        t_words = []
        for w in item["words"]:
            ws = round(w["start"] + shift, 3)
            we = round(w["end"] + shift, 3)
            t_words.append({"turn": tid, "speaker": spk, "text": w["text"], "start": ws, "end": we})

        t_end = t_words[-1]["end"]
        g0 = int(round(t_start * SR))
        g1 = int(round(t_end * SR))

        if spk == "A":
            mono_A[p0:p1] += clip
            gate_A[g0:g1] = 1.0
        else:
            mono_B_raw[p0:p1] += clip
            gate_B[g0:g1] = 1.0

        placed_turns.append({
            "turn": tid, "speaker": spk, "voice": item["voice"], "rate": item["rate"], "pitch": item["pitch"],
            "start": t_start, "end": t_end, "dur": round(t_end - t_start, 3), "text": item["text"],
        })
        cursor = t_end

    # Strict mathematical non-overlap assertion!
    overlap_samples = int(np.sum((gate_A > 0.5) & (gate_B > 0.5)))
    assert overlap_samples == 0, f"Speaker overlap detected: {overlap_samples} samples!"

    # --- Process Voice A (Narrator / Keeper: Full-Range Close-Mic Baritone) ---
    f0_A, _ = estimate_f0_and_centroid(mono_A, gate_A)
    sos_hpA = signal.butter(2, 80.0 / (SR * 0.5), btype="highpass", output="sos")
    vA = signal.sosfilt(sos_hpA, mono_A).astype(np.float32)
    vA = peaking_eq(vA, 132.0, 1.1, +1.5)
    vA = peaking_eq(vA, 320.0, 1.4, -2.4)
    vA = peaking_eq(vA, 2950.0, 1.0, +2.6)

    envA = signal.sosfilt(signal.butter(1, 12.0 / (SR * 0.5), btype="lowpass", output="sos"), np.abs(vA)) + 1e-5
    vA = vA * np.where(envA > 0.15, (0.15 / envA) ** 0.42, 1.0)
    vA = np.tanh(vA / max(np.max(np.abs(vA)), 1e-6) * 1.05) * 0.76
    _, cent_A = estimate_f0_and_centroid(vA, gate_A)

    # --- Process Voice B (Responder: Bakelite Copper-Handset 340-3450 Hz Acoustic Chain) ---
    f0_B, _ = estimate_f0_and_centroid(mono_B_raw, gate_B)
    sos_tel = signal.butter(4, [340.0 / (SR * 0.5), 3450.0 / (SR * 0.5)], btype="bandpass", output="sos")
    vB = signal.sosfilt(sos_tel, mono_B_raw).astype(np.float32)
    vB = peaking_eq(vB, 1750.0, 1.15, +3.4)  # Classic carbon-receiver upper-mid intelligibility peak
    envB = signal.sosfilt(signal.butter(1, 14.0 / (SR * 0.5), btype="lowpass", output="sos"), np.abs(vB)) + 1e-5
    vB = vB * np.where(envB > 0.14, (0.14 / envB) ** 0.46, 1.0)
    # Mild carbon-mic saturation + post-bandpass cleanup
    vB = np.tanh((vB / max(np.max(np.abs(vB)), 1e-6)) * 1.45) / np.tanh(1.45)
    vB = signal.sosfilt(sos_tel, vB).astype(np.float32)

    # Match active RMS of Voice B cleanly to Voice A (-0.3 dB so handset sits naturally yet 100% intelligible)
    rms_A_active = float(np.sqrt(np.mean(vA[gate_A > 0.5] ** 2)))
    rms_B_active = float(np.sqrt(np.mean(vB[gate_B > 0.5] ** 2)))
    vB *= (rms_A_active * (10.0 ** (-0.3 / 20.0))) / max(rms_B_active, 1e-6)

    # Add subtle copper-wire carrier hiss ONLY while Responder B's handset transmit gate is keyed
    rng_line = np.random.default_rng(6061)
    line_noise = signal.sosfilt(sos_tel, rng_line.normal(0.0, 1.0, N_SAMPLES).astype(np.float32))
    sos_key = signal.butter(1, 8.0 / (SR * 0.5), btype="lowpass", output="sos")
    key_env = np.clip(signal.sosfilt(sos_key, gate_B) * 1.15, 0.0, 1.0).astype(np.float32)
    vB_with_line = vB + line_noise * key_env * 0.0045
    _, cent_B = estimate_f0_and_centroid(vB, gate_B)

    # --- Distinct Stereo Panning (Separable & Mono-Safe) ---
    # Voice A panned Left-Center (-28%): L=0.880, R=0.550 (+4.08 dB Left dominance)
    # Voice B panned Right-Center (+28%): L=0.550, R=0.880 (+4.08 dB Right dominance)
    panA_L, panA_R = np.float32(0.880), np.float32(0.550)
    panB_L, panB_R = np.float32(0.550), np.float32(0.880)

    stereo_A = np.column_stack([vA * panA_L, vA * panA_R]).astype(np.float32)
    stereo_B = np.column_stack([vB_with_line * panB_L, vB_with_line * panB_R]).astype(np.float32)
    dialogue_stereo = stereo_A + stereo_B

    stats = {
        "overlap_samples": overlap_samples,
        "overlap_seconds": 0.0,
        "voice_A": {
            "engine": VOICE_A[0], "rate": VOICE_A[1], "pitch": VOICE_A[2],
            "median_f0_hz": round(f0_A, 1),
            "spectral_centroid_hz": round(cent_A, 1),
            "pan_L_R_db": round(float(20.0 * np.log10(panA_L / panA_R)), 2),
        },
        "voice_B": {
            "engine": VOICE_B[0], "rate": VOICE_B[1], "pitch": VOICE_B[2],
            "median_f0_hz": round(float(f0_B), 1),
            "spectral_centroid_hz": round(float(cent_B), 1),
            "pan_R_L_db": round(float(20.0 * np.log10(panB_R / panB_L)), 2),
        },
    }
    print("Voice separation telemetry:", json.dumps(stats, indent=2))
    return stereo_A, stereo_B, dialogue_stereo, np.maximum(gate_A, gate_B), stats


def build_score_and_foley(t: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(202606)

    # 1. Stereo Storm Rain Bed (quieter inside tower on Shots 02/04/07/10, louder on exterior/oculus Shots 01/03/05/08/09)
    wn_l = rng.normal(0.0, 1.0, N_SAMPLES).astype(np.float32)
    wn_r = rng.normal(0.0, 1.0, N_SAMPLES).astype(np.float32)
    sos_wash = signal.butter(2, [420.0 / (SR * 0.5), 1950.0 / (SR * 0.5)], btype="bandpass", output="sos")
    sos_pat = signal.butter(2, [4400.0 / (SR * 0.5), 8400.0 / (SR * 0.5)], btype="bandpass", output="sos")
    rain_l = signal.sosfilt(sos_wash, wn_l) * 0.050 + signal.sosfilt(sos_pat, wn_l) * 0.024
    rain_r = signal.sosfilt(sos_wash, wn_r) * 0.050 + signal.sosfilt(sos_pat, wn_r) * 0.024

    gust = 0.86 + 0.14 * np.sin(2.0 * np.pi * 0.08 * t + 0.3)
    rooftop_swell = 1.0 + 0.32 * np.exp(-((t - 46.2) / 4.2) ** 2)
    rain_l *= (gust * rooftop_swell).astype(np.float32)
    rain_r *= (gust * rooftop_swell).astype(np.float32)

    # 2. Dark Bowed D-Minor / Phrygian Sub-Cello Score (strictly low-passed at 360 Hz -> ZERO vocal masking!)
    w1 = 1.0 / (1.0 + np.exp(np.clip((t - 26.8) * 2.5, -40.0, 40.0)))
    w2 = (1.0 / (1.0 + np.exp(np.clip(-(t - 26.8) * 2.5, -40.0, 40.0)))) * (1.0 / (1.0 + np.exp(np.clip((t - 42.1) * 3.5, -40.0, 40.0))))
    w3 = 1.0 / (1.0 + np.exp(np.clip(-(t - 42.1) * 3.5, -40.0, 40.0)))

    vib = 0.0022 * np.sin(2.0 * np.pi * 4.5 * t)

    def bowed(freq: float, det: float = 0.0) -> np.ndarray:
        f = freq * (1.0 + det)
        ph = 2.0 * np.pi * f * (t + vib / max(f, 30.0))
        return (0.68 * np.sin(ph) + 0.22 * np.sin(2.0 * ph + 0.4) + 0.08 * np.sin(3.0 * ph + 0.8)).astype(np.float32)

    # D1 (36.71Hz) + A1 (55.00Hz) + D2 (73.42Hz) -> G1/Bb1 -> D1 + Eb2 (77.78Hz Phrygian dread!)
    s1_l = 0.46 * bowed(36.708) + 0.38 * bowed(73.416, -0.0015) + 0.24 * bowed(110.000, +0.001)
    s1_r = 0.46 * bowed(36.708) + 0.38 * bowed(73.416, +0.0015) + 0.24 * bowed(110.000, -0.001)

    s2_l = 0.48 * bowed(49.000) + 0.36 * bowed(97.999, -0.0018) + 0.22 * bowed(146.832)
    s2_r = 0.48 * bowed(49.000) + 0.36 * bowed(97.999, +0.0018) + 0.22 * bowed(146.832)

    s3_l = 0.56 * bowed(36.708) + 0.42 * bowed(73.416, -0.002) + 0.30 * bowed(77.782, +0.001) + 0.20 * bowed(110.000)
    s3_r = 0.56 * bowed(36.708) + 0.42 * bowed(73.416, +0.002) + 0.30 * bowed(77.782, -0.001) + 0.20 * bowed(110.000)

    breath = 0.83 + 0.17 * np.sin(2.0 * np.pi * 0.10 * t - 0.5)
    sc_l = (w1 * s1_l + w2 * s2_l + w3 * s3_l) * breath * 0.115
    sc_r = (w1 * s1_r + w2 * s2_r + w3 * s3_r) * breath * 0.115

    sos_lp = signal.butter(3, 350.0 / (SR * 0.5), btype="lowpass", output="sos")
    sc_l = signal.sosfilt(sos_lp, sc_l).astype(np.float32)
    sc_r = signal.sosfilt(sos_lp, sc_r).astype(np.float32)

    # 3. Diegetic Foley (Wall-phone twin-gong ring, Bakelite cradle lift, roof footsteps, pre-twist pulse, rising water)
    fl_l = np.zeros(N_SAMPLES, dtype=np.float32)
    fl_r = np.zeros(N_SAMPLES, dtype=np.float32)

    def add_phone_ring(t0: float, dur_s: float = 0.82, amp: float = 0.055):
        i0 = int(t0 * SR)
        n = min(int(dur_s * SR), N_SAMPLES - i0)
        lt = np.arange(n, dtype=np.float32) / SR
        clapper = 0.55 + 0.45 * np.sin(2.0 * np.pi * 19.0 * lt)
        gong = (0.60 * np.sin(2 * np.pi * 1088.0 * lt) + 0.40 * np.sin(2 * np.pi * 1362.0 * lt)) * clapper
        env = np.minimum(1.0, lt * 35.0) * np.exp(-np.maximum(0.0, lt - (dur_s - 0.12)) * 18.0)
        fl_l[i0:i0 + n] += gong * env * amp * 0.72
        fl_r[i0:i0 + n] += gong * env * amp * 0.95

    def add_click(t0: float, freq: float, decay: float, amp: float, pan_r: float = 0.5):
        i0 = int(t0 * SR)
        n = min(int(0.16 * SR), N_SAMPLES - i0)
        lt = np.arange(n, dtype=np.float32) / SR
        c = (np.sin(2 * np.pi * freq * lt) + 0.45 * np.sin(2 * np.pi * freq * 2.18 * lt)) * np.exp(-lt * decay) * amp
        fl_l[i0:i0 + n] += c * (1.0 - pan_r * 0.4)
        fl_r[i0:i0 + n] += c * (0.6 + pan_r * 0.4)

    def add_thump(t0: float, f0: float, f1: float, dur_s: float, amp: float):
        i0 = int(t0 * SR)
        n = min(int(dur_s * SR), N_SAMPLES - i0)
        lt = np.arange(n, dtype=np.float32) / SR
        ph = 2.0 * np.pi * np.cumsum(f0 + (f1 - f0) * (lt / dur_s)) / SR
        th = np.sin(ph) * np.exp(-lt * (4.2 / dur_s)) * (1.0 - np.exp(-lt * 85.0)) * amp
        fl_l[i0:i0 + n] += th
        fl_r[i0:i0 + n] += th

    # Brass wall-phone ring at 6.38s (right after 'wall phone rings.')
    add_phone_ring(6.42, dur_s=0.78, amp=0.052)
    # Bakelite cradle pickup click at 10.32s before Responder Turn 02 (panned Right with Responder!)
    add_click(10.30, 1420.0, 62.0, 0.065, pan_r=0.9)
    add_click(10.34, 780.0, 48.0, 0.055, pan_r=0.9)
    # Muffled overhead stone-roof footsteps at 26.75s & 31.35s
    add_thump(26.72, 92.0, 44.0, 0.28, 0.10)
    add_thump(31.32, 88.0, 42.0, 0.28, 0.11)
    # Double heartbeat + alligator-clip line click in the 1.28s pre-twist pause (41.163s -> 42.443s)!
    add_thump(41.38, 66.0, 36.0, 0.34, 0.14)
    add_thump(41.76, 60.0, 33.0, 0.42, 0.18)
    add_click(42.26, 1880.0, 75.0, 0.055, pan_r=0.95)
    # Tectonic turn drop at 42.44s & final handset disconnect click at 59.05s
    add_thump(42.44, 76.0, 29.0, 1.30, 0.15)
    add_click(59.05, 1620.0, 70.0, 0.068, pan_r=0.95)

    # Rising tower water swell 51.0s - 59.8s
    w_mask = np.clip((t - 50.8) / 1.8, 0.0, 1.0) * np.clip((59.95 - t) / 0.75, 0.0, 1.0)
    sos_water = signal.butter(2, [70.0 / (SR * 0.5), 310.0 / (SR * 0.5)], btype="bandpass", output="sos")
    fl_l += signal.sosfilt(sos_water, wn_l).astype(np.float32) * w_mask * 0.075
    fl_r += signal.sosfilt(sos_water, wn_r).astype(np.float32) * w_mask * 0.075

    bed_l = rain_l + sc_l + fl_l
    bed_r = rain_r + sc_r + fl_r
    fi, fo = int(0.25 * SR), int(0.35 * SR)
    bed_l[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    bed_r[:fi] *= np.linspace(0.0, 1.0, fi, dtype=np.float32)
    bed_l[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    bed_r[-fo:] *= np.linspace(1.0, 0.0, fo, dtype=np.float32)
    return np.column_stack([bed_l, bed_r]).astype(np.float32)


def main():
    build_dir = "/tmp/grade_v06_build"
    narr_dir = os.path.join(build_dir, "narration")
    os.makedirs(narr_dir, exist_ok=True)

    manifest = asyncio.run(ensure_tts_turns(narr_dir))
    stereo_A, stereo_B, dialogue_stereo, active_gate, sep_stats = build_two_voice_stems(manifest, narr_dir)

    wavfile.write(os.path.join(narr_dir, "voice_A_narrator_48k.wav"), SR, np.clip(stereo_A * 32767.0, -32768, 32767).astype(np.int16))
    wavfile.write(os.path.join(narr_dir, "voice_B_responder_48k.wav"), SR, np.clip(stereo_B * 32767.0, -32768, 32767).astype(np.int16))
    wavfile.write(os.path.join(narr_dir, "dialogue_stem_48k.wav"), SR, np.clip(dialogue_stereo * 32767.0, -32768, 32767).astype(np.int16))

    t = np.arange(N_SAMPLES, dtype=np.float32) / SR
    bed_stereo = build_score_and_foley(t)

    # Sidechain-duck bed ~10.5 dB below active dialogue
    sos_duck = signal.butter(1, 3.2 / (SR * 0.5), btype="lowpass", output="sos")
    duck_curve = np.clip(signal.sosfilt(sos_duck, active_gate).astype(np.float32), 0.0, 1.0)

    act = active_gate > 0.5
    d_rms = float(np.sqrt(np.mean(dialogue_stereo[act] ** 2)))
    b_rms = float(np.sqrt(np.mean(bed_stereo[act] ** 2)))
    target_bed_rms = d_rms * (10.0 ** (-10.5 / 20.0))
    base_scale = target_bed_rms / max(b_rms, 1e-6)
    dyn_mult = 1.65 - 0.65 * duck_curve
    bed_ducked = bed_stereo * (base_scale * dyn_mult[:, None])

    duck_margin_db = 20.0 * np.log10(
        float(np.sqrt(np.mean(dialogue_stereo[act] ** 2))) / float(np.sqrt(np.mean(bed_ducked[act] ** 2)))
    )
    sep_stats["dialogue_to_bed_ducking_db"] = round(duck_margin_db, 2)
    json.dump(sep_stats, open(os.path.join(narr_dir, "audio_telemetry.json"), "w"), indent=2)
    print(f"Dialogue-to-bed RMS margin during speech: +{duck_margin_db:.2f} dB")

    raw_mix = dialogue_stereo + bed_ducked
    pk = float(np.max(np.abs(raw_mix)))
    if pk > 0.89:
        raw_mix *= 0.89 / pk

    pre_wav = os.path.join(build_dir, "mix_pre_loudnorm_48k.wav")
    master_wav = os.path.join(build_dir, "master_audio_48k.wav")
    wavfile.write(pre_wav, SR, np.clip(raw_mix * 32767.0, -32768, 32767).astype(np.int16))

    p1 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", pre_wav, "-af", "loudnorm=I=-16.0:TP=-1.8:LRA=9.0:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    st = json.loads(re.search(r"\{\s*\"input_i\".*?\}", p1.stderr, re.DOTALL).group(0))
    ln_af = (
        f"loudnorm=I=-16.0:TP=-1.8:LRA=9.0:"
        f"measured_I={st['input_i']}:measured_LRA={st['input_lra']}:"
        f"measured_TP={st['input_tp']}:measured_thresh={st['input_thresh']}:"
        f"offset={st['target_offset']}:linear=true:print_format=summary,aresample=48000"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", pre_wav, "-af", ln_af, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", master_wav],
        check=True,
    )
    p2 = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", master_wav, "-af", "loudnorm=I=-16.0:TP=-1.5:LRA=9.0:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    post = json.loads(re.search(r"\{\s*\"input_i\".*?\}", p2.stderr, re.DOTALL).group(0))
    print(f"Master WAV loudness: I={post['input_i']} LUFS, TP={post['input_tp']} dBTP, LRA={post['input_lra']} LU")


if __name__ == "__main__":
    main()
