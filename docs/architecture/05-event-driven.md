# Event-Driven Architecture

> Phase 8+ design. Don't introduce Kafka before Phase 8. See [step-15](../plan/step-15-event-driven.md).

## When to start using events

- ✅ Multiple services need the same data (price tick goes to UI + signal engine + agent)
- ✅ Operation can fail independently (notification queue)
- ✅ Workload is bursty (RL training events)
- ❌ Simple request/response works
- ❌ Adding events for "future-proofing"

## Tooling

- **Phase 8 trial:** Redis Streams (lightweight, already in stack)
- **Phase 11+ production:** Kafka or Redpanda (Kafka-API compatible, faster, easier ops)
- **Schema registry:** start without; add when consumer count > 5

## Topic naming

`<domain>.<entity>.<action>` — past tense for events.

Good: `market.price.updated`, `prediction.signal.generated`, `portfolio.position.closed`
Bad: `update_price`, `signals`, `things`

## Event envelope

```json
{
  "event_id": "uuid",
  "event_version": "v1",
  "event_type": "market.price.updated",
  "timestamp": "2026-05-10T10:00:00Z",
  "source": "market-data-service",
  "correlation_id": "uuid",
  "payload": { "...": "..." }
}
```

Always Pydantic-validate on both produce and consume.

## Producer / consumer responsibilities

### Producer
- Validate payload schema before publishing
- Use `event_id` for idempotency support downstream
- Log on every publish (event_type, key, partition)
- Retry on broker errors with exponential backoff
- DO NOT block request handling on event publishing (publish in background)

### Consumer
- Idempotent processing (handle the same event twice safely)
- Commit offsets only after successful processing
- DLQ on repeated failures (3 retries, exponential backoff, then `<topic>.dlq`)
- Track lag in metrics
- Graceful shutdown: finish current message before exit

## Topic ownership

| Topic | Producer | Consumers |
|-------|----------|-----------|
| `market.price.updated` | market-data | websocket-gateway, prediction, agent |
| `market.news.ingested` | market-data | agent (RAG), analytics |
| `prediction.signal.generated` | prediction | portfolio, agent, websocket |
| `portfolio.position.closed` | portfolio | analytics, notification |
| `agent.research.completed` | agent | notification |
| `rl.episode.completed` | rl | analytics |
| `risk.alert.triggered` | risk | notification, websocket |

## Partitioning

Pick partition keys carefully:
- `market.price.updated` partition by `symbol` (preserve order per symbol)
- `prediction.signal.generated` partition by `user_id` (preserve order per user)
- `portfolio.position.closed` partition by `portfolio_id`

Wrong key choices cause hot partitions and out-of-order processing.

## Retention

| Topic class | Retention |
|-------------|-----------|
| Hot streaming (prices) | 24h |
| Operational events | 7 days |
| Audit / compliance | 1+ years (or move to S3) |
| Debug logs | 24h |

## DLQ pattern

```
producer → topic → consumer
                       ↓ (3 failures)
                   topic.dlq
                       ↓
                   manual review or replay
```

Build a DLQ inspector page (Phase 11) so you can see what's stuck.

## Schema evolution

- Always backward compatible additions (new optional fields OK)
- Breaking changes → new topic version: `market.price.updated.v2`
- Run v1 and v2 in parallel during migration
- Deprecate v1 only after all consumers migrated

## CQRS (Phase 12+, only if needed)

Separate read and write models when:
- Read load >> write load
- Reads need denormalized views

Don't add CQRS for "future-proofing." It's a real complexity tax.

## Event sourcing (Phase 12+, very rarely needed)

Store all state as events; reconstruct by replay. Useful when:
- Compliance requires full audit trail
- You need time-travel debugging

Cost: significant. Most fintech projects do NOT need full event sourcing.

## Local dev

Run Redpanda locally via Docker Compose:
```yaml
redpanda:
  image: redpandadata/redpanda:latest
  command: redpanda start --smp 1 --memory 1G --reserve-memory 0M --overprovisioned --node-id 0 --check=false
  ports: ["9092:9092"]
```

Use `kcat` for topic inspection.

## Observability

Track per topic:
- Throughput (events/sec)
- Consumer lag (messages, time)
- DLQ size
- End-to-end latency (timestamp at produce → timestamp at consume)
- Error rate per consumer group

Prometheus metrics + Grafana dashboards are non-optional once you have events.
