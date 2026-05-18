---
description: Load and summarize the relevant plan step for the active phase
argument-hint: [step-number-or-topic]
---

Load the relevant plan step before working.

If `$ARGUMENTS` is empty:
1. Read `docs/CURRENT_PHASE.md` to find the active phase
2. Read `docs/phases/phase-<N>.md` to find which plan steps it references
3. Read those plan steps and summarize them in 5–10 bullets

If `$ARGUMENTS` is a number (1–16) or a topic keyword:
1. Map it to a file in `docs/plan/step-<N>-*.md` (try matching the topic to filenames)
2. Read the file
3. Summarize the key decisions, the reality checks, and the pitfalls

After summarizing, end with: "What aspect do you want to dig into?"

Be concise — the goal is orientation, not exhaustive coverage.
