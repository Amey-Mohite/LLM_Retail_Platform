# LLM Retail Platform (`atelier`)

Design, phases and exit criteria: **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)**.

## Run it

```
make up      # start services, wait, then assert all 5 are healthy
make health  # re-check without starting anything
make down    # stop, remove orphans, keep data
make clean   # ... and drop the volumes
```

`make up` generates `.env` on first run (`scripts/env_init.py`); it is gitignored.

## Services

| Service | Where | URL | Stands in for |
|---|---|---|---|
| Ollama | host, native | http://localhost:11434 | Azure OpenAI |
| Qdrant | docker | http://localhost:6333/dashboard | Azure AI Search |
| Postgres | docker | `localhost:5432` (dbs: `atelier`, `langfuse`) | Cosmos / Azure DB |
| Langfuse | docker | http://localhost:3000 | Azure Monitor / App Insights |
| MLflow | docker | http://localhost:5000 | Azure ML |

Ollama runs natively rather than in Compose so it reaches the GPU without WSL
passthrough. `scripts/health.py` checks it as a service regardless.

## Status

Phase 0.1. See PROJECT_BRIEF.md section 9 for what lands next.
