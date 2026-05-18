# quant-os — Project Plan Index

This is the master index for everything in `docs/`. The full 16-step architecture plan you wrote is preserved verbatim in `docs/plan/`. Phase-by-phase actionable task lists live in `docs/phases/`. Architecture deep-dives live in `docs/architecture/`.

## How to use these docs

**With Claude Code:**
- Don't load all of these into CLAUDE.md — that bloats context and degrades performance.
- The lean root `CLAUDE.md` references these on demand.
- When working on a specific phase, only `docs/CURRENT_PHASE.md` and `docs/phases/phase-<N>.md` need to be in context.
- Use slash commands like `/review-plan` to pull in the relevant plan step when needed.

**For yourself (the human):**
- The plan files (`docs/plan/`) are reference material, like an architecture book.
- The phase files (`docs/phases/`) are your actual day-to-day checklist.
- Architecture files (`docs/architecture/`) are deep-dives for when you're implementing something specific.

## The original 16-step plan

Preserved as written, one file per step:

1. [Foundation Architecture](plan/step-01-foundation-architecture.md)
2. [Database Schema Design](plan/step-02-database-schema.md)
3. [Microservice Architecture](plan/step-03-microservice-architecture.md)
4. [API Design](plan/step-04-apis.md)
5. [Quant ML Roadmap](plan/step-05-quant-ml-roadmap.md)
6. [RL Trading Architecture](plan/step-06-rl-architecture.md)
7. [Multi-Agent Hedge Fund](plan/step-07-multi-agent.md)
8. [Institutional Dashboard UI](plan/step-08-ui-wireframes.md)
9. [Production Deployment](plan/step-09-deployment.md)
10. [Development Timeline](plan/step-10-timeline.md)
11. [Monorepo Setup](plan/step-11-monorepo.md)
12. [Open-Source Reuse Strategy](plan/step-12-open-source-reuse.md)
13. [MVP vs Enterprise Separation](plan/step-13-mvp-vs-enterprise.md)
14. [Folder Structures](plan/step-14-folder-structures.md)
15. [Event-Driven Architecture](plan/step-15-event-driven.md)
16. [AI Agent Workflows](plan/step-16-agent-workflows.md)

## Phase-by-phase execution plan

Each phase has its own checklist with concrete tasks, acceptance criteria, and the related plan steps:

- [Phase 1 — Foundation Infrastructure](phases/phase-1.md) (Month 1)
- [Phase 2 — Market Data Platform](phases/phase-2.md) (Month 2)
- [Phase 3 — Portfolio + Analytics](phases/phase-3.md) (Month 3)
- [Phase 4 — ML Prediction Systems](phases/phase-4.md) (Month 4)
- [Phase 5 — Backtesting Platform](phases/phase-5.md) (Month 5)
- [Phase 6 — AI Research Assistant](phases/phase-6.md) (Month 6) ← **MVP complete here**
- [Phase 7 — Portfolio Optimization](phases/phase-7.md) (Month 7)
- [Phase 8 — RL Trading Systems](phases/phase-8.md) (Month 8)
- [Phase 9 — Multi-Agent Hedge Fund](phases/phase-9.md) (Month 9)
- [Phase 10 — Institutional Analytics](phases/phase-10.md) (Month 10)
- [Phase 11 — Production Scaling](phases/phase-11.md) (Month 11)
- [Phase 12 — Enterprise Stabilization](phases/phase-12.md) (Month 12)

## Architecture references

Topical deep-dives, used when implementing a specific area:

- [System Architecture](architecture/01-system-architecture.md)
- [Database Schema](architecture/02-database-schema.md)
- [Service Topology](architecture/03-service-topology.md)
- [API Contracts](architecture/04-api-contracts.md)
- [Event-Driven Design](architecture/05-event-driven.md)
- [AI Agent Design](architecture/06-agent-design.md)
- [RL System Design](architecture/07-rl-design.md)
- [UI System](architecture/08-ui-system.md)
- [Deployment & Infra](architecture/09-deployment.md)
- [Open-Source Reuse](architecture/12-open-source-reuse.md)

## A note on the plan vs. reality

The original plan (Steps 1–16) is ambitious and aspirational. Step 13 itself acknowledges that not all of it should be built upfront — and that advice is correct. Your real path through this is:

1. **Months 1–6:** Build the MVP (Phases 1–6). This is a complete, demoable, useful product on its own.
2. **Months 7–10:** Add advanced features (optimization, RL, agents, analytics) in priority order based on what users actually want.
3. **Months 11–12:** Production scale, only when there's traction that demands it.

If you reach the end of Phase 6 with a working MVP, you've already built something most ambitious projects never finish. Phases 7+ are upside, not requirements.
