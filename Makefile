.PHONY: up down build logs migrate seed test fuzz lint shell

# ─── Docker ──────────────────────────────────────────────────────────────────
up:
	docker compose --profile dev up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f backend

# ─── Database ─────────────────────────────────────────────────────────────────
migrate:
	docker compose exec backend alembic upgrade head

migrate-down:
	docker compose exec backend alembic downgrade -1

seed:
	docker compose exec backend python seed.py

# ─── Testing ──────────────────────────────────────────────────────────────────
test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing

fuzz:
	docker compose exec backend pytest tests/fuzz/ -v

roles:
	docker compose exec backend pytest tests/test_roles.py -v

# ─── Code quality ─────────────────────────────────────────────────────────────
lint:
	docker compose exec backend ruff check app/ tests/
	docker compose exec backend mypy app/

format:
	docker compose exec backend ruff format app/ tests/

# ─── Utils ────────────────────────────────────────────────────────────────────
shell:
	docker compose exec backend bash

psql:
	docker compose exec postgres psql -U crowdlabel -d crowdlabel

redis-cli:
	docker compose exec redis redis-cli

# ─── Frontend ─────────────────────────────────────────────────────────────────
fe-install:
	cd frontend && npm install

fe-dev:
	cd frontend && npm run dev

fe-build:
	cd frontend && npm run build
