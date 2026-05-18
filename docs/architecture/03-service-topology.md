# Service Topology

> How services connect, scale, and fail.

## Topology by phase

### Phase 1
```
[browser] → Vercel (Next.js) → Railway (FastAPI gateway) → Supabase Postgres
                                                         → Upstash Redis
```

### Phase 6 (end of MVP)
```
[browser] → Vercel
              │
              ▼
         FastAPI gateway ──────────────────────────────────┐
              │                                            │
              ├── REST → market-data-service               │
              ├── REST → portfolio-service                 │
              ├── REST → prediction-service                │
              ├── REST → backtesting-service               │
              └── REST → agent-service ── pgvector ── LLM API
                                                            │
                            Postgres + TimescaleDB + Redis ─┘
```

### Phase 11+ (production scale)
```
[browser] → Cloudflare → ALB → k8s ingress
                                  │
                              ┌───┴───┐
                              ▼       ▼
                          gateway pods (HPA)
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
              service       service     service
              pods          pods        pods
                  │           │           │
                  └───────────┼───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         Postgres RDS    Redis cluster    Kafka cluster
         + TimescaleDB                    (Redpanda)
```

## Scaling characteristics

| Service | CPU | Memory | Scale axis |
|---------|-----|--------|------------|
| api-gateway | low | low | request count |
| market-data | medium | medium | symbol count, WS connections |
| portfolio | low | low | user count |
| prediction | high (inference) | medium | request count, model size |
| backtesting | high | high | concurrent backtests |
| agent | low CPU, high LLM tokens | low | concurrent conversations |
| rl | very high (training) | high | training jobs (queue, not realtime) |
| analytics | medium | high | data volume |

## Failure modes

| Service down | User impact |
|--------------|-------------|
| api-gateway | total outage |
| market-data | no live prices, charts cached |
| portfolio | can't view portfolio (read from cache) |
| prediction | no new signals (existing visible) |
| backtesting | new runs fail; old results visible |
| agent | chat unavailable |
| rl | training paused; inference in prediction-service still works |
| analytics | dashboards stale |

## Health checks

Every service exposes:
- `GET /health` — liveness (process up)
- `GET /ready` — readiness (DB + dependencies reachable)

k8s probes:
- liveness: `/health`, every 10s, fail after 3
- readiness: `/ready`, every 5s, fail after 2

## Service-to-service auth

Phase 1-7: shared service token in env (`INTERNAL_SERVICE_TOKEN`). Simple, fine for solo dev.

Phase 8+: mTLS or service-mesh (Istio/Linkerd). Each service has its own cert.

Never trust internal service calls implicitly. The "trusted internal network" doesn't exist in cloud.

## Rate limits per service

| Service | Endpoint | Limit |
|---------|----------|-------|
| gateway | public auth | 10/min/IP |
| gateway | authenticated | 1000/min/user |
| market-data | candles | 600/min/user |
| prediction | predict | 60/min/user |
| backtesting | run | 5/min/user (heavy) |
| agent | chat | 30/min/user (LLM cost) |

Use Redis-backed token bucket. Library: `slowapi` (FastAPI integration).
