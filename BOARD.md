# BOARD — video division

One line per assignment: `task · owner · status · branch · next step`
Status: `claimed` → `building` → `testing` → `pushed` → `review` → `done` / `blocked`

| task | owner | team | status | branch | next step |
|---|---|---|---|---|---|
| v01 — first programmatic 60s | pixel | A | claimed | pixel/v01 | onboarding, then script before render |
| v02 — second programmatic 60s | reel | A | pushed | reel/v02 | revised video and byte-identical clean-clone reproduction; Manager B to review picture and sound |
| v03 — first visual 60s | cut | B | claimed | cut/v03 | map what actually runs in the sandbox first |
| v04 — second visual 60s | grade | B | claimed | grade/v04 | map what actually runs in the sandbox first |

## Notes
- All four run in parallel, independently. A failure in one never blocks the others.
- Branch naming: `<agent>/<task>`; merge to `main` only after your own verification passes.
- Manager B owns integration and final QA; Manager A reports to the Director.
