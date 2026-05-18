---
description: Start a vertical slice for a feature (branch + plan + todos)
argument-hint: <feature-name>
---

Start a new vertical-slice feature called `$ARGUMENTS`.

Steps:

1. Verify we're on `main` and the working tree is clean. If not, stop and tell the user.
2. Read `docs/CURRENT_PHASE.md` to confirm the feature belongs in the current phase. If not, ASK before proceeding.
3. Create a feature branch: `git checkout -b feat/$ARGUMENTS`
4. Read the relevant `docs/phases/phase-<N>.md` and identify the specific tasks that map to `$ARGUMENTS`.
5. Create a planning doc at `docs/scratch/$ARGUMENTS.md` with:
   - Goal
   - Phase + plan-step references
   - Vertical slice breakdown (UI → API → DB → tests)
   - Open questions
   - Acceptance criteria
6. Write a TodoWrite list with the slice broken into:
   - DB migration (if any)
   - Backend models / schemas / services / endpoints
   - Frontend components / hooks / pages
   - Tests (backend + frontend)
   - Documentation update

CRITICAL principles:
- The slice must be COMPLETE end-to-end before merging — no half-done backends or stub frontends
- If the slice is too large for one PR, break it into multiple sub-features rather than merging incomplete work
- Tests are part of "done"
- Update `docs/architecture/02-database-schema.md` if you add tables

After setup, give the user a one-paragraph summary of what's about to happen and wait for confirmation before writing any code.
