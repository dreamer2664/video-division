# BOARD — video division

Integration owner: **lux (Manager B)**, reporting to Manager A. Updated 2026-10-31 16:28 UTC. **All four first-generation samples ACCEPTED and merged to main. No publishing.**

| task | owner | team | final status | source branch / audited head | merge commit | next step |
|---|---|---|---|---|---|---|
| v01 — A Million Is Not a Billion | pixel | A | done / ACCEPT | pixel/v01 · dd7f112 | 48d8a29 | v05 brief issued; await worker claim |
| v02 — Waiting has a curve | reel | A | done / ACCEPT | reel/v02 · 19f85f9 | 686553e | r01 Team A fresh-checkout audit; await claim |
| v03 — The Quiet Signal | cut | B | done / ACCEPT | cut/v03 · e20082d | 7f67d04 | v06 brief issued; await worker claim |
| v04 — KELVIN | grade | B | done / ACCEPT | grade/v04 · 17e8fa8 | 8a17600 | r01 Team B fresh-checkout audit; await claim |

## Acceptance evidence
`reviews/2026-10-31-final/VERDICTS.md` supersedes the earlier missing-output audit. Per-worker directories contain independently executed spec commands, visible-summary loudnorm Input measurements, stream details, full-file black/freeze scans, atom inventories, actual boundary frames and visual inspection sheets. `integration.txt` records main/source blob equality and output SHA256. No production rerender by lux.

All four: 60.000000s, 1080p30 H.264/yuv420p, 48kHz stereo AAC, faststart, below 90MB, no detected >0.5s black/freeze intervals. Measured loudness/peak: reel -16.0/-4.4; cut -16.0/-3.3; grade -16.0/-1.7; pixel -16.1/-1.4 LUFS/dBTP. Pixel accepted within documented ±0.2 LU target tolerance, not misreported as exactly -16.0. Peaks all meet ≤-1dBTP.

Sampled visual inspection done; no subjective listening or real-time full audiovisual screening claimed. Human screening recommended before presentation; publication remains prohibited. Creative weaknesses are recorded honestly in verdicts/worker QA, not hidden by technical acceptance.

## Next assignments — issued, NOT claimed or started
See `assignments/next-wave.md` and `division-plan.md`.
- v05 — pixel, Team A; reel backup. New branch pixel/v05; script-first data explainer, full existing QA gate.
- v06 — cut, Team B; grade backup. New branch cut/v06; stronger editorial micro-story, independent of v05.
- r01 — reel/grade, independent team-specific audit lanes. New branches reel/r01 and grade/r01; do not alter accepted media. Explicitly document any reproduction failure.

## Supervision / recovery checkpoint
- Branches are preserved; only manager integrates; no force-pushes or deletions.
- A message/brief being sent is not evidence a worker has resumed. New-wave tasks await explicit claims; ask A to reactivate existing sessions if not receiving messages, rather than inventing live supervision or spawning sessions.
- While active, inspect approximately every 20min and push at least every 30min. No unattended manager process is promised between turns. Resume by fetching current heads, channel contacts and this board.
- For a claimed active task, >45min confirmed silence triggers same-team reassignment with checkpoint/commit preserved; if no live teammate, hand A the paste-ready recovery brief in division-plan.md.
- Integration order was exactly reel → cut → grade → pixel, one non-ff merge per video. BOARD-only conflicts retained manager state; worker deliverable paths are unchanged.
