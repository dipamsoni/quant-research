# Deployment & Infrastructure

> See [step-09](../plan/step-09-deployment.md) for the full plan and the honest "don't over-engineer" framing.

## Phased infra

| Phase | Frontend | Backend | DB | Real-time | Cost/mo |
|-------|----------|---------|-----|-----------|---------|
| 1-3 | Vercel | Railway / Render | Supabase / Neon | Upstash Redis | $0-80 |
| 4-6 | Vercel | Railway (multi-service) | Supabase | Upstash | $80-300 |
| 7-10 | Vercel | Fly.io or AWS Fargate | RDS Postgres | ElastiCache | $300-2k |
| 11-12 | Vercel or self-hosted CDN | EKS or GKE | RDS + replicas | Kafka cluster | $2k-20k+ |

Move to the next tier ONLY when the current one hurts.

## Local dev

```yaml
# docker-compose.yml (root)
services:
  postgres:
    image: timescale/timescaledb-ha:pg16
    environment:
      POSTGRES_DB: quantos
      POSTGRES_USER: quantos
      POSTGRES_PASSWORD: quantos_local
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U quantos"]
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: ./services/api-gateway
    environment:
      DATABASE_URL: postgresql+asyncpg://quantos:quantos_local@postgres:5432/quantos
      REDIS_URL: redis://redis:6379/0
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
    volumes: ["./services/api-gateway:/app"]

  web:
    build: ./apps/web
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports: ["3000:3000"]
    volumes: ["./apps/web:/app", "/app/node_modules", "/app/.next"]

volumes:
  pgdata:
```

## Staging

Mirror production tooling at smaller scale. Same providers, smaller plans. Auto-deployed from `main` after CI passes.

## Production

### Phase 1-7

- **Frontend:** Vercel — git-integrated, instant rollbacks, zero ops
- **Backend:** Railway or Fly.io — git-integrated, sensible defaults
- **DB:** Supabase or Neon — managed Postgres with branching
- **Redis:** Upstash — serverless, pay-per-request
- **Email:** Resend
- **Errors:** Sentry
- **Logs:** Logtail / Axiom
- **CDN:** Cloudflare

This stack costs <$300/mo and handles thousands of users. Stay here as long as you can.

### Phase 11+

When you outgrow the above (real signal: backend latency degrades, queries pile up, costs spike unpredictably):

- **Cloud:** AWS (most mature ecosystem) or GCP (better ML tooling)
- **Compute:** EKS (k8s) for services; ECS/Fargate fine if you don't need k8s features
- **DB:** RDS Postgres + read replicas; or Aurora for auto-scaling
- **TimescaleDB:** Self-hosted on RDS (extension available) or Timescale Cloud
- **Cache:** ElastiCache Redis cluster
- **Queue/Stream:** MSK (managed Kafka) or self-hosted Redpanda
- **Object storage:** S3
- **Secrets:** AWS Secrets Manager
- **Observability:** Datadog or self-hosted Prometheus + Grafana + Loki
- **CDN/WAF:** Cloudflare in front

## CI/CD pipeline

```
PR opened
    ↓
GitHub Actions
    ├─ Lint (ruff, eslint)
    ├─ Typecheck (mypy, tsc)
    ├─ Test (pytest, vitest)
    ├─ Build images
    └─ Smoke test in ephemeral env
        ↓
PR approved + merged
    ↓
Auto-deploy to staging
    ↓
Smoke tests
    ↓
Manual promote to production (or auto, if confident)
```

## Migration strategy

For DB changes:
1. Generate Alembic migration in PR
2. Review + approve
3. Apply to staging via deploy
4. Verify
5. Apply to production via deploy

NEVER apply migrations manually. NEVER use `--autogenerate` without reviewing the diff.

For breaking schema changes (renames, drops):
- Multi-step: add new → backfill → cut over → drop old
- Coordinate with code releases

## Backups

| Resource | Frequency | Retention | Method |
|----------|-----------|-----------|--------|
| Postgres | Daily snapshot | 30 days | Provider built-in |
| Postgres (full) | Weekly | 6 months | `pg_dump` to S3 |
| Object storage | Versioning on | 90 days | Bucket setting |
| Audit logs | Daily | 1+ year | S3 + lifecycle to Glacier |

Test restore quarterly. A backup you've never restored is a hope, not a backup.

## Disaster recovery

RTO: 4 hours. RPO: 1 hour.

Plan:
1. Provider outage → switch DNS to backup region (manual, documented)
2. DB corruption → restore latest snapshot to fresh instance
3. Bad deploy → roll back container tag (instant)
4. Data leak → revoke credentials, rotate secrets, audit access logs

## Secrets

Never in repo. Never in logs. Never in error messages.

Storage:
- Local: `.env` (gitignored)
- Provider: Doppler, Railway secrets, or Vercel env vars
- Production: AWS Secrets Manager or HashiCorp Vault

Rotate quarterly. After any suspected compromise, immediately.

## Cost monitoring

Set budget alerts on every cloud account. A runaway training job or a recursive Lambda can cost thousands overnight.

Track:
- Total spend per month
- Spend per service
- Spend per user (cost / DAU)
- LLM token spend separately (highest variable cost)

## Anti-patterns

- ❌ Self-hosted Postgres on Phase 1 (use managed)
- ❌ Kubernetes before Phase 11
- ❌ Multi-region before there are users in multiple regions
- ❌ "Cloud-agnostic" architecture from day one (vendor lock-in is fine; switch when forced)
- ❌ Building observability infra instead of using Datadog/Logtail/Sentry
- ❌ Manual deploys to production
