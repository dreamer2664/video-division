#!/usr/bin/env python3
"""
Procedural 48 kHz Stereo Sound Design & Original Score for KELVIN (grade-v04).
Synthesizes 60.000s (2,880,000 stereo samples) across three narrative stems:
  1. Coastal Weather & Foley Arc (harbour tide, night rain droplets, 120Hz sodium ballast hum,
     Atlantic storm surf crash, calm morning glass water)
  2. Diegetic Cut Motifs (04.0s lighthouse foghorn fifth, 12.0s relay click-on, 17.5s ferry bell L->R,
     28.0s bowed metallic crane glissando, 34.0s slow-mo wave impact, 46.0s relay click-off + dawn bell)
  3. Harmonic Score (Dm(add9) -> Bbmaj7#11 -> Gm9 -> Ebmaj9 -> Cm11 -> Abmaj9 -> A7b9 -> Dmaj9 Picardy resolution)
Then applies stereo Schroeder/FDN coastal canyon reverb + two-pass FFmpeg EBU R128 loudnorm (-16.0 LUFS, TP <= -1.5 dBTP).
"""
import json
import os
import re
import subprocess
import sys
import wave
import numpy as np
from scipy import signal

SR = 48000
DUR = 60.0
N = int(SR * DUR)


def midi_to_hz(m):
    return 440.0 * (2.0 ** ((m - 69.0) / 12.0))


def env_adsr(length, attack=0.4, decay=0.8, sustain=0.65, release=1.2):
    t = np.linspace(0.0, length / SR, length, endpoint=False, dtype=np.float32)
    tot = length / SR
    rel_start = max(attack + decay, tot - release)
    e = np.ones_like(t) * sustain
    a_mask = t < attack
    if attack > 0:
        e[a_mask] = 0.5 - 0.5 * np.cos(np.pi * t[a_mask] / attack)
    d_mask = (t >= attack) & (t < attack + decay)
    if decay > 0:
        e[d_mask] = 1.0 - (1.0 - sustain) * ((t[d_mask] - attack) / decay)
    r_mask = t >= rel_start
    if release > 0 and tot > rel_start:
        rem = np.clip((t[r_mask] - rel_start) / (tot - rel_start + 1e-6), 0.0, 1.0)
        e[r_mask] *= 0.5 + 0.5 * np.cos(np.pi * rem)
    return e


def add_stereo(mix, sig_mono, start_s, pan=0.0, gain=1.0):
    """Equal-power stereo pan (-1.0 left .. +1.0 right) with slight Haas micro-delay."""
    i0 = int(round(start_s * SR))
    if i0 >= N:
        return
    seg = sig_mono[: max(0, N - i0)]
    if len(seg) == 0:
        return
    angle = (pan + 1.0) * (np.pi / 4.0)
    gl = np.cos(angle) * gain
    gr = np.sin(angle) * gain
    mix[i0 : i0 + len(seg), 0] += seg * gl
    # Subtle 0.25 ms Haas offset on quieter side for natural width
    delay = int(abs(pan) * 14)
    if delay > 0 and pan < 0:
        end_r = min(N, i0 + delay + len(seg))
        mix[i0 + delay : end_r, 1] += seg[: end_r - (i0 + delay)] * gr
    elif delay > 0 and pan > 0:
        end_l = min(N, i0 + delay + len(seg))
        mix[i0 + delay : end_l, 0] += seg[: end_l - (i0 + delay)] * (gl * 0.15)
        mix[i0 : i0 + len(seg), 1] += seg * gr
    else:
        mix[i0 : i0 + len(seg), 1] += seg * gr


