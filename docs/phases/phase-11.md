# Phase 11 — Production Scaling

**Duration:** ~4 weeks
**Goal:** Move from MVP infra (Vercel + Railway) to scalable infra (k8s + observability).

> **Don't start this phase unless you have real traction.** Empty Kubernetes clusters cost money and time without delivering value.

## Trigger conditions (start phase 11 only if)
- 100+ daily active users, OR
- Multiple concurrent backtests blocking each other, OR
- WebSocket connections > 1k concurrent, OR
- Real-time streaming across many services

If none apply, **skip this phase** and stay on managed services.

## Acceptance criteria
- [ ] Production cluster (EKS or GKE) running services
- [ ] Horizontal pod autoscaling on prediction-service and agent-service
- [ ] Kafka cluster (or Redpanda) for event streaming
- [ ] Prometheus + Grafana dashboards live
- [ ] Loki for centralized logs
- [ ] OpenTelemetry tracing
- [ ] Zero-downtime deployments via ArgoCD or Helm
- [ ] Backup + DR plan documented and tested

## Task list

### Week 1: Containers + k8s base
- [ ] Tighten Dockerfiles (multi-stage, distroless where possible)
- [ ] Helm charts per service in `infra/kubernetes/`
- [ ] Kustomize overlays for staging vs production
- [ ] Provision cluster via Terraform (`infra/terraform/`)

### Week 2: Streaming
- [ ] Kafka or Redpanda cluster (3+ brokers)
- [ ] Migrate market price stream to Kafka
- [ ] Migrate WebSocket gateway to consume from Redis Pub/Sub fed by Kafka
- [ ] Topic ACLs

### Week 3: Observability
- [ ] Prometheus scraping all services
- [ ] Grafana dashboards: API latency, Kafka lag, DB queries, agent latency, RL training throughput
- [ ] Loki for logs, with alerts on error rates
- [ ] OpenTelemetry instrumentation across services

### Week 4: GPU + reliability
- [ ] GPU node pool for inference + RL training
- [ ] Spot instances for training, on-demand for inference
- [ ] Backup automation for Postgres (pgBackRest or managed)
- [ ] DR runbook

## Out of scope
- ❌ Multi-region (Phase 12+)
- ❌ Compliance certifications (Phase 12+)

## Pitfalls
- **Premature k8s.** If you're alone with 50 users, k8s is over-engineering.
- **Forgetting cost monitoring.** Set budget alerts. GPU bills can run away fast.
- **Migrating everything at once.** Move one service at a time. Validate. Repeat.
