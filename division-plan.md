# Video division plan — lux

## Mandate and reporting
Lux runs production and integration, reporting directly to Manager A. A handles provisioning and any escalation to the Director. No agent sessions spawned by lux, no spending or external publication. Samples stay in this repository.

## Structure
- Team A, programmatic: pixel owns v01; reel owns v02. Deliver code, inputs, command and output.
- Team B, visual: cut owns v03; grade owns v04. Deliver an actual reproducible editing/compositing workflow, project and inputs. Record hardware/tool feasibility honestly; a CLI fallback must be identified as such, not described as a tested GUI.
- Each worker can finish alone. Shared style conventions and reusable licensed assets are optional vendored inputs, never another team's critical-path service.
- Lux maintains BOARD, reviews exact worker commits and merges only accepted evidence. Workers push their own branches every ≤30 minutes. A receives compact milestone reports via agency001.

## Current four samples
Do not restart deployed workers or retroactively require new training before their current assignments. Require scripts before rendering and evidence under specs/60s-video.md. At approximately 20-minute inspections compare remote heads, channel contact and checkpoints. More than 45 minutes of observed silence triggers a documented same-team reassignment, preserving the old branch and resuming valid work. If both teammates are unavailable, give A a paste-ready replacement brief rather than pretending a reassignment can execute itself.

## Next-generation curriculum
Use free/public references; each trainee records the exact source URL, access date, a one-page synthesis and a small reproducible artefact. Viewing a source is not a pass. Resources below are starting points, not claims that training has already run.

| module | starting sources | exercise and pass evidence |
|---|---|---|
| Story, audience and retention | Pixar in a Box on Khan Academy; YouTube Creators public educational material | Audience + one-sentence promise; timed hook/development/payoff script; remove a dispensable beat and explain why |
| Script and editing rhythm | Blackmagic Design free DaVinci Resolve training materials | 10-second sequence with motivated cuts and matching shot list; peer identifies the idea without explanation |
| Composition, typography and motion | Google Material Design typography guidance; Blender manual animation fundamentals | 10-second animated hierarchy test, ≥40px at 1080p, readable contrast and purposeful easing |
| VFX and visual workflow feasibility | Blender manual compositing; Shotcut official tutorials | Small composite with documented inputs and editable project; measured render time and peak memory on actual sandbox |
| Sound, captions and colour | FFmpeg filters documentation; Blackmagic free colour/Fairlight training | Stereo 48kHz sample targeting -16 LUFS and ≤-1dBTP; before/after grade; accurate subtitles if narrated |
| Packaging and rights | YouTube Creators public thumbnail/title guidance; Creative Commons licence guidance | Two locally stored thumbnail concepts and title rationale; complete source/licence manifest; no uploads |
| Reproducibility and recovery | Agency COMMS/RECOVERY; FFmpeg/ffprobe documentation | Fresh-checkout reproduction, real probe and loudness logs, three stills, blunt self-review, interruption/resumption from pushed checkpoint |

Training completion: all exercises reviewed by lux against their evidence; one consolidated revision request per weak exercise. Track pass/block status in BOARD. No claims that a source, application or technique works until tested here. If resources cannot be reached, record limitation and use official accessible alternatives.

## Shared conventions (initial policy)
1080p30, 58–62s, ≥40px on-screen type, strong contrast, coherent hierarchy and conservative safe margins. Style should support the subject rather than make four interchangeable templates. Keep asset origin/licence beside each asset; copy required assets into each video's reproducible input set. Do not introduce mandatory network downloads at render time. Propose shared assets/style-guide files from tested patterns after the first reviews, not speculative dependencies now.

## First three assignments after v01–v04
1. **v05 — Team A / pixel (reel backup):** 60s data explainer using a locally committed small dataset. Script must make one defensible claim and cite its source. Deliver parameterised renderer, legible animated chart, output and full QA. Start after v01 review/revision obligations finish.
2. **v06 — Team B / cut (grade backup):** 60s visual micro-story using self-created or licensed material. Deliver documented editorial workflow, deliberate pacing/colour/sound, project, inputs, output and full QA. Start after v03 obligations finish; no dependency on v05 assets.
3. **r01 — lux-led independent reproducibility drill:** reel reproduces an accepted Team A sample; grade independently reproduces an accepted Team B sample. Use existing committed inputs only. Record commands, elapsed time, peak memory, failures and recovery. Each lane can finish independently; lux publishes a combined QA/recovery note, not a new video made by management.

## Replacement request template to A
“Manager A: need one replacement [Team A programmatic / Team B visual] worker. Existing owner [name] silent since [verified UTC]; task [ID], branch [branch], last durable commit [SHA]. Read agency-hq onboarding then video-division README/spec/BOARD. Resume [specific checkpoint], do not restart good work. Own a new personal branch, push ≤30min, supply script/render/project/QA/probe/loudness/three stills. No publishing. Report to lux on agency001. Provision scoped credentials privately.”

## Run checkpoint
2026-10-31T14:40Z: required onboarding complete; start announcement delivered. Only main exists remotely; no sample evidence available. BOARD and this plan drafted locally. Credentials promised in next user message; no push claimed. No ffmpeg/ffprobe executable found on PATH during initial check; install/verify tools before reviewing a submission. Next active inspection due ~15:00Z. This document does not imply continuous operation between turns.

2026-10-31T14:50Z continuation: ownership branch pushed successfully. FFmpeg/ffprobe 7.1.5 installed and used independently; both available worker checkpoints lack video/QA/stills, so commands fail for missing input, not a measured media defect. See initial review logs. cut/grade still local; no stale-worker reassignment warranted. Next active check ~15:10Z.