def synth_warm_pad_chord(midi_notes, dur_s, brightness=0.35, detune_cents=5.5):
    length = int(round(dur_s * SR))
    t = np.arange(length, dtype=np.float32) / SR
    out = np.zeros((length, 2), dtype=np.float32)
    # Slow tape wow/flutter
    wow = 1.0 + 0.0009 * np.sin(2 * np.pi * 0.42 * t)
    for idx, m in enumerate(midi_notes):
        f0 = midi_to_hz(m)
        for ch, sign in enumerate([-1.0, 1.0]):
            det = 2.0 ** ((sign * detune_cents * (0.6 + 0.2 * (idx % 3))) / 1200.0)
            phase = 2.0 * np.pi * f0 * det * np.cumsum(wow) / SR
            # Warm bowed/analog harmonic series
            tone = (
                1.00 * np.sin(phase)
                + 0.48 * brightness * np.sin(2.0 * phase + 0.3)
                + 0.24 * brightness * np.sin(3.0 * phase + 1.1)
                + 0.10 * (brightness ** 1.4) * np.sin(4.0 * phase)
            )
            out[:, ch] += tone / max(len(midi_notes), 1)
    env = env_adsr(length, attack=min(1.4, dur_s * 0.25), decay=1.0, sustain=0.78, release=min(1.8, dur_s * 0.32))
    out *= env[:, None]
    # Gentle low-pass warmth
    b, a = signal.butter(2, min(2600.0, 900.0 + 2400.0 * brightness) / (SR / 2), btype="low")
    out[:, 0] = signal.lfilter(b, a, out[:, 0])
    out[:, 1] = signal.lfilter(b, a, out[:, 1])
    return out


