# Step 12 — Open-Source Reuse Strategy

> What to reuse, what to build, what to study only.

## Strategy principles

1. **Reuse mature libraries** for primitives (charts, RL algos, vector DBs)
2. **Build the product layer yourself** (UX, workflows, orchestration)
3. **Wrap external libs in adapters** so you can swap them later
4. **Verify the lib is alive** before depending on it (last commit, issue activity, sponsor list)

## Don't build from scratch

- ❌ Candlestick chart engine
- ❌ RL algorithms (PPO, DQN, SAC)
- ❌ Portfolio optimization math
- ❌ Vector database
- ❌ Authentication framework
- ❌ Kafka client
- ❌ Web charting library
- ❌ Backtesting engine core

## Quant libraries

| Library | Use for | Phase |
|---------|---------|-------|
| **vectorbt** | Backtesting, portfolio metrics, vectorized strategies | 5 |
| **Backtrader** | Event-driven strategies (more realistic) | 5+ |
| **Qlib** (Microsoft) | Factor modeling, ML pipelines, datasets | 7+ |
| **PyPortfolioOpt** | Mean-variance, risk parity, Black-Litterman | 7 |
| **pandas-ta** or **TA-Lib** | Technical indicators | 4 |

## RL

| Library | Use for | Phase |
|---------|---------|-------|
| **FinRL** | Trading environments, reference pipelines | 8 |
| **Stable-Baselines3** | RL algorithms | 8 |
| **Ray RLlib** | Distributed RL, multi-agent | 9 |
| **Gymnasium** | Environment standard | 8 |

## AI / Agents

| Library | Use for | Phase |
|---------|---------|-------|
| **LangGraph** | Stateful agent orchestration (primary) | 6, 9 |
| **CrewAI** | Quick prototyping (secondary) | 9 |
| **LlamaIndex** | RAG, document indexing | 6 |
| **FinGPT** | Finance prompts, sentiment, fine-tuning | 6+ |

## MLOps

| Library | Use for | Phase |
|---------|---------|-------|
| **MLflow** | Model registry, experiment tracking | 4 |
| **Weights & Biases** | RL experiment tracking, hyperparameter sweeps | 8 |

## UI

| Library | Use for | Phase |
|---------|---------|-------|
| **TradingView Lightweight Charts** | Candlestick + financial charts | 2 |
| **shadcn/ui** | Component foundation | 1 |
| **Tremor** | Analytics KPI cards & dashboards | 3+ |
| **ECharts** | Heatmaps, correlation matrices, factor charts | 7+ |
| **TanStack Table + Virtual** | Large data tables | 3+ |
| **cmdk** | Command palette | 3+ |

## Data infra

| Library | Use for | Phase |
|---------|---------|-------|
| **TimescaleDB** | Time-series Postgres extension | 2 |
| **pgvector** | Embeddings in Postgres | 6 |
| **Qdrant** | Standalone vector DB (only if pgvector isn't enough) | 9+ |
| **Redpanda** | Kafka-compatible, modern | 11+ |
| **Dagster** | Modern alternative to Airflow | 11+ |

## Auth

| Library | Use for |
|---------|---------|
| **Auth.js / NextAuth** | Next.js auth |
| **Keycloak** | Enterprise SSO (Phase 12+) |

## DevOps

| Library | Use for | Phase |
|---------|---------|-------|
| **Docker Compose** | Local dev | 1 |
| **Helm** | k8s packaging | 11 |
| **ArgoCD** | GitOps | 11+ |
| **Terraform** | IaC | 11+ |

## Trading platforms to study (don't fork)

These are too heavyweight to integrate, but read the architecture:

- **QuantConnect Lean** — strategy engine, brokerage abstraction
- **NautilusTrader** — institutional-grade event-driven engine
- **OpenBB** — open quant terminal patterns
- **Hummingbot** — execution + market making

## Outdated / avoid

- ❌ **Zipline** — abandoned
- ❌ Old TF1.x finance repos
- ❌ Quantopian-era projects (most code paths broken)
- ❌ Random crypto bots from 2018–2020

## The adapter pattern

Always wrap external libs:

```
your-platform/
└── adapters/
    ├── finrl/          # adapter for FinRL
    ├── vectorbt/       # adapter for vectorbt
    ├── langgraph/      # adapter for LangGraph
    └── tradingview/    # adapter for TV charts
```

This lets you swap libraries when one becomes unmaintained.

## See also

- [Phase 5: vectorbt integration](../phases/phase-5.md)
- [Phase 6: LangGraph + LlamaIndex](../phases/phase-6.md)
- [Phase 8: FinRL + Stable-Baselines3](../phases/phase-8.md)
