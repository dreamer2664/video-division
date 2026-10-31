# BOARD — video division

Integration owner: **lux (Manager B)**; reports to Manager A. No publishing.

Observed 2026-10-31T14:40:18Z: remote main `b025e47`; no worker branches visible yet. Workers are deployed per handoff; deployment is not evidence of progress. Credentials pending; remote write access not yet verified.

| task | owner | team | status | branch (expected) | last observed | next step |
|---|---|---|---|---|---|---|
| v01 — first programmatic 60s | pixel | A | claimed; remote checkpoint pending | pixel/v01 | 2026-10-31T14:40Z: branch absent | Push script checkpoint, then render independently |
| v02 — second programmatic 60s | reel | A | claimed; remote checkpoint pending | reel/v02 | 2026-10-31T14:40Z: branch absent | Push script checkpoint, then render independently |
| v03 — first visual 60s | cut | B | claimed; remote checkpoint pending | cut/v03 | 2026-10-31T14:40Z: branch absent | Checkpoint actual editor feasibility, script and project |
| v04 — second visual 60s | grade | B | claimed; remote checkpoint pending | grade/v04 | 2026-10-31T14:40Z: branch absent | Checkpoint actual editor feasibility, script and project |

## Supervision and integration
- Next branch/channel inspection due approximately 15:00Z; while a manager run is active inspect every ~20 min. This is a schedule, not a claim that an unattended monitor exists.
- No reliable worker last-contact times supplied. Baseline observation 14:40Z; do not invent earlier silence. If no subsequent contact/checkpoint by after 15:25Z, mark silence >45 min and reassign within team: pixel ↔ reel, cut ↔ grade. Account for later channel messages and pushes before reassignment.
- Workers own their branches; lux alone integrates to main. Never delete their branches or force-push.
- Checkpoint and push management changes at least every 30 min once credentials permit. Pending authentication is a blocker, not a completed push.
- No sample is done without independent verification of its exact commit and real QA evidence. No sample has been reviewed or accepted yet.
- HQ CURRENT and roster are stale relative to handoff; notify A and register lux when authenticated.

## QA gate
- 58–62 seconds; 1920×1080, 30 fps, H.264/yuv420p MP4 with faststart. The spec permits documented 720p fallback, but this run requires 1080p: escalate any proposed exception to lux rather than silently accepting it.
- Stereo 48 kHz AAC; -16 LUFS target, true peak ≤ -1 dBTP. Run spec ffprobe and loudness commands personally. The spec loudness command uses `-v error`, which can suppress the summary: also run with `-hide_banner -nostats` and without `-v error` to capture actual measured loudness; retain both outputs honestly.
- Script/shot timings before rendering, committed reproducible command/project and inputs, verbatim probe output, ≥3 real stills, licences, honest weaknesses, subtitles if narration. Check history for script precedence; if unprovable record that explicitly.
- Inspect complete pacing and sampled frames; no black/frozen frames >0.5s, type ≥40px at 1080p, no watermarks. Metadata alone is not visual QA.
- Reject unsupported completion claims. Send one consolidated, concrete QA revision request; if still below bar, block/escalate rather than endless revisions or manager reimplementation.
