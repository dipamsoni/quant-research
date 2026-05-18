# Step 9 — Production Deployment Strategy

> MVP deployment is much simpler than the full plan suggests. Read with that in mind.

## Reality vs. plan

The original plan describes a Kubernetes + Kafka + GPU-cluster deployment. **You don't need any of that for the first 6–9 months.** Most of this doc is for Phase 11+.

For MVP through Phase 10, use:
- **Frontend hosting:** Vercel (free tier OK to start)
- **Backend hosting:** Railway, Render, or Fly.io ($5–50/month)
- **Database:** Supabase or Neon ($0–25/month for managed Postgres)
- **Redis:** Upstash ($0 to start)
- **CDN:** Cloudflare (free)
- **Monitoring:** Logtail or Axiom (free tier)

Total: **$0–80/month** until you have real users. Don't pre-spend on infra.

## When to introduce each piece

| Feature | Add when |
|---------|----------|
| Docker Compose (local) | Phase 1 |
| Hosted Postgres + Redis | Phase 1 |
| Vercel + Railway deploys | Phase 1 |
| Cloudflare CDN | Phase 2 |
| Structured logging | Phase 2 |
| Sentry-style error tracking | Phase 3 |
| Hosted vector store | Phase 6 |
| Background job queue (Celery/Dramatiq) | Phase 5 |
| Kafka | Phase 8 (if real-time multi-service streaming) |
| Kubernetes | Phase 11 (only if >10 services + real traffic) |
| GPU infrastructure | Phase 8 (only when actually training RL) |
| Multi-region | Phase 12+ |

## Production architecture (Phase 11+)

```
Cloudflare (CDN/WAF/DNS)
    ↓
Load Balancer
    ↓
Kubernetes Cluster
├── Next.js pods
├── FastAPI gateway pods
├── Service pods (market, portfolio, ML, agent)
└── WebSocket pods
    ↓
Postgres + TimescaleDB | Redis Cluster | Kafka | GPU nodes
```

## Cloud provider

Recommendation: **AWS** for scale, but stay simple for MVP.
- AWS EKS for k8s (Phase 11+)
- RDS for Postgres (or stay with Supabase/Neon)
- S3 for object storage
- Lambda Labs / RunPod for cheap GPU when training RL

Alternative: **GCP** if you're heavy ML; **Azure** for enterprise.

## Containerization

Every service has a Dockerfile from Phase 1. Example FastAPI:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environments

| Env | Purpose |
|-----|---------|
| local | Developer machine |
| development | Shared dev/preview |
| staging | Pre-prod |
| production | Live |

## CI/CD

GitHub Actions from Phase 1. Pipeline:

```
lint → typecheck → test → build → docker → push → deploy staging → smoke tests → deploy prod
```

## Observability stack (Phase 11+)

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics |
| Grafana | Dashboards |
| Loki | Logs |
| Tempo | Tracing |
| OpenTelemetry | Instrumentation |

For MVP: Logtail or Axiom + Sentry is enough.

## Secrets

- MVP: `.env` files + Doppler or Railway secrets
- Phase 11+: AWS Secrets Manager or HashiCorp Vault

**Never** commit secrets. The repo's `.gitignore` blocks `.env*`.

## Backups

| Data | Frequency | Retention |
|------|-----------|-----------|
| Postgres | Daily | 30 days |
| Object storage | Versioning enabled | 90 days |
| Audit logs | Daily | 1+ years |

Most managed Postgres providers (Supabase, Neon) handle this automatically.

## Zero-downtime deployments

Phase 11+:
- Rolling updates (k8s default)
- Blue-green for risky changes
- Canary for ML model rollouts

For MVP: Vercel and Railway handle this for you.

## Cost expectations

| Stage | Monthly cost (rough) |
|-------|----------------------|
| MVP (Phases 1–6) | $0–80 |
| Growth (Phases 7–10) | $200–800 |
| Production scaling (Phase 11+) | $2k–20k+ |

If you find yourself spending $500+/month in Phase 1, you're over-engineering.

## See also

- [Deployment architecture](../architecture/09-deployment.md)
- [Phase 1: local Docker Compose](../phases/phase-1.md)
- [Phase 11: production scaling](../phases/phase-11.md)
