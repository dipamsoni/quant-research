.PHONY: help setup up down logs ps restart dev test lint typecheck clean migrate seed

help:
	@echo "quant-os Makefile — common commands"
	@echo ""
	@echo "  make setup      Run scripts/setup.sh"
	@echo "  make up         Start the full stack (docker compose up -d)"
	@echo "  make down       Stop the stack"
	@echo "  make logs       Tail logs from all services"
	@echo "  make ps         List running containers"
	@echo "  make restart    Restart all services"
	@echo "  make dev        Run frontend + backend in dev mode (no docker)"
	@echo "  make test       Run all tests"
	@echo "  make lint       Lint everything"
	@echo "  make typecheck  Typecheck everything"
	@echo "  make migrate    Apply DB migrations"
	@echo "  make seed       Seed test data"
	@echo "  make clean      Remove build artifacts and node_modules"

setup:
	./scripts/setup.sh

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

restart:
	docker compose restart

dev:
	pnpm dev

test:
	pnpm test
	cd services/api-gateway && uv run pytest -q

lint:
	pnpm lint
	cd services/api-gateway && uv run ruff check .

typecheck:
	pnpm typecheck
	cd services/api-gateway && uv run mypy app

migrate:
	cd services/api-gateway && uv run alembic upgrade head

seed:
	python scripts/seed_data.py

clean:
	pnpm clean
	rm -rf services/*/.venv services/*/.ruff_cache services/*/.mypy_cache services/*/.pytest_cache
	docker compose down -v
