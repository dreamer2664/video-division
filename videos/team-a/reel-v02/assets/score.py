#!/usr/bin/env python3
"""Original 'Waiting has a curve' score. Every sound is synthesized; fixed seed.

60 s at 112 BPM: evolving D minor electronic underscore with a resolved ending.
Writes 48 kHz stereo, 16-bit PCM WAV. CC0 1.0 by reel.
"""
import math
import sys
import wave
import numpy as np

SR = 48_000
DURATION = 60.0
N = round(SR * DURATION)
BEAT = 60.0 / 112.0
rng = np.random.default_rng(20261031)
left = np.zeros(N, dtype=np.float32)
right = np.zeros(N, dtype=np.float32)


def mix(start, samples, amp=1.0, pan=0.0):
    i = round(start * SR)
    if i >= N:
        return
    a = max(0, -i)
    i = max(0, i)
    n = min(len(samples) - a, N - i)
    if n <= 0:
        return
    # Equal-power stereo placement.
    theta = (max(-1.0, min(1.0, pan)) + 1.0) * math.pi / 4.0
    left[i:i+n] += samples[a:a+n] * np.float32(amp * math.cos(theta))
    right[i:i+n] += samples[a:a+n] * np.float32(amp * math.sin(theta))


def note(start, duration, frequency, amp, kind='pluck', pan=0.0):
    t = np.arange(round(duration * SR), dtype=np.float32) / SR
    if kind == 'pad':
        attack = np.minimum(1.0, t / 0.65)
        release = np.minimum(1.0, np.maximum(0.0, (duration - t) / 0.85))
        env = attack * release
        phase = 2 * np.pi * frequency * t
        signal = np.sin(phase) + .15 * np.sin(phase * 2.01) + .08 * np.sin(phase * 3.0)
    elif kind == 'bass':
        env = np.minimum(1.0, t / .018) * np.exp(-t / .65)
        phase = 2 * np.pi * frequency * t
        signal = np.sin(phase) + .17 * np.sin(phase * 2.0)
    else:
        # Soft struck-glass tone, with decaying overtones.
        env = np.minimum(1.0, t / .012) * np.exp(-t / .46)
        phase = 2 * np.pi * frequency * t
        signal = (np.sin(phase) + .28 * np.sin(phase * 2.003) * np.exp(-t / .25)
                  + .09 * np.sin(phase * 3.01) * np.exp(-t / .12))
    mix(start, (signal * env).astype(np.float32), amp, pan)


def kick(start, amp):
    t = np.arange(round(.24 * SR), dtype=np.float32) / SR
    # Rapidly dropping frequency, no recording or sample.
    phase = 2*np.pi*(48*t + 70*.023*(1-np.exp(-t/.023)))
    sig = np.sin(phase) * np.exp(-t/.075)
    mix(start, sig.astype(np.float32), amp, 0)


def hat(start, amp, pan):
    t = np.arange(round(.075 * SR), dtype=np.float32) / SR
    noise = rng.standard_normal(t.size).astype(np.float32)
    # A differentiated noise signal provides a dry, bright hi-hat.
    noise[1:] = (noise[1:] - noise[:-1]) * .50
    mix(start, noise * np.exp(-t/.012), amp, pan)


def snare(start, amp):
    t = np.arange(round(.15 * SR), dtype=np.float32) / SR
    noise = rng.standard_normal(t.size).astype(np.float32)
    sig = (.65 * noise * np.exp(-t/.027) + .35 * np.sin(2*np.pi*180*t)*np.exp(-t/.055))
    mix(start, sig, amp, .08)


def swell(start, duration, amp, reverse=False):
    t = np.arange(round(duration * SR), dtype=np.float32) / SR
    noise = rng.standard_normal(t.size).astype(np.float32)
    # Smooth the noise: a gentle broadband riser, not a borrowed effect.
    noise = np.convolve(noise, np.ones(12, dtype=np.float32)/12, mode='same')
    env = (t/duration if reverse else 1-t/duration) ** 1.7
    mix(start, noise * env, amp, -.12)

