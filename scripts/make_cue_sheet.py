#!/usr/bin/env python3
"""Generate the deterministic cue sheet for 'What if I never slept again?'.

The cue sheet drives the counter at every frame, the caption beats, and the
escalation labels. One JSON feeds vox's animation and the final render.

Premise (chosen, see docs/PREMISE_ENGINE.md §11):
  What if I never slept again?
  Counter = hours awake. Rate = 1 hour per film second (1 film s = 1 real h).
  Film = 75 s @ 30 fps = 2250 frames, counter 0 -> 75 hours.

Pipeline rule (voice first): caption beats lock to voice word boundaries.
This sheet stores the *planned* beats; the locked version replaces start/end
times with the ElevenLabs synthesiser's actual word timestamps.
"""

import json, os

FPS = 30
DURATION_S = 75.0
TOTAL_FRAMES = int(round(DURATION_S * FPS))  # 2250
W, H = 1080, 1920  # 1080x1920 portrait (register house style for this format)
UNIT = "hours awake"
# Counter function: C(t) = t hours (t in seconds), i.e. 1 h / film second.
# Acceleration stated: 1 film second = 1 real hour; underlying physiology real-time.

CAPTIONS = [
    # (start_s, end_s, text, voice_line, escalation_label)
    (0.0, 5.0, "What if I never slept?", "What if I never slept again?", "baseline"),
    (5.0, 24.0, "I stayed awake for you", "I stayed awake for you, hour by hour.", "baseline"),
    (24.0, 36.0, "Legally drunk at 24", "At twenty-four hours you're impaired like a 0.10 percent blood alcohol level. Legally drunk.", "legally drunk (~0.10% BAC)"),
    (36.0, 48.0, "Microsleeps start now", "At thirty-six hours your brain forces microsleeps. Involuntary seconds of blackout.", "microsleeps begin"),
    (48.0, 72.0, "Hallucinations begin", "At forty-eight hours hallucinations and perceptual distortions set in. Reality wavers.", "hallucinations begin"),
    (72.0, 75.0, "Seventy-two hours awake", "Seventy-two hours awake. Psychosis territory.", "psychosis territory"),
]

JOKE = {
    "start_s": 75.0,
    "end_s": 78.0,
    "text": "That's a documentary.",
    "voice_line": "That's not a what-if. That's a documentary.",
    "counter": 75,
}

def counter_at(t_s):
    """Hours awake at time t (seconds). Deterministic: 1 h per film second."""
    return t_s  # 1 hour per second

def counter_at_frame(f):
    return f / FPS

def build():
    cue = {
        "meta": {
            "premise": "What if I never slept again?",
            "question": "What if I never slept again?",
            "unit": UNIT,
            "fps": FPS,
            "duration_s": DURATION_S,
            "total_frames": TOTAL_FRAMES,
            "resolution": [W, H],
            "counter_rate": "1 hour per film second",
            "acceleration": "1 film second = 1 real hour (underlying physiology real-time)",
            "counter_fn": "C(t) = t hours, t in seconds",
            "note": "Caption beats lock to voice word boundaries (voice first). Planned times here; "
                    "replace with ElevenLabs with-timestamps word boundaries before render.",
        },
        "counter_per_frame": [round(counter_at_frame(f), 6) for f in range(TOTAL_FRAMES)],
        "captions": [],
        "escalation": [],
        "joke": JOKE,
    }

    for i, (start_s, end_s, text, voice_line, label) in enumerate(CAPTIONS):
        cue["captions"].append({
            "id": i,
            "start_s": start_s,
            "end_s": end_s,
            "start_frame": int(round(start_s * FPS)),
            "end_frame": int(round(end_s * FPS)),
            "text": text,
            "voice_line": voice_line,
            "escalation_label": label,
            "word_boundaries": None,  # filled after voice synthesis (voice first)
        })

    # Escalation ladder (monotonic, from sleep medicine).
    ladder = [
        (0, "baseline - sharp"),
        (17, "impairment starts (~0.08% BAC)"),
        (24, "legally drunk (~0.10% BAC)"),
        (36, "microsleeps begin"),
        (48, "hallucinations begin"),
        (72, "psychosis territory"),
        (75, "past the verified 72-hour threshold"),
    ]
    for hours, label in ladder:
        cue["escalation"].append({
            "hours": hours,
            "frame": int(round(hours * FPS)),
            "time_s": hours,
            "label": label,
        })

    return cue

if __name__ == "__main__":
    out = "/home/user/video-division/cue_sheets/sleep_premise/cue_sheet.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cue = build()
    with open(out, "w") as f:
        json.dump(cue, f, indent=2)
    print(f"Wrote {out}")
    print(f"frames={TOTAL_FRAMES} duration={DURATION_S}s counter 0->{counter_at_frame(TOTAL_FRAMES-1)} h")
    # Verify named frames
    for f in [0, 720, 1080, 1440, 2160, 2249]:
        print(f"  frame {f} (t={f/FPS}s) -> counter {cue['counter_per_frame'][f]} h")
