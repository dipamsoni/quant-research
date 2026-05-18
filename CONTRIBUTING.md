# Contributing

## Workflow

1. Pick a task from `docs/phases/phase-<N>.md` (the active phase only)
2. Branch: `git checkout -b feat/<short-name>` (or `fix/`, `refactor/`, `chore/`, `docs/`)
3. Build the feature as a vertical slice: UI + API + DB + tests, all together
4. Tests must pass: `pnpm test`
5. Lint must pass: `pnpm lint`
6. Typecheck must pass: `pnpm typecheck`
7. Push and open a PR
8. CI must be green
9. Squash-merge to `main`

## Branch naming

```
feat/<short-name>      # new feature
fix/<short-name>       # bug fix
refactor/<short-name>  # refactor without behavior change
chore/<short-name>     # tooling, deps, infra
docs/<short-name>      # docs only
```

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat(market-data): add Polygon WebSocket adapter
fix(portfolio): correct PnL on short positions
refactor(api-gateway): extract auth middleware
docs: update phase 2 acceptance criteria
chore(deps): bump fastapi to 0.115
test(backtesting): cover slippage edge case
```

Scope is the affected service / package / area.

## PR checklist

- [ ] Belongs to the current phase (check `docs/CURRENT_PHASE.md`)
- [ ] Tests added/updated
- [ ] Documentation updated if behavior changed
- [ ] Migration added if schema changed
- [ ] No secrets in code or commit history
- [ ] CI green

## Code standards

### TypeScript / Frontend
- TypeScript strict mode
- ESLint + Prettier (auto-format on save)
- shadcn/ui patterns; don't reinvent primitives
- Server state in TanStack Query, client state in Zustand
- Components in `components/` if app-specific, in `packages/ui/` if reusable

### Python / Backend
- Ruff for lint + format
- mypy strict mode for type checking
- Async-first (`async def` + `await`)
- Pydantic models for all schemas
- SQLAlchemy 2.x async style

### Database
- All schema changes via Alembic
- No manual `ALTER TABLE` on staging or production
- Foreign keys explicit `ON DELETE` policies
- Indexes named `idx_<table>_<columns>`

### Tests
- Unit tests for business logic
- Integration tests for full flows (auth, portfolio CRUD, etc.)
- Don't aim for 100% coverage; aim for tests that would hurt to break

## Vertical slice principle

A PR should NOT contain only backend or only frontend for a feature. The slice is:

```
DB migration → SQLAlchemy model → Pydantic schema →
service → repository → API route → SDK client →
React hook → component → page → tests
```

Build the slice end-to-end before merging.

## Phase discipline

If you find yourself building something not in the active phase, stop. Either:
1. Discuss whether the active phase definition is wrong, or
2. Defer the work to its proper phase.

Don't quietly expand scope. The phase gates exist to keep the project shippable.

## Working with Claude Code

This repo is set up for Claude Code:
- Slash commands: `/phase-status`, `/new-service`, `/new-feature`, `/db-migrate`, `/review-plan`
- Subagents: `quant-researcher`, `infra-engineer`, `frontend-architect`
- Project context is in `CLAUDE.md` (root)

Start each session with `/phase-status`.

## Questions

Open a discussion or issue. Don't guess on architecture decisions in silence.
