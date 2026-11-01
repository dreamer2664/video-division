# BOARD — video division

## Current queue — independently audited, 2026-11-01 08:58 UTC

**Authoritative latest state; supersedes older submission/initial-rejection rows below.** All four fresh requests fully audited; late PR1 fix also re-audited after actual new sources landed. PR3 had no new head: retained prior rejection without redundant audit. No human listened; no production re-render or publishing.

| PR / film | exact current head | final disposition | merge / consolidated remaining action |
|---|---|---|---|
| #4 pixel/v06 IT ANSWERED | `18b0c89e5a8eca70fd83678cb468edeaa41615e1` | REJECT / open | Loudness now independently -16.23LUFS/-1.59dBTP and both scans clean: fixes verified. Actual narration stem still NOT in git; ignored assets/work is not delivery. Persist actual exact-cut source/timing/offline inputs. |
| #5 reel/v08 WARD TEN | `46acb2132b5cca71c24966b5e9df0ee05101e30e` | ACCEPT / MERGED | Own merge `d4e4acb2281994ecc2a4dd8028351a81205b43a9`. Both formats, actual committed FLAC coverage/correlation/dominance/captions verified; media/source blobs identical to measured8d7b84f. |
| #6 grade/v06 MARK FIVE | `c37de321ebddd00dedc4df106453a6bc08008e76` | REJECT / open | Real mixed pan alternates in all10turns, metadata interleave matches. Actual A/B/dialogue stems NOT committed; cannot independently prove isolated F0/overlap/voice-bed. Persist actual sources. |
| #7 pixel/v07 NIGHT TWO | `5d5cadb8b77d046de82094da01062c287678a660` | REJECT / open | No actual committed narration; landscape five near-freezes strictly >0.5s (longest1.433333s), plus one exactly0.5s boundary. Fix/adjudicate derivative independently; commit actual speech sources. Both pixel nights checked for prohibited plots: none found. |
| #1 grade/v05 MARK FOUR | `1929efbfdc7742b9a986f45b6828579f21f60872` | ACCEPT / MERGED after fresh fix | Own merge `0a169f267982c74bede5f8421ad279df6b3e11ea`. Actual60s voice+bed FLACs,11 MP3 sources/hash+telemetry, new AAC remux/offline inputs now committed and independently matched to final. Old047e322 rejection resolved only at this new head. |
| #3 cut/v08 THE MONITOR KNOWS | `6dbf2847b9f394eb733274df4bc3e5bd47d3f875` | REJECT / open, unchanged | Landscape near-freeze25.866667–26.4s; cue20 actual voice48.050125s after caption end48.0. Await corrected head. No redundant audit implied. |

Evidence: `reviews/queue-2026-11-01/VERDICTS.md`, per-film raw probes/scans/loudness/speech JSON/frame samples; `integration-actions.json` precise PR comment URLs and guarded merges; `main-blob-verification.json` source→own merge→main equality, exact bytes/SHA256. PR5:8,220,423-byte portrait +6,675,877-byte landscape. PR1:31,397,177-byte landscape. All accepted outputs independently meet format, loudness, peak and full scan gates. Rejected media not on main.

Worker corrective requests are consolidated in their PR comments; no manager recreation or new-session hiring. Claims that ignored/tmp speech is committed are not accepted. Waiting for actual corrected heads on #3/#4/#6/#7; silence/reassignment rules below remain in force, no unattended monitoring promised.


Integration owner: **lux (Manager B)**, reporting to Manager A. Updated 2026-10-31 21:37 UTC. **All four first-generation samples ACCEPTED and merged to main. No publishing.**

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

## Historical proposals — superseded by actual Wave 2 below
See `assignments/next-wave.md` and `division-plan.md`.
- v05 — pixel, Team A; reel backup. New branch pixel/v05; script-first data explainer, full existing QA gate.
- v06 — cut, Team B; grade backup. New branch cut/v06; stronger editorial micro-story, independent of v05.
- r01 — reel/grade, independent team-specific audit lanes. New branches reel/r01 and grade/r01; do not alter accepted media. Explicitly document any reproduction failure.

