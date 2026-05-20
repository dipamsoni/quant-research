# Step 15 — Event-Driven Architecture Design

> Phase 8+ concern. Don't add Kafka in MVP.

## When to introduce events

Phase 1–7: REST is enough. Use FastAPI WebSockets for real-time UI.
Phase 8+: Add Kafka when you have:
- Real-time market streaming across multiple consumers
- AI agent task distribution
- RL training event streams
- Multi-service coordination beyond what REST handles cleanly

## Architecture (target state, Phase 11+)

```
Market Providers
       ↓
Market Ingestion
       ↓
Kafka topics ──┬─→ Prediction Service
               ├─→ Portfolio Service
               ├─→ Agent Service
               ├─→ Analytics Service
               └─→ RL Service
                       ↓
               Redis Streams
                       ↓
               WebSocket Gateway
                       ↓
               Next.js Frontend
```

## Event categories

| Category | Topic example |
|----------|---------------|
| Market | `market.price.updated` |
| ML | `prediction.signal.generated` |
| Portfolio | `portfolio.position.closed` |
| Agent | `agent.research.completed` |
| RL | `rl.episode.completed` |
| Risk | `risk.alert.triggered` |
| Notification | `notification.email.queued` |

## Topic naming convention

```
domain.entity.action
```

Examples:
- `market.price.updated`
- `market.news.ingested`
- `prediction.signal.generated`
- `portfolio.position.closed`
- `agent.research.completed`
- `risk.alert.triggered`
- `rl.episode.completed`

## Event schema

Always structured. Always versioned.

```json
{
  "event_id": "uuid",
  "event_version": "v1",
  "event_type": "market.price.updated",
  "timestamp": "2026-05-10T10:00:00Z",
  "source": "market-data-service",
  "payload": {
    "symbol": "RELIANCE",
    "price": 2850.45,
    "volume": 1200
  }
}
```

Use Pydantic models for events. Validate on produce and consume.

## Communication patterns

| Pattern | Use case |
|---------|----------|
| Sync REST | CRUD, auth, dashboard fetch |
| Async events | Streaming, fan-out, AI workflows, RL |

**Rule:** Commands → REST. Events → Kafka.

## WebSocket pipeline

```
Kafka topic → Redis Pub/Sub → WebSocket nodes → Frontend
```

Why Redis between Kafka and WebSockets? WS nodes are stateful (per-connection); Redis lets multiple WS nodes share subscriptions cleanly.

## Producer/Consumer ownership

| Producer | Topic |
|----------|-------|
| market-data-service | `market.*` |
| prediction-service | `prediction.*`, `signal.*` |
| portfolio-service | `portfolio.*` |
| agent-service | `agent.*` |
| rl-service | `rl.*` |

| Consumer | Subscribes to |
|----------|---------------|
| analytics-service | All `market.*`, `signal.*`, `portfolio.*` |
| notification-service | `risk.*`, custom user alerts |
| websocket-service | Broadcast subset of all topics |
| agent-service | `market.*`, `signal.*` (for triggered analysis) |

## Failure handling

### Dead Letter Queues (DLQ)

Each topic has a `<topic>.dlq` for failed events:
- `prediction.failed.dlq`
- `agent.failed.dlq`

### Retry policy

- 3 attempts max
- Exponential backoff (1s, 4s, 16s)
- Then DLQ

### Idempotency

Events may process more than once. Every consumer must handle duplicates safely. Use `event_id` for deduplication.

## Event retention

| Topic type | Retention |
|------------|-----------|
| Market data | 7–30 days |
| Audit / compliance | 1–7 years |
| Operational | 7 days |
| Debug logs | 24 hours |

## Distributed state

| Type | Store |
|------|-------|
| Persistent | PostgreSQL |
| Cache | Redis |
| Streaming | Kafka |
| Vectors | pgvector |
| Object | S3/MinIO |

## CQRS (advanced, Phase 12+)

Separate read and write models. Trade execution writes to one model; dashboards read from a denormalized read model. Don't add this until you have actual read/write contention.

## Event sourcing (optional, Phase 12+)

Store all events; reconstruct state by replaying. Benefits: audit, replay, debugging. Cost: complexity. Only add if compliance requires it.

## Observability for events

Track:
- Kafka consumer lag
- Event throughput per topic
- DLQ size
- Retry counts
- End-to-end latency

Tools: Prometheus exporters for Kafka + Grafana dashboards.

## Security

- TLS / mTLS for broker connections
- Service-level auth (each service has its own credentials)
- Topic ACLs (services only produce/consume their owned topics)
- Encrypted payloads for sensitive data (PII, secrets)

## See also

- [Phase 8: introduce Kafka](../phases/phase-8.md)
- [Architecture: event-driven](../architecture/05-event-driven.md)
