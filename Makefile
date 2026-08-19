# Recipes stay single-command and shell-agnostic: this runs under cmd.exe on
# Windows and sh in CI. Anything conditional lives in scripts/*.py.
.PHONY: env up down ps logs health clean

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

## Also drops the volumes: catalog, traces and MLflow runs are gone.
clean:
	docker compose down --remove-orphans --volumes
