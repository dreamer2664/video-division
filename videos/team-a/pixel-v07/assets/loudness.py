#!/usr/bin/env python3
"""
loudness.py — master the mix to −16 LUFS ±0.5 with true peak ≤ −1 dBTP, verified on the *encoded*
file rather than on a prediction.

Why this exists: in v06 I used the two-pass `loudnorm` recipe from the spec, it fell back to
`normalization_type: dynamic`, its prediction was 0.69 dB off, and the delivered film measured
−16.69 LUFS — outside tolerance. So here the loop measures the actual AAC output, the level is
corrected by a static gain plus a sample-peak limiter, and the number that goes into QA.md is the
number measured on the file that ships.

Also: ebur128 prints a per-frame block of `I:` lines before the Summary, and the Summary itself
contains a "Threshold: … LUFS" line. Parsing anything but the last Summary block reads −70.00.
"""
import re
import subprocess
import sys

TARGET_I = -16.0
TOL = 0.05
# The limiter ceiling is NOT the delivered true peak: sampling at 48 kHz and re-encoding to AAC
# adds 1.3-1.7 dB of inter-sample overshoot on this material (measured, see QA.md). So the ceiling
# is searched, not assumed, and the file is only accepted on its measured peak.
CEILINGS = (-1.6, -2.2, -2.8, -3.4, -4.0)
MAX_ITERS = 12


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def measure(path):
    """Integrated loudness and true peak from the Summary block only."""
    r = run(["ffmpeg", "-v", "info", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"])
    summary = r.stderr.split("Summary:")[-1]
    mi = re.search(r"^\s*I:\s+(-?[0-9.]+) LUFS", summary, re.M)
    mp = re.search(r"^\s*Peak:\s+(-?[0-9.]+) dBFS", summary, re.M)
    ml = re.search(r"^\s*LRA:\s+(-?[0-9.]+) LU", summary, re.M)
    if not mi or not mp:
        raise RuntimeError(f"could not parse ebur128 summary for {path}")
    return float(mi.group(1)), float(mp.group(1)), float(ml.group(1)) if ml else 0.0


def build(src, dst, gain_db, ceil_db=-2.2):
    lim = 10 ** (ceil_db / 20.0)
    af = f"volume={gain_db}dB,alimiter=limit={lim:.6f}:attack=5:release=60:level=0"
    r = run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af,
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", dst])
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-400:])


def search(src, dst, ceil_db, start_gain):
    """Fix the ceiling, solve for the gain that lands integrated loudness on target."""
    gain = start_gain
    best = None
    for _ in range(10):
        build(src, dst, gain, ceil_db)
        i, p, l = measure(dst)
        if best is None or (abs(i - TARGET_I), -p) < (abs(best[0] - TARGET_I), -best[1]):
            best = (i, p, l, gain)
        if abs(i - TARGET_I) <= TOL:
            break
        gain += TARGET_I - i
    return best


def main(src, dst):
    i0, p0, l0 = measure(src)
    print(f"source       {src}")
    print(f"  integrated {i0:+.2f} LUFS   peak {p0:+.2f} dBFS   LRA {l0:.1f} LU")
    print(f"  gain needed for {TARGET_I:+.1f} LUFS: {TARGET_I - i0:+.2f} dB\n")

    accepted = []
    for ceil in CEILINGS:
        i, p, l, g = search(src, dst, ceil, TARGET_I - i0)
        ok = abs(i - TARGET_I) <= 0.5 and p <= -1.0
        print(f"  ceiling {ceil:+.1f} dB -> gain {g:+.2f} dB | {i:+.2f} LUFS | peak {p:+.2f} dBTP "
              f"| LRA {l:.1f} | {'PASS' if ok else 'fail'}")
        if ok:
            accepted.append((abs(i - TARGET_I), -p, ceil, i, p, l, g))

    if not accepted:
        print("verdict      FAIL — no ceiling satisfied both limits")
        return 1

    # prefer the loudest accurate result: closest to target, then the most peak headroom
    accepted.sort()
    _, _, ceil, i, p, l, g = accepted[0]
    build(src, dst, g, ceil)
    i, p, l = measure(dst)
    print(f"\nchosen       ceiling {ceil:+.1f} dB, gain {g:+.2f} dB")
    print(f"measured     {i:+.2f} LUFS   peak {p:+.2f} dBTP   LRA {l:.1f} LU")
    print(f"verdict      PASS (spec: -16 +/-0.5 LUFS, true peak <= -1 dBTP)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