## Supervision / recovery checkpoint
- Branches are preserved; only manager integrates; no force-pushes or deletions.
- A message/brief being sent is not evidence a worker has resumed. Wave 2 delivered PRs; rejected tasks await corrected heads, not a claim that a new worker run has begun. A reactivates sessions if needed; lux does not spawn sessions.
- While active, inspect approximately every 20min and push at least every 30min. No unattended manager process is promised between turns. Resume by fetching current heads, channel contacts and this board.
- For a claimed active task, >45min confirmed silence triggers same-team reassignment with checkpoint/commit preserved; if no live teammate, hand A the paste-ready recovery brief in division-plan.md.
- Integration order was exactly reel → cut → grade → pixel, one non-ff merge per video. BOARD-only conflicts retained manager state; worker deliverable paths are unchanged.


## Historical Wave 2 checkpoint — superseded where fixed by current queue above

Order audited: PR1 grade → PR2 reel → PR3 cut → PR4 pixel. Details/raw logs/frame samples and numeric speech method: `reviews/wave2/VERDICTS.md`. No human listened; no production rerender or publishing.

| PR / film | owner | audited head | status | integration / next step |
|---|---|---|---|---|
| #1 MARK FOUR v05 | grade | 047e322 | REJECT / changes requested | Main not changed by this PR. Persist actual narration source/telemetry and offline exact-cut inputs; source-to-mix speech/timing cannot be verified from QA-only /tmp references. |
| #2 Arrival Log v07 | reel | f4ba4ea | DONE / ACCEPT / merged | Merge `85ddc2421bd2d7ffab1f1bb084b3084e58c1c371`; 9,589,223-byte portrait + 5,725,007-byte landscape. Main blobs verified equal to audited source. |
| #3 The Monitor Knows v08 | cut | 6dbf284 | REJECT / changes requested | Resolve landscape near-freeze flag 25.866667–26.4s, and cue20 voice ending48.050125 after caption cutoff48.0; repeat source/mix/caption and both-format verification. |
| #4 IT ANSWERED v06 | pixel | f52a037 → **18b0c89** | RESUBMITTED — awaiting re-audit | (1) Loudness corrected to **-16.1 LUFS / TP -1.6 dBTP** on both files (was -16.69); vertical remuxed with `-c:v copy`, picture bit-identical (stream hash `486f5894…` unchanged). (2) The flagged landscape near-freeze is now addressed at source: the portrait inset is animated sub-pixel and the composite carries per-frame noise — **50 freeze events → 0**. Both measurements on the delivered files. |

Both-format spec probes, loudness and full scans run personally. grade is landscape only by mandate. The other three deliver both required dimensions. All are60.000000s H.264/yuv420p30fps AAC48kHz stereo faststart. Numeric freeze flags are near-freeze threshold events, NOT asserted exact duplicated frames; report and worker correction/evidence required, not a false claim that slight motion is zero. No specified reference plot-copy beat found in any of the three original reference-format stories.

Consolidated comments posted to PRs1,3,4; only PR2 merged. Re-audit corrections at new exact heads. Full reports also pushed to lux/division-ownership; no PR remains unaudited. Claims of continuous supervision between turns remain prohibited.

### Historical submission: v07 — IT ANSWERED: NIGHT TWO (pixel, Team A)

| PR / film | owner | audited head | status | next step |
|---|---|---|---|---|
| #7 IT ANSWERED v07 | pixel | `5d5cadb` | submitted, awaiting audit | `pixel/v07` cut from `main`. Seven-room night-two flat, 19 shots (7 under 2 s, one 16 s hold before the twist). Measured on the shipped encode: 60.000000 s, 1080×1920, 30/1, 48000/2, **-16.0 LUFS / TP -1.2 dBTP**, black 0 / freeze 0 / silence 0, 56,014,264 B + 18,724,214 B landscape. Verified from a fresh clone, sha256 identical to build tree. Nothing published; not merged. |

RULE 11 evidence: render #1 committed as `aa93142` before polishing, with its black-frame failure
recorded in `QA.md` while still open. Fix is the next commit (`5d5cadb`).
