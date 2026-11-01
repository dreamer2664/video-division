# VIDEO DIVISION

**Current creative target:** read `DIRECTIVE-2026-11-01-house-look.md` first. House reference: `videos/team-b/grade-v06/` MARK FIVE. Prior portrait/vector/reference-format targets are withdrawn; their audits remain historical. Every new film must pass the house-look gate in `specs/60s-video.md`. Teams retain independent production workflows, not separate visual standards.

Manager B runs this repository. Two teams produce complete videos independently.

| team | approach | how it makes pictures |
|---|---|---|
| **Team A** — programmatic | code-generated video | FFmpeg filter graphs, Python rendering, generated typography/diagrams/motion |
| **Team B** — visual | conventional editing workflows | editors and compositing tools that actually run in a ~2 GB Debian sandbox |

**Law of the division**
1. One worker finishes a video alone. No cross-team dependency in any video's critical path.
2. Every deliverable is reproducible: the render command and its inputs are committed next to the output.
3. Every video ships with a QA note: what is good, what is not, measured facts (duration, resolution, levels).
4. **Nothing is published** to any external account. Samples stay here.
5. Never end a run on a command. A finished run ends with a closing message: paths, commit SHA, how to verify.

## Where things go

```
videos/team-a/<agent>-<slug>/   video.mp4 · script.md · assets/ · render.sh · QA.md
videos/team-b/<agent>-<slug>/   video.mp4 · script.md · assets/ · project/ · QA.md
specs/                          the brief every video must satisfy
BOARD.md                        one line per assignment: task · owner · status · branch · next step
```

Read `specs/60s-video.md` before producing anything. Read `agency-hq/docs/ONBOARDING.md` first.
