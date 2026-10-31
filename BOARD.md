# BOARD — video division

Integration owner: **lux (Manager B)**; reports to Manager A. No publishing.

Observed 2026-10-31T14:50Z: ownership branch pushed; worker branches fetched and checked. No completed video submitted. cut and grade are working locally per Manager A/user handoff; no remote branches yet.

| task | owner | team | status | branch | last observed | next step |
|---|---|---|---|---|---|---|
| v01 — first programmatic 60s | pixel | A | building; checkpoint reviewed, not accepted | pixel/v01 | 14:50Z head `3bf11ee2`: script only | Complete own renderer/output, QA/probe/loudness, captions and ≥3 stills; see initial review |
| v02 — second programmatic 60s | reel | A | building; checkpoint reviewed, not accepted | reel/v02 | 14:50Z head `941b9870` (after `6bfadb77`): script, renderer/assets/captions | Push own output, QA/probe/loudness and ≥3 stills; see initial review |
| v03 — first visual 60s | cut | B | building locally (reported); remote checkpoint pending | cut/v03 (expected) | channel progress 14:44:04Z; remote absent at 14:50Z | Push existing script/tool-feasibility checkpoint, continue own visual workflow |
| v04 — second visual 60s | grade | B | building locally (reported); remote checkpoint pending | grade/v04 (expected) | channel start 14:46:13Z; remote absent at 14:50Z | Push existing script/tool-feasibility checkpoint, continue own visual workflow |

## Supervision and integration
- Next branch/channel inspection due approximately 15:10Z; while a manager run is active inspect every ~20 min. This is a schedule, not a claim that an unattended monitor exists.
- Latest channel contact observed: pixel 14:46:22Z; reel 14:48:38Z; cut 14:44:04Z; grade 14:46:13Z. No worker is >45 min silent. Use later contact/push if available; if silence exceeds 45 min, reassign within team pixel ↔ reel or cut ↔ grade and preserve old branches.
- Workers own their branches; lux alone integrates to main. Never delete their branches or force-push.
- Checkpoint and push management changes at least every 30 min once credentials permit. Authentication verified through ownership-branch push; secrets remain outside repos (private askpass, clean HTTPS remote).
- No sample is done without independent verification of its exact commit and real QA evidence. Initial checkpoint reviews and failed missing-input verification logs: `reviews/2026-10-31-initial/`. No sample accepted; no visual inspection possible without stills/output.
- HQ CURRENT and roster are stale relative to handoff; notify A and register lux when authenticated.

## QA gate
- 58–62 seconds; 1920×1080, 30 fps, H.264/yuv420p MP4 with faststart. The spec permits documented 720p fallback, but this run requires 1080p: escalate any proposed exception to lux rather than silently accepting it.
- Stereo 48 kHz AAC; -16 LUFS target, true peak ≤ -1 dBTP. Run spec ffprobe and loudness commands personally. The spec loudness command uses `-v error`, which can suppress the summary: also run with `-hide_banner -nostats` and without `-v error` to capture actual measured loudness; retain both outputs honestly.
- Script/shot timings before rendering, committed reproducible command/project and inputs, verbatim probe output, ≥3 real stills, licences, honest weaknesses, subtitles if narration. Check history for script precedence; if unprovable record that explicitly.
- Inspect complete pacing and sampled frames; no black/frozen frames >0.5s, type ≥40px at 1080p, no watermarks. Metadata alone is not visual QA.
- Reject unsupported completion claims. Send one consolidated, concrete QA revision request; if still below bar, block/escalate rather than endless revisions or manager reimplementation.
