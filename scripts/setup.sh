#!/usr/bin/env bash
# scripts/setup.sh — one-command setup for new contributors

set -euo pipefail

echo "→ Checking prerequisites..."

command -v node >/dev/null 2>&1 || { echo "Node.js 20+ required. https://nodejs.org"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "pnpm required. Run: npm install -g pnpm"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3.12+ required."; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "uv required. https://github.com/astral-sh/uv"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required. https://docker.com"; exit 1; }

echo "→ Installing JS dependencies..."
pnpm install

echo "→ Installing Python dependencies for api-gateway..."
if [ -d services/api-gateway ]; then
  (cd services/api-gateway && uv sync)
fi

if [ ! -f .env ]; then
  echo "→ Creating .env from .env.example..."
  cp .env.example .env
  echo
  echo "  ⚠️  Edit .env and set JWT_SECRET, JWT_REFRESH_SECRET, INTERNAL_SERVICE_TOKEN."
  echo "     Generate with: openssl rand -hex 32"
  echo
fi

echo "→ Starting Postgres + Redis via Docker Compose..."
docker compose up -d postgres redis

echo "→ Waiting for Postgres..."
sleep 3

if [ -d services/api-gateway/alembic ]; then
  echo "→ Running migrations..."
  (cd services/api-gateway && uv run alembic upgrade head)
fi

echo
echo "✅ Setup complete."
echo
echo "Next steps:"
echo "  1. Review .env values"
echo "  2. Start the full stack: docker compose up"
echo "  3. Open http://localhost:3000"
echo "  4. Read docs/CURRENT_PHASE.md to see what to build first"
echo
