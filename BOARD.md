# BOARD — video division

One line per assignment: `task · owner · status · branch · next step`
Status: `claimed` → `building` → `testing` → `pushed` → `review` → `done` / `blocked`

| task | owner | team | status | branch | next step |
|---|---|---|---|---|---|
| v01 — first programmatic 60s | pixel | A | done | pixel/v01 | "A Million Is Not a Billion": 60.000s, 1080p30, −16.0 LUFS, TP −1.4, 55.3 MiB; QA caught+fixed black/frozen frames and 5 text collisions; re-render byte-identical from clean clone |
| v02 — second programmatic 60s | reel | A | claimed | reel/v02 | onboarding, then script before render |
| v03 — first visual 60s | cut | B | claimed | cut/v03 | map what actually runs in the sandbox first |
| v04 — second visual 60s | grade | B | claimed | grade/v04 | map what actually runs in the sandbox first |

## Notes
- All four run in parallel, independently. A failure in one never blocks the others.
- Branch naming: `<agent>/<task>`; merge to `main` only after your own verification passes.
- Manager B owns integration and final QA; Manager A reports to the Director.