# Chords are changed as a 28-bar composition, not a pre-existing music loop.
chords = [
    [146.832, 174.614, 220.000, 329.628],   # Dm add 9
    [116.541, 146.832, 174.614, 220.000],   # Bb maj 7
    [130.813, 164.814, 195.998, 293.665],   # C add 9
    [130.813, 174.614, 220.000, 329.628],   # F maj 7 / C
    [146.832, 174.614, 220.000, 329.628],
    [116.541, 146.832, 174.614, 220.000],
    [130.813, 164.814, 195.998, 293.665],
    [146.832, 174.614, 220.000, 293.665],
    [116.541, 146.832, 174.614, 220.000],
    [130.813, 164.814, 195.998, 293.665],
    [146.832, 174.614, 220.000, 329.628],
    [116.541, 146.832, 174.614, 220.000],
    [130.813, 164.814, 195.998, 293.665],
    [146.832, 174.614, 220.000, 293.665],
]
for ci, chord in enumerate(chords):
    start = ci * 8 * BEAT
    duration = min(8.8 * BEAT, DURATION-start)
    for j, freq in enumerate(chord):
        note(start, duration, freq, .085 if j < 3 else .055, 'pad', (-.5 + j/3))
    # Bass develops as the system fills, then simplifies for the ending.
    for beat_no in ([0, 4] if start < 50 else [0]):
        note(start + beat_no*BEAT, BEAT*1.6, chord[0]/2, .22, 'bass', -.05)

# An evolving, generated arpeggio; notes and rests differ by section.
for eighth in range(int(DURATION / (BEAT/2))):
    time = eighth * BEAT/2
    if time < 3.0 or time > 56.5:
        continue
    chord = chords[min(len(chords)-1, int(time/(8*BEAT)))]
    section = int(time / 8.0)
    pattern = ([0,2,1,3,2,1,3,1], [0,1,2,3,1,2,3,2],
               [0,2,3,1,2,3,1,2], [0,3,2,1,3,2,1,2])[section % 4]
    if (eighth + section) % (5 if time < 29 else 7) == 0:
        continue
    freq = chord[pattern[eighth % len(pattern)]] * (2 if eighth % 8 in (3, 6) else 1)
    amp = .090 if time < 21 else (.115 if time < 49 else .078)
    note(time, .65, freq, amp, 'pluck', -.5 if eighth % 2 else .5)

# Restrained rhythm with deliberate build and thinning.
for bi in range(int(DURATION / BEAT)):
    time = bi * BEAT
    if 3.5 <= time < 55:
        kick(time, .24 if bi % 4 == 0 else (.13 if bi % 4 == 2 else .04))
        if bi % 4 in (1, 3) and 10 < time < 51:
            snare(time, .09)
        if time > 12:
            hat(time, .055, -.35)
            if time > 20:
                hat(time + BEAT/2, .032, .40)

# Scene punctuation uses synthesized noise and a short tuned accent.
for cut in [6, 13, 21, 29, 39, 49, 56]:
    swell(cut-.5, .5, .06, reverse=True)
    note(cut, .65, 587.33 if cut != 56 else 440.0, .085, 'pluck', .1)

# Resolve the ending rather than looping out.
for j, freq in enumerate([146.832, 220.0, 293.665, 349.228]):
    note(56.2 + j*.13, 3.7-j*.13, freq, .11, 'pad', -.45+j*.3)

fade_in = np.minimum(1, np.arange(N, dtype=np.float32) / (SR*.35))
fade_out = np.minimum(1, np.arange(N, 0, -1, dtype=np.float32) / (SR*1.25))
left *= fade_in * fade_out
right *= fade_in * fade_out
peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))), .001)
gain = .73 / peak
stereo = np.empty((N, 2), dtype=np.int16)
stereo[:, 0] = np.rint(np.clip(left * gain, -1, 1) * 32767).astype(np.int16)
stereo[:, 1] = np.rint(np.clip(right * gain, -1, 1) * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo.tobytes())
print('Score synthesized: 60.000 s, 48000 Hz stereo PCM; fixed seed 20261031.', file=sys.stderr)
