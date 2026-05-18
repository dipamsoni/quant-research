# Step 3 — Full Microservice Architecture

> Reference doc. Defines service communication, real-time pipelines, gateway routing, observability.

## Service map

### Core services (MVP, Phases 1–6)
- `api-gateway`
- `auth-service` (or auth folded into gateway for MVP)
- `market-data-service`
- `portfolio-service`
- `prediction-service`
- `backtesting-service`
- `agent-service`

### Later services (Phases 7+)
- `analytics-service`
- `rl-service`
- `notification-service`

### Infra services
- Postgres + TimescaleDB
- Redis
- (Phase 11+) Kafka, Prometheus, Grafana

## Communication

### MVP (Phases 1–6)
Use **REST** between services. Simpler to debug, faster to build.

### Later (Phase 8+)
Add **Kafka** for streaming concerns: market price feeds, AI task distribution, RL training events.

**Rule:** Commands → REST. Events → Kafka.

## API gateway responsibilities

| Responsibility | Description |
|----------------|-------------|
| Authentication | JWT verification |
| Routing | Forward to internal services |
| Rate limiting | Prevent abuse |
| WebSockets | Real-time price/portfolio streaming |
| API aggregation | Combine multi-service responses |
| Request logging | Audit trail |
| Monitoring | Metrics export |

## Gateway internal layout

```
api-gateway/
├── routes/
├── middleware/
├── websocket/
├── auth/
├── rate_limit/
└── monitoring/
```

## Real-time streaming (Phase 2+)

For MVP, use **FastAPI WebSockets** directly:

```
/ws/prices
/ws/portfolio
/ws/signals
```

For Phase 11+, add Redis Pub/Sub between Kafka and WebSocket nodes for horizontal scaling.

## Internal SDK pattern (Phases 4+)

Don't have services call each other with raw `requests.get(...)`. Build typed SDKs in `packages/sdk/`:

```python
from sdk.market import MarketSDK
prices = await MarketSDK().get_candles("AAPL", "1d")
```

This makes refactoring vastly easier when service boundaries shift.

## Observability (start in Phase 11)

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics |
| Grafana | Dashboards |
| Loki | Logs |
| OpenTelemetry | Tracing |

For MVP just use structured JSON logging + a hosted logger like Logtail or Axiom.

## Security layers

- JWT auth (Phase 1)
- RBAC (Phase 1, basic)
- API keys for external clients (Phase 7+)
- Rate limiting (Phase 1, basic)
- Audit logs (Phase 1, basic)
- Secrets manager (Phase 11+; for MVP use `.env` + Doppler/Railway secrets)

## See also

- [Service topology](../architecture/03-service-topology.md)
- [API contracts](../architecture/04-api-contracts.md)
- [Event-driven design](../architecture/05-event-driven.md)
