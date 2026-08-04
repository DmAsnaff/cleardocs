.PHONY: up down build logs shell migrate makemigrations test lint fmt

COMPOSE = docker compose -f infrastructure/docker-compose.yml

# ── Dev lifecycle ──────────────────────────────────────────────────────────────

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

# ── Database ───────────────────────────────────────────────────────────────────

## Create new migration files from model changes (run AFTER all sprints complete)
makemigrations:
	$(COMPOSE) exec backend python manage.py makemigrations

## Apply all pending migrations
migrate:
	$(COMPOSE) exec backend python manage.py migrate --noinput

## First-time setup: create superuser for Django Admin
createsuperuser:
	$(COMPOSE) exec backend python manage.py createsuperuser

## Full DB reset (destructive — dev only)
resetdb:
	$(COMPOSE) exec postgres psql -U cleardocs -c "DROP DATABASE cleardocs; CREATE DATABASE cleardocs;"
	$(MAKE) migrate

# ── Shell access ───────────────────────────────────────────────────────────────

shell:
	$(COMPOSE) exec backend python manage.py shell

bash:
	$(COMPOSE) exec backend bash

psql:
	$(COMPOSE) exec postgres psql -U cleardocs cleardocs

redis-cli:
	$(COMPOSE) exec redis redis-cli

# ── Testing ────────────────────────────────────────────────────────────────────

test:
	$(COMPOSE) exec backend pytest --tb=short -q

test-cov:
	$(COMPOSE) exec backend pytest --cov=. --cov-report=html --cov-fail-under=70

# ── Code quality ───────────────────────────────────────────────────────────────

lint:
	ruff check backend/
	npx --prefix frontend eslint frontend/src

fmt:
	black backend/
	ruff check backend/ --fix
	npx --prefix frontend prettier --write "frontend/src/**/*.{ts,tsx}"

typecheck:
	mypy backend/ --ignore-missing-imports
	npx --prefix frontend tsc --noEmit

# ── Flower (Celery task monitor) ───────────────────────────────────────────────

flower:
	@echo "Flower UI: http://localhost:5555"
	$(COMPOSE) up -d flower
