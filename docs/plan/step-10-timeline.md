# Step 10 — Development Timeline

> 12-month roadmap. See `docs/phases/` for actionable per-phase task lists.

## Reality check

The original plan is 12 months for a full-time solo developer who never gets stuck. Realistic adjustments:

- **Solo dev, part-time (~15 hrs/week):** 18–24 months for the full vision
- **Solo dev, full-time:** 9–12 months for MVP through Phase 6, **18 months total**
- **Team of 3–5:** 6–8 months MVP, 10–12 months for full vision

If you fall behind, that's expected. Don't extend scope to "make up time."

## Phase summary

| # | Phase | Months | What you have at the end |
|---|-------|--------|---------------------------|
| 1 | Foundation Infrastructure | 1 | Monorepo, auth, dashboard shell |
| 2 | Market Data Platform | 2 | Real-time prices + charts |
| 3 | Portfolio + Analytics | 3 | Working portfolio tracker |
| 4 | ML Prediction Systems | 4 | XGBoost-powered signals |
| 5 | Backtesting Platform | 5 | Strategy testing lab |
| 6 | AI Research Assistant | 6 | **MVP COMPLETE** |
| 7 | Portfolio Optimization | 7 | Efficient frontier + risk parity |
| 8 | RL Trading Systems | 8 | PPO trading agent |
| 9 | Multi-Agent Hedge Fund | 9 | LangGraph supervisor + agents |
| 10 | Institutional Analytics | 10 | Heatmaps, factor models |
| 11 | Production Scaling | 11 | Kubernetes, Kafka, observability |
| 12 | Enterprise Stabilization | 12 | Security, compliance, polish |

## Sprint structure

Use **2-week sprints**:
- Week 1: Implementation
- Week 2: Testing, integration, deployment

## Vertical slice principle

Each feature must be completed end-to-end before starting the next:

```
Feature
├── UI component
├── API endpoint
├── DB migration
├── Tests
└── Deployment
```

Don't build all backend then all frontend. That guarantees nothing ships.

## Investor / portfolio demo milestones

| When | Show |
|------|------|
| End of Month 3 | Live dashboard, portfolio analytics, basic charts |
| End of Month 6 | + ML signals, backtesting, AI research assistant — **this is the MVP demo** |
| End of Month 9 | + RL trading lab, multi-agent workflows |
| End of Month 12 | Full institutional terminal |

## Risk management

| Risk | Mitigation |
|------|------------|
| Scope explosion | Strict phase gates; don't start Phase N+1 until N's acceptance criteria pass |
| RL complexity | Delay until Phase 8; classical ML in MVP |
| Infra over-engineering | Use managed services in MVP; no k8s before Phase 11 |
| Burnout | 2-week sprints with buffer; not 7-day-a-week grind |
| Data quality | Build ingestion + validation carefully in Phase 2 |

## See also

- [Phase 1 tasks](../phases/phase-1.md) — start here
