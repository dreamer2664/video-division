#!/usr/bin/env python3
"""
voice.py — narration synthesis, trimming and placement for v06 "IT ANSWERED".

Engine: edge-tts, voice en-US-ChristopherNeural, rate -12%, pitch -4 Hz.

edge-tts pads every line with ~0.2 s lead-in and 0.7-1.1 s of trailing silence. Left in, a
one-word line measures 1.87 s and the timeline inflates by 20 s. So each line's real speech
bounds are measured with silencedetect and cut to them (80 ms head, 100 ms tail kept), then the
lines are packed sequentially with a written pause between each — the pauses are the performance.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

VOICE = "en-US-ChristopherNeural"
RATE = "-12%"
PITCH = "-4Hz"

HERE = Path(__file__).resolve().parent
OUT = HERE / "work"
LINES_DIR = OUT / "lines"
TRIMMED = OUT / "trim"

FILM_LEN = 60.0
HEAD, TAIL = 0.08, 0.10

LINES = [
    (1,  "It's two fourteen in the morning.",                  0.40),
    (2,  "There is one smart speaker in this flat.",           0.70),
    (3,  "One.",                                               0.55),
    (4,  "It has never been told my name.",                    0.85),
    (5,  "It said my name.",                                   0.70),
    (6,  "So I made a rule.",                                  0.90),
    (7,  "I don't answer it.",                                 0.60),
    (8,  "One speaker.",                                       0.95),
    (9,  "One flat.",                                          0.25),
    (10, "One person.",                                        0.25),
    (11, "That's the whole count.",                            0.45),
    (12, "Then it started answering things I only thought.",    0.95),
    (13, "A question I didn't say out loud.",                   0.55),
    (14, "Answered. In my own words.",                          0.40),
    (15, "I checked the microphone.",                           1.10),
    (16, "It was switched off.",                                0.35),
    (17, "So it was never the microphone.",                     0.60),
    (18, "It only ever heard one voice in here.",               2.00),
    (19, "Mine.",                                               0.30),
    (20, "It didn't learn what I thought.",                     1.60),
    (21, "It learned the phrase I say when I'm alone.",         0.45),
]


def sh(args):
    return subprocess.run(args, capture_output=True, text=True)


def synth(idx, text, path):
    for attempt in (1, 2, 3):
        r = sh(["edge-tts", "--voice", VOICE, f"--rate={RATE}", f"--pitch={PITCH}",
                "--text", text, "--write-media", str(path)])
        if path.exists() and path.stat().st_size > 1000:
            return
        print(f"  attempt {attempt} failed (line {idx}): {r.stderr.strip()[:160]}")
    raise RuntimeError(f"edge-tts failed for line {idx}: {text!r}")


def duration(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(path)])
    return float(r.stdout.strip())


def speech_bounds(path):
    total = duration(path)
    r = sh(["ffmpeg", "-v", "info", "-i", str(path), "-af", "silencedetect=n=-45dB:d=0.12",
            "-f", "null", "-"])
    txt = r.stderr
    # parse by regex: the log line carries a "[silencedetect @ 0x...]" prefix that shifts fields
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([0-9.]+)", txt)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*([0-9.]+)", txt)]
    s = ends[0] if (starts and starts[0] < 0.02 and ends) else 0.0
    e = total
    if starts:
        last = max(starts)
        if last > s and (total - last) > 0.05:
            e = last
    return max(0.0, s - HEAD), min(total, e + TAIL), total


def main():
    OUT.mkdir(exist_ok=True)
    LINES_DIR.mkdir(exist_ok=True)
    TRIMMED.mkdir(exist_ok=True)
    print(f"voice={VOICE} rate={RATE} pitch={PITCH}\n")
    rows, t = [], 0.0
    for idx, text, pause in LINES:
        mp3 = LINES_DIR / f"line{idx:02d}.mp3"
        if not mp3.exists() or mp3.stat().st_size < 1000:
            synth(idx, text, mp3)
        s, e, padded = speech_bounds(mp3)
        wav = TRIMMED / f"line{idx:02d}.wav"
        sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(mp3),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
        d = duration(wav)
        start = (t + pause) if idx > 1 else pause
        rows.append({"i": idx, "text": text, "start": round(start, 3), "dur": round(d, 3),
                     "end": round(start + d, 3), "pause_before": pause,
                     "padded_mp3": round(padded, 3)})
        t = start + d

    meta = {"voice": VOICE, "rate": RATE, "pitch": PITCH, "lines": rows,
            "speech_total": round(sum(r["dur"] for r in rows), 3),
            "last_end": round(rows[-1]["end"], 3)}
    (OUT / "narration.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # place the trimmed stems on a 60 s bed -> the narration master the picture is built around
    args, filt = [], []
    for n, r in enumerate(rows):
        args += ["-i", str(TRIMMED / f"line{r['i']:02d}.wav")]
        ms = int(round(r["start"] * 1000))
        filt.append(f"[{n}]adelay={ms}|{ms}[v{n}]")
    filt.append("".join(f"[v{n}]" for n in range(len(rows))) +
                f"amix=inputs={len(rows)}:normalize=0:dropout_transition=0[nar]")
    sh(["ffmpeg", "-v", "error", "-y"] + args + ["-filter_complex", ";".join(filt), "-map", "[nar]",
       "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(OUT / "narration_master.wav")])

    print(f"{'#':>3} {'start':>6} {'dur':>5} {'end':>6} {'pause':>6}  text")
    for r in rows:
        print(f"{r['i']:>3} {r['start']:>6.2f} {r['dur']:>5.2f} {r['end']:>6.2f} {r['pause_before']:>6.2f}  {r['text']}")
    print(f"\nspeech {meta['speech_total']:.1f}s | last word ends {meta['last_end']:.2f}s of {FILM_LEN:.0f}s "
          f"| {meta['speech_total'] / FILM_LEN * 100:.0f}% voiced")
    if meta["last_end"] > FILM_LEN - 4.5:
        print("FAIL: narration leaves under 4.5s for the end card")
        sys.exit(1)
    print("OK: narration fits, with room for the end card.")


if __name__ == "__main__":
    main()
