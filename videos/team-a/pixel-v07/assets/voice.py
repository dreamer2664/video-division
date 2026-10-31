#!/usr/bin/env python3
"""
voice.py — narration for v07 "IT ANSWERED — NIGHT TWO".

Engine: edge-tts 7.3.1, en-US-ChristopherNeural, --rate=-12%, --pitch=-4Hz. Same voice as night
one on purpose: it is the same speaker, the same flat, one night later. The voice decision and its
reasoning are recorded in QA.md §4 (RULE 8 — chosen, not polled).

Pacing trap found while building this: edge-tts 7.3.1 inserts roughly a full second of silence at
every *internal full stop*, so "Same flat. Same speaker. Nothing changed." synthesises at 55 wpm
while the same words separated by commas run at 130 wpm. A staccato script therefore has to be
written with commas and have its beats carried by the *cuts*, which is what this film does.

Difference from v06: v06 packed lines sequentially with a per-line pause. v07 has an uneven shot
list, so each line gets a *target* start time tied to the cut it belongs to, and the measured
speech is placed as close to that target as the previous line allows. Any line that overruns its
shot window is reported loudly, and the shot list is adjusted before rendering rather than the
audio being nudged to fit a caption.
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
WORK = HERE / "work"
LINES_DIR = WORK / "lines"
TRIMMED = WORK / "trim"

DUR = 60.0
HEAD, TAIL = 0.08, 0.10
MIN_GAP = 0.06

# (index, target start, text, shot window end this line must finish before)
LINES = [
    (1,  0.60, "Night two, two fourteen again.", 4.10),
    (2,  4.40, "Same flat, same speaker, nothing changed.", 6.90),
    (3,  7.00, "Except the walls.", 8.40),
    (4,  8.50, "And the door.", 9.70),
    (5,  9.80, "And the kitchen.", 11.10),
    (6, 11.20, "Six rooms in this flat.", 13.60),
    (7, 13.70, "Six surfaces, six microphones.", 16.10),
    (8, 16.20, "So I keep it loud, all night.", 18.40),
    (9, 18.50, "The radio stays on.", 19.90),
    (10, 20.00, "The kettle, twice an hour.", 21.40),
    (11, 21.50, "A towel under the door.", 24.10),
    (12, 24.20, "It isn't listening with a microphone any more.", 27.30),
    (13, 27.40, "There are seven surfaces now.", 30.00),
    (14, 30.20, "I stopped making noise.", 46.00),
    (15, 32.80, "And the flat went quiet.", 46.00),
    (16, 35.60, "And it was still listening.", 46.00),
    (17, 46.20, "It heard the quiet.", 49.40),
    (18, 49.60, "And the quiet was in the hall.", 52.00),
    (19, 52.40, "Night two is over.", 55.20),
    (20, 55.60, "Tomorrow, the quiet answers.", 60.00),
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
    """Trim edge-tts's ~0.2 s lead-in and 0.7-1.1 s tail. Parse by regex, never by field index."""
    total = duration(path)
    r = sh(["ffmpeg", "-v", "info", "-i", str(path), "-af", "silencedetect=n=-45dB:d=0.12", "-f", "null", "-"])
    txt = r.stderr
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*(-?[0-9.]+)", txt)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*(-?[0-9.]+)", txt)]
    s = ends[0] if (starts and starts[0] < 0.02 and ends) else 0.0
    e = total
    if starts:
        last = max(starts)
        if last > s and (total - last) > 0.05:
            e = last
    return max(0.0, s - HEAD), min(total, e + TAIL), total


def main():
    WORK.mkdir(exist_ok=True)
    LINES_DIR.mkdir(exist_ok=True)
    TRIMMED.mkdir(exist_ok=True)
    print(f"voice={VOICE} rate={RATE} pitch={PITCH}\n")

    rows, prev_end = [], 0.0
    for idx, target, text, window_end in LINES:
        mp3 = LINES_DIR / f"line{idx:02d}.mp3"
        if not mp3.exists() or mp3.stat().st_size < 1000:
            synth(idx, text, mp3)
        s, e, padded = speech_bounds(mp3)
        wav = TRIMMED / f"line{idx:02d}.wav"
        sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(mp3),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
        d = duration(wav)
        start = max(target, prev_end + MIN_GAP)
        end = start + d
        rows.append({"i": idx, "text": text, "target": target, "start": round(start, 3),
                     "dur": round(d, 3), "end": round(end, 3), "window_end": window_end,
                     "slip": round(start - target, 3), "overrun": round(max(0.0, end - window_end), 3),
                     "padded_mp3": round(padded, 3)})
        prev_end = end

    meta = {"voice": VOICE, "rate": RATE, "pitch": PITCH, "lines": rows,
            "speech_total": round(sum(r["dur"] for r in rows), 3),
            "last_end": round(rows[-1]["end"], 3)}
    (WORK / "narration.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    args, filt = [], []
    for n, r in enumerate(rows):
        args += ["-i", str(TRIMMED / f"line{r['i']:02d}.wav")]
        ms = int(round(r["start"] * 1000))
        filt.append(f"[{n}]adelay={ms}|{ms}[v{n}]")
    filt.append("".join(f"[v{n}]" for n in range(len(rows))) +
                f"amix=inputs={len(rows)}:normalize=0:dropout_transition=0[nar]")
    sh(["ffmpeg", "-v", "error", "-y"] + args + ["-filter_complex", ";".join(filt), "-map", "[nar]",
       "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(WORK / "narration_master.wav")])

    print(f"{'#':>3} {'target':>6} {'start':>6} {'dur':>5} {'end':>6} {'slip':>6} {'over':>6}  text")
    bad = 0
    for r in rows:
        flag = "  << OVERRUN" if r["overrun"] > 0.001 else ""
        if r["overrun"] > 0.001:
            bad += 1
        print(f"{r['i']:>3} {r['target']:>6.2f} {r['start']:>6.2f} {r['dur']:>5.2f} {r['end']:>6.2f} "
              f"{r['slip']:>6.2f} {r['overrun']:>6.2f}  {r['text']}{flag}")
    print(f"\nspeech {meta['speech_total']:.1f}s | last word ends {meta['last_end']:.2f}s of {DUR:.0f}s "
          f"| {meta['speech_total'] / DUR * 100:.0f}% voiced")
    if bad:
        print(f"FAIL: {bad} line(s) overrun their shot window — adjust the shot list, not the audio")
        sys.exit(1)
    if meta["last_end"] > DUR - 2.0:
        print("FAIL: narration leaves under 2 s for the hook card")
        sys.exit(1)
    print("OK: every line lands inside its shot window.")


if __name__ == "__main__":
    main()