def synth_felt_piano_note(midi_note, dur_s, vel=0.7):
    length = int(round(dur_s * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f0 = midi_to_hz(midi_note)
    # Slight piano string inharmonicity
    B = 0.00018
    sig = np.zeros(length, dtype=np.float32)
    partials = [(1, 1.0), (2, 0.42 * vel), (3, 0.16 * vel), (4, 0.06 * vel), (5, 0.025 * vel)]
    for k, amp in partials:
        fk = f0 * k * np.sqrt(1.0 + B * (k ** 2))
        if fk < SR * 0.45:
            decay_rate = 1.15 + 0.45 * k + (f0 / 500.0)
            sig += amp * np.sin(2.0 * np.pi * fk * t) * np.exp(-decay_rate * t)
    # Soft felt hammer thump (18 ms low-passed transient)
    thump_env = np.exp(-t / 0.012)
    b, a = signal.butter(2, 260.0 / (SR / 2), btype="low")
    hammer = signal.lfilter(b, a, np.sin(2 * np.pi * 92.0 * t) * thump_env) * 0.16 * vel
    attack_env = 1.0 - np.exp(-t / 0.009)
    fade_out = np.clip((dur_s - t) / 0.12, 0.0, 1.0)
    return (sig * attack_env + hammer) * fade_out


def synth_foghorn(dur_s=4.2):
    """Deep resonant coastal lighthouse foghorn fifth (D2 73.42 Hz + A2 110 Hz)."""
    length = int(round(dur_s * SR))
    t = np.arange(length, dtype=np.float32) / SR
    # Slight air-pressure pitch sag at start & end
    pitch_bend = 1.0 - 0.012 * np.exp(-t / 0.25) - 0.008 * np.clip((t - (dur_s - 0.9)) / 0.9, 0.0, 1.0)
    sig = np.zeros(length, dtype=np.float32)
    for f_base, g in [(73.42, 1.0), (110.0, 0.58), (146.83, 0.35)]:
        ph = 2.0 * np.pi * f_base * np.cumsum(pitch_bend) / SR
        for h_idx, h_amp in [(1, 1.0), (2, 0.62), (3, 0.45), (4, 0.22), (5, 0.12), (6, 0.06)]:
            sig += g * h_amp * np.sin(h_idx * ph)
    b, a = signal.butter(3, 520.0 / (SR / 2), btype="low")
    sig = signal.lfilter(b, a, sig)
    env = env_adsr(length, attack=0.55, decay=0.6, sustain=0.82, release=1.45)
    return np.tanh(sig * 0.35) * env


def synth_ferry_bell(dur_s=3.4):
    """Distant bronze harbour/ferry bell (A4 + inharmonic bell partials)."""
    length = int(round(dur_s * SR))
    t = np.arange(length, dtype=np.float32) / SR
    f0 = 440.0
    modes = [(1.0, 1.0, 1.4), (2.0, 0.55, 1.9), (2.42, 0.38, 2.5), (3.01, 0.24, 3.2), (4.18, 0.14, 4.5)]
    sig = np.zeros(length, dtype=np.float32)
    for ratio, amp, dec in modes:
        sig += amp * np.sin(2.0 * np.pi * f0 * ratio * t) * np.exp(-dec * t)
    b, a = signal.butter(2, 2800.0 / (SR / 2), btype="low")
    return signal.lfilter(b, a, sig) * (1.0 - np.exp(-t / 0.004))


def synth_bowed_crane_harmonic(dur_s=5.6):
    """Eerie bowed steel harmonic swell synced to Shot 07 live colour-grade sweep."""
    length = int(round(dur_s * SR))
    t = np.arange(length, dtype=np.float32) / SR
    glide = 1.0 + 0.035 * (0.5 - 0.5 * np.cos(np.pi * np.clip(t / dur_s, 0.0, 1.0)))
    sig = np.zeros(length, dtype=np.float32)
    for f0, amp in [(130.81, 0.7), (196.0, 0.55), (311.13, 0.40), (587.33, 0.22), (880.0, 0.12)]:
        ph = 2.0 * np.pi * f0 * np.cumsum(glide) / SR
        sig += amp * np.sin(ph + 0.25 * np.sin(2 * np.pi * 3.1 * t))
    env = env_adsr(length, attack=1.6, decay=0.8, sustain=0.8, release=1.8)
    b, a = signal.butter(2, [110.0 / (SR / 2), 2400.0 / (SR / 2)], btype="band")
    return signal.lfilter(b, a, sig) * env


def stereo_reverb(stereo_in, wet=0.32):
    """Lush coastal canyon / harbour stereo Schroeder-style feedback comb + allpass network."""
    delays_ms = [(37.3, 41.1), (53.7, 58.9), (71.3, 76.1), (89.7, 95.3)]
    wet_sig = np.zeros_like(stereo_in)
    # High-cut input to reverb so tail stays warm & velvety
    b_lp, a_lp = signal.butter(2, 3400.0 / (SR / 2), btype="low")
    src = np.column_stack([
        signal.lfilter(b_lp, a_lp, stereo_in[:, 0]),
        signal.lfilter(b_lp, a_lp, stereo_in[:, 1]),
    ])
    for ch in range(2):
        acc = np.zeros(len(src), dtype=np.float32)
        for d_pair in delays_ms:
            d = int(round(d_pair[ch] * 0.001 * SR))
            g = 0.74
            # Feedforward + feedback comb via lfilter: y[n] = x[n-d] + g*y[n-d]
            b_c = np.zeros(d + 1, dtype=np.float32)
            b_c[d] = 1.0
            a_c = np.zeros(d + 1, dtype=np.float32)
            a_c[0] = 1.0
            a_c[d] = -g
            acc += signal.lfilter(b_c, a_c, src[:, ch]) * 0.25
        # Two diffusing allpass stages
        for ap_ms, ap_g in [(11.3, 0.6), (4.7, 0.6)]:
            d = int(round(ap_ms * 0.001 * SR))
            b_ap = np.zeros(d + 1, dtype=np.float32)
            b_ap[0] = -ap_g
            b_ap[d] = 1.0
            a_ap = np.zeros(d + 1, dtype=np.float32)
            a_ap[0] = 1.0
            a_ap[d] = -ap_g
            acc = signal.lfilter(b_ap, a_ap, acc)
        wet_sig[:, ch] = acc
    # Cross-blend L/R wet for wide stereo envelope
    wet_x = np.column_stack([
        0.82 * wet_sig[:, 0] + 0.18 * wet_sig[:, 1],
        0.82 * wet_sig[:, 1] + 0.18 * wet_sig[:, 0],
    ])
    return stereo_in * (1.0 - wet * 0.35) + wet_x * wet


def build_weather_and_foley(rng):
    """Continuous evolving 60s coastal environment (tide, rain droplets, sodium hum, storm wave, dawn calm)."""
    t = np.arange(N, dtype=np.float32) / SR
    amb = np.zeros((N, 2), dtype=np.float32)

    # 1. Filtered stereo harbour tide & surf across all 60s (quiet calm -> storm surge -> dawn glass tide)
    for ch in range(2):
        white = rng.standard_normal(N).astype(np.float32)
        # Pink-ish shaping
        b_p, a_p = signal.butter(1, 320.0 / (SR / 2), btype="low")
        surf_low = signal.lfilter(b_p, a_p, white)
        b_h, a_h = signal.butter(2, [350.0 / (SR / 2), 2600.0 / (SR / 2)], btype="band")
        surf_foam = signal.lfilter(b_h, a_h, white)

        # Slow wave breathing (different phase L/R for wide shore imaging)
        wave_lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.16 * t + ch * 1.1 + 0.4 * np.sin(2 * np.pi * 0.05 * t))
        # Storm intensity curve peaking 28s..45.5s, dropping at 46s
        storm_env = np.exp(-((t - 37.5) / 8.5) ** 2) * (t < 46.2)
        # Gentle constant coastal presence so there is never dead silence
        base_env = 0.22 + 0.55 * storm_env - 0.06 * (t >= 46.2)
        amb[:, ch] += (surf_low * 0.85 + surf_foam * (0.22 + 0.45 * storm_env)) * wave_lfo * base_env * 0.20

    # 2. Night rain micro-droplets on stone & glass (active 11.5s -> 46.0s)
    rain_env = np.clip((t - 11.2) / 1.8, 0.0, 1.0) * np.clip((46.2 - t) / 1.0, 0.0, 1.0)
    # Soft wet rain wash
    for ch in range(2):
        w_rain = rng.standard_normal(N).astype(np.float32)
        b_r, a_r = signal.butter(2, [1100.0 / (SR / 2), 5800.0 / (SR / 2)], btype="band")
        amb[:, ch] += signal.lfilter(b_r, a_r, w_rain) * rain_env * 0.032

    # Individual resonant raindrop pitter-patter impulses (12s..45.5s)
    n_drops = 420
    drop_times = rng.uniform(12.0, 45.6, n_drops)
    for dt in drop_times:
        dur_d = 0.035
        ld = int(dur_d * SR)
        td = np.arange(ld, dtype=np.float32) / SR
        freq_d = rng.uniform(950.0, 3400.0)
        drop_sig = np.sin(2 * np.pi * freq_d * (1.0 + 0.35 * td / dur_d) * td) * np.exp(-td / 0.006)
        add_stereo(amb, drop_sig, dt, pan=rng.uniform(-0.85, 0.85), gain=rng.uniform(0.012, 0.038))

    # 3. Subtle 120 Hz + 240 Hz Sodium Streetlamp Transformer Hum (12.0s -> 28.2s)
    hum_env = np.clip((t - 12.0) / 0.3, 0.0, 1.0) * np.clip((28.3 - t) / 0.6, 0.0, 1.0)
    hum = (0.65 * np.sin(2 * np.pi * 120.0 * t) + 0.35 * np.sin(2 * np.pi * 240.0 * t)) * hum_env * 0.014
    amb[:, 0] += hum
    amb[:, 1] += hum * 0.9

    # 4. Lamp relay click-on at 12.00s & relay click-off at 46.00s
    for click_t, gain_c in [(12.02, 0.14), (46.02, 0.12)]:
        lc = int(0.045 * SR)
        tc = np.arange(lc, dtype=np.float32) / SR
        click = (
            np.sin(2 * np.pi * 1480.0 * tc) * np.exp(-tc / 0.003)
            + 0.6 * np.sin(2 * np.pi * 420.0 * tc) * np.exp(-tc / 0.008)
        )
        add_stereo(amb, click, click_t, pan=-0.15, gain=gain_c)

    # 5. Slow-motion Atlantic wave impact at Shot 08 (34.00s) + storm swell crest at 43.2s
    for swell_t, swell_dur, swell_g in [(33.85, 5.2, 0.28), (41.8, 4.1, 0.22)]:
        ls = int(swell_dur * SR)
        ts = np.arange(ls, dtype=np.float32) / SR
        boom_noise = rng.standard_normal(ls).astype(np.float32)
        b_b, a_b = signal.butter(3, 145.0 / (SR / 2), btype="low")
        sub_boom = signal.lfilter(b_b, a_b, boom_noise) * np.exp(-((ts - 1.1) / 1.6) ** 2) * 2.2
        spray = signal.lfilter(*signal.butter(2, [700.0 / (SR / 2), 4500.0 / (SR / 2)], btype="band"), boom_noise)
        spray *= env_adsr(ls, attack=0.65, decay=1.2, sustain=0.45, release=2.2) * 0.32
        add_stereo(amb, sub_boom + spray, swell_t, pan=-0.12, gain=swell_g)
        add_stereo(amb, np.roll(sub_boom + spray, 180), swell_t, pan=0.18, gain=swell_g * 0.9)

    return amb


def build_score_and_motifs():
    """Original harmonic score & tonal diegetic motifs across all four Kelvin acts."""
    music = np.zeros((N, 2), dtype=np.float32)

    # Cut motifs
    # 04.0s: Lighthouse foghorn fifth (D2 + A2)
    horn = synth_foghorn(4.4)
    add_stereo(music, horn, 3.95, pan=0.18, gain=0.34)

    # 17.5s: Distant ferry bell drifting left -> right
    bell1 = synth_ferry_bell(3.2)
    bell2 = synth_ferry_bell(3.0)
    add_stereo(music, bell1, 17.65, pan=-0.45, gain=0.13)
    add_stereo(music, bell2, 19.35, pan=0.30, gain=0.10)

    # 28.0s: Bowed crane steel harmonic synced to live colour-grade sweep
    crane_bow = synth_bowed_crane_harmonic(5.6)
    add_stereo(music, crane_bow, 28.00, pan=-0.10, gain=0.24)

    # 46.1s: Morning crystalline bell chime (D5 + A5) opening silver dawn
    dawn_chime = synth_felt_piano_note(74, 4.5, vel=0.85) + 0.55 * synth_felt_piano_note(81, 4.2, vel=0.75)
    add_stereo(music, dawn_chime, 46.12, pan=0.12, gain=0.22)

    # Warm pad harmonic progression matching the 4 Kelvin acts:
    chords = [
        # (start_s, dur_s, midi_notes, brightness, gain)
        (0.05, 8.4, [38, 45, 57, 64], 0.26, 0.24),              # Open D5/9 twilight bed
        (7.90, 4.7, [38, 45, 52, 53, 57, 64], 0.32, 0.28),      # Dm(add9)
        (12.00, 6.1, [46, 53, 57, 60, 62, 64], 0.38, 0.30),     # Bbmaj7(#11) — 2100K Sodium warmth
        (17.50, 6.0, [43, 50, 53, 57, 58, 62], 0.36, 0.30),     # Gm9 — Ferry window
        (23.00, 5.5, [39, 46, 53, 55, 58, 62], 0.35, 0.30),     # Ebmaj9 — Prussian shadows
        (28.00, 6.5, [36, 43, 48, 51, 55, 58, 62], 0.48, 0.33), # Cm11 — 4200K Mercury crane shift
        (34.00, 6.5, [32, 39, 46, 48, 51, 56, 63], 0.56, 0.36), # Abmaj9 — Slow-motion wave crest
        (40.00, 6.0, [33, 40, 45, 55, 58, 61, 64], 0.62, 0.38), # A7(b9) — Storm watch climax, cuts at 46.0s!
        (46.05, 5.5, [38, 45, 50, 54, 57, 64], 0.45, 0.31),     # Dmaj9 — 6500K Picardy resolution!
        (51.00, 5.0, [35, 42, 50, 54, 57, 62, 64], 0.48, 0.32), # Bm11 / D6-9 — Glass water
        (55.50, 4.5, [38, 45, 50, 54, 57, 64, 66], 0.52, 0.34), # Radiant Dmaj9 final horizon hold
    ]
    for st, dur_c, notes, br, gn in chords:
        pad = synth_warm_pad_chord(notes, dur_c, brightness=br)
        i0 = int(round(st * SR))
        seg_len = min(len(pad), N - i0)
        if seg_len > 0:
            music[i0 : i0 + seg_len] += pad[:seg_len] * gn

    # Slow-motion storm sub-bass pulse in Act II-B (28.5s -> 45.2s)
    pulse_times = np.arange(28.6, 45.2, 1.25)
    for pt in pulse_times:
        lp = int(1.1 * SR)
        tp = np.arange(lp, dtype=np.float32) / SR
        f_sub = 65.41 if pt < 34.0 else (51.91 if pt < 40.0 else 55.0)
        pulse = (np.sin(2 * np.pi * f_sub * tp) + 0.35 * np.sin(4 * np.pi * f_sub * tp)) * np.exp(-tp / 0.38)
        pulse *= 1.0 - np.exp(-tp / 0.025)
        add_stereo(music, pulse, pt, pan=0.0, gain=0.19)

    # Expressive nocturnal & dawn felt-piano melody notes
    piano_events = [
        # Act I sparse questioning motif
        (1.10, 62, 3.2, 0.55, -0.18), (2.45, 64, 3.0, 0.50, 0.15),
        (8.60, 69, 2.8, 0.58, -0.20), (10.10, 65, 2.8, 0.54, 0.18),
        # Act II-A 2100K Sodium lyrical felt piano
        (12.80, 62, 3.4, 0.65, -0.22), (14.30, 64, 3.2, 0.62, 0.12), (15.85, 69, 3.2, 0.68, 0.25),
        (18.30, 67, 3.2, 0.64, -0.18), (19.95, 65, 3.0, 0.60, 0.15), (21.40, 62, 3.2, 0.62, -0.10),
        (23.80, 67, 3.0, 0.62, 0.20),  (25.30, 70, 3.0, 0.66, -0.15), (26.65, 69, 2.6, 0.58, 0.10),
        # Act II-B Storm octave accents
        (34.35, 68, 3.4, 0.75, -0.25), (36.80, 67, 3.0, 0.70, 0.22), (38.50, 63, 2.8, 0.68, -0.12),
        (40.60, 69, 3.2, 0.76, 0.18),  (42.40, 70, 2.8, 0.78, -0.20), (44.00, 73, 2.2, 0.82, 0.15),
        # Act III 6500K Silver Dawn luminous Dmaj9 arpeggio
        (47.20, 66, 3.8, 0.62, -0.22), (48.90, 69, 3.6, 0.64, 0.18),
        (51.50, 74, 3.8, 0.68, -0.16), (52.90, 76, 3.6, 0.66, 0.22), (54.20, 73, 3.4, 0.62, -0.08),
        (55.90, 66, 4.0, 0.66, -0.20), (56.55, 69, 3.4, 0.68, 0.18), (57.25, 74, 2.75, 0.72, 0.04),
    ]
    for pt, midi_n, dur_n, vel_n, pan_n in piano_events:
        note = synth_felt_piano_note(midi_n, dur_n, vel=vel_n)
        add_stereo(music, note, pt, pan=pan_n, gain=0.26)

    return stereo_reverb(music, wet=0.38)


def write_wav_float_or_pcm16(path, stereo):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    peak = np.max(np.abs(stereo)) + 1e-9
    normed = stereo / peak * 0.78
    pcm = np.clip(normed * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def master_loudnorm_two_pass(raw_wav, out_wav, target_i=-16.0, target_tp=-1.5, target_lra=11.0):
    """Exact two-pass EBU R128 loudnorm to hit -16.0 LUFS integrated and TP <= -1.5 dBTP."""
    pass1 = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", raw_wav,
            "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    m = re.search(r"\{[\s\S]*?\}", pass1.stderr)
    if not m:
        raise RuntimeError(f"Could not parse loudnorm JSON:\n{pass1.stderr}")
    stats = json.loads(m.group(0))
    af_pass2 = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true:print_format=summary,"
        f"aresample={SR}"
    )
    pass2 = subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-i", raw_wav,
            "-af", af_pass2,
            "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le",
            out_wav,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print("=== EBU R128 Two-Pass Mastering Summary ===")
    for line in pass2.stderr.splitlines()[-12:]:
        print(" ", line)


def main():
    out_wav = sys.argv[1] if len(sys.argv) > 1 else "/tmp/grade_v04_build/audio_master_48k.wav"
    raw_wav = out_wav.replace(".wav", "_pre.wav")
    rng = np.random.default_rng(20261031)

    weather = build_weather_and_foley(rng)
    music = build_score_and_motifs()
    mix = weather + music

    # Smooth 0.18s fade-in and 0.25s anti-click fade-out (strictly < 0.5s so audio stays alive to the end)
    t = np.arange(N, dtype=np.float32) / SR
    fade_in = np.clip(t / 0.18, 0.0, 1.0)
    fade_out = np.clip((DUR - t) / 0.25, 0.0, 1.0)
    mix *= (fade_in * fade_out)[:, None]

    write_wav_float_or_pcm16(raw_wav, mix)
    master_loudnorm_two_pass(raw_wav, out_wav, target_i=-16.0, target_tp=-1.6, target_lra=11.0)
    if os.path.exists(raw_wav):
        os.remove(raw_wav)
    print(f"Mastered 48kHz stereo WAV ready: {out_wav}")


if __name__ == "__main__":
    main()
