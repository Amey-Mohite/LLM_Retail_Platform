# Recipes stay single-command and shell-agnostic: this runs under cmd.exe on
# Windows and sh in CI. Anything conditional lives in scripts/*.py.
# Windows venv layout. CI on Linux overrides: make gate-0.2 PY=.venv/bin/python
PY ?= .venv/Scripts/python

.PHONY: env up down ps logs health clean gate-0.2

env:
	python scripts/env_init.py

up: env
	docker compose up -d --wait
	python scripts/health.py --wait 180

down:
	docker compose down --remove-orphans

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

health:
	python scripts/health.py

## Phase 0.2 exit criterion: 100 calls, 0 unhandled exceptions, every response accounted.
gate-0.2:
	$(PY) scripts/gate_02.py --calls 100

## Also drops the volumes: catalog, traces and MLflow runs are gone.
clean:
	docker compose down --remove-orphans --volumes
