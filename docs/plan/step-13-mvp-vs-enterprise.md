# Step 13 — MVP vs Enterprise Feature Separation

> The single most important strategic doc in this plan.

## The golden rule

> MVP = Maximum Validation Product, not Minimum Viable Product

Build the smallest thing that proves:
- Users care
- The architecture works
- Investors / portfolio reviewers understand the vision

## What your MVP actually is

> **AI-Powered Quant Research & Portfolio Platform**

Not:
- ❌ An autonomous hedge fund
- ❌ A full RL ecosystem
- ❌ An institutional cloud platform

## MVP feature set (Phases 1–6, ~6 months)

### Market dashboard (Phase 2)
- Live prices + watchlists
- Candlestick charts with indicators (RSI, MACD, etc.)
- Market search

### Portfolio tracker (Phase 3)
- Holdings + transactions
- Allocation chart
- PnL + Sharpe + drawdown
- Performance over time

### ML signal engine (Phase 4)
- XGBoost-based price prediction
- BUY/SELL/HOLD signals with confidence
- Technical indicator features
- Signal history

### Backtesting platform (Phase 5)
- vectorbt-based simulation
- Equity curve
- Sharpe, max drawdown, win rate, CAGR
- Strategy comparison

### AI research assistant (Phase 6)
- LangGraph-based chat
- News + market analysis
- RAG over SEC filings, news
- Citations

### Auth (Phase 1)
- Login / signup
- JWT
- Basic RBAC

## MVP tech stack (deliberately simple)

```
Frontend: Next.js + Tailwind + shadcn/ui + TradingView Charts + Zustand
Backend:  FastAPI + Postgres + Redis + WebSockets
ML:       XGBoost + LightGBM + vectorbt + PyPortfolioOpt
AI:       LangGraph + OpenAI/Anthropic + pgvector + LlamaIndex
Deploy:   Docker Compose locally; Vercel + Railway/Render hosted
```

## MVP architecture (deliberately not microservices-y)

For Phases 1–6, you can run as a near-monolith with logical service boundaries:

```
Next.js
   ↓
FastAPI app (with internal routers per domain)
   ↓
PostgreSQL + Redis
   ↓
ML modules (imported, not separate processes)
```

You **don't** need separate processes per service until Phase 7+. Logical boundaries (folder structure) is enough.

## Don't build during MVP

- ❌ Multi-agent hedge fund
- ❌ Autonomous trading
- ❌ Distributed RL training
- ❌ Institutional OMS
- ❌ Prime brokerage integrations
- ❌ Multi-tenant enterprise infra
- ❌ Kubernetes
- ❌ Kafka
- ❌ Compliance systems
- ❌ Advanced observability

## MVP success metrics

| Validation | Goal |
|------------|------|
| Users use dashboards | Yes |
| Users trust AI analysis | Yes |
| ML predictions look useful | Yes |
| Investors understand product | Yes |
| Infrastructure stable | Yes |

## Target MVP user

Don't target:
- ❌ Goldman Sachs
- ❌ Citadel
- ❌ Jane Street

Target:
- ✅ Retail quants
- ✅ AI/finance enthusiasts
- ✅ Finance students
- ✅ Indie researchers
- ✅ Crypto quants

## Phase 2 — Growth (Phases 7–10)

Add when MVP has traction:

- Portfolio optimization (efficient frontier, risk parity)
- Advanced AI copilots
- Collaborative workspaces
- Paper trading
- Strategy marketplace
- Advanced RAG with persistent memory
- Basic agent orchestration

Infra additions: Kafka, separate microservices, GPU inference.

## Phase 3 — Advanced AI (Phases 8–10)

- Supervisor agents
- Research / risk / portfolio agents
- AI investment committee
- Consensus engines
- Autonomous workflows
- PPO trading agents
- RL experiment tracking

## Phase 4 — Enterprise (Phases 11–12)

- Multi-tenant
- Team workspaces
- SSO/SAML
- Audit logging
- Compliance tooling
- Kubernetes
- GPU clusters
- High-frequency streaming
- Institutional dashboards

## Solo founder optimization

**Build in this order. Period.**

```
Dashboard
   ↓
Market Data
   ↓
Portfolio
   ↓
ML Signals
   ↓
Backtesting
   ↓
AI Assistant
   ↓
[STOP — this is your MVP. Get users.]
   ↓
Optimization (Phase 7)
   ↓
RL (Phase 8)
   ↓
Multi-Agent (Phase 9)
```

## Cost targets

| Stage | Monthly |
|-------|---------|
| MVP | $50–300 |
| Growth | $500–2k |
| Enterprise | $5k–50k+ |

## Acceptable MVP shortcuts

- ✅ Monolithic FastAPI backend (with clean modules)
- ✅ Simple deploy (Vercel + Railway)
- ✅ Minimal observability
- ✅ Managed databases
- ✅ Test coverage on critical paths only

## Never take shortcuts on

- ❌ Database schema quality
- ❌ API design
- ❌ Authentication
- ❌ Modular folder structure (so you can split services later)
- ❌ Logging basics

## Most important strategic advice

**Build vertical slices, not horizontal layers.**

Wrong: "all backend → then all frontend → then all AI"
Right: "feature complete (UI + API + DB + tests) → next feature"

## See also

- [Phase 1 tasks](../phases/phase-1.md)
- [Timeline](step-10-timeline.md)
