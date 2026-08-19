# Decision log

Seed entries 1-8 are in [PROJECT_BRIEF.md](../PROJECT_BRIEF.md) section 13. Numbering continues here,
recorded as made.

## 9. Ollama runs natively on the host, not in Compose
**Phase 0.1.** The dev box has an RTX 2060 (6 GB). A containerised Ollama on Windows needs WSL2 GPU
passthrough to use it; the native Windows install picks it up with no configuration. Compose covers
the four stateful services; `scripts/health.py` treats Ollama as a fifth service regardless, so the
phase gate is unchanged. **Cost:** the stack is not one-command portable to a fresh Linux box —
adding an `ollama` service there is ~6 lines when it matters.

## 10. Langfuse v2 (single container), not v3
**Phase 0.1.** v3 is six containers (web, worker, clickhouse, redis, minio, postgres). v2 is one, and
reuses the Postgres already present. What Phase 0.5 needs from it is trace ingest and a trace view,
which v2 does. **Upgrade trigger:** if trace volume from the nightly full matrix (Phase 3) makes v2's
Postgres-backed ingest the bottleneck.

## 11. MLflow on SQLite, not Postgres
**Phase 0.1.** Single-writer local tracking server; a SQLite backend store needs no driver, no second
database and no credentials. Azure ML compatibility is at the *client* API, which is unaffected by
the backend store. **Upgrade trigger:** concurrent run logging, which does not exist here.

## 12. Named volumes, no bind mounts, for service data
**Phase 0.1.** The repo lives on a Google Drive path. Bind-mounting service data from a syncing drive
invites file locks and sync churn; named volumes live in the Docker VM and never touch it. The
`langfuse` database is created by an inlined Compose `config` rather than a mounted init script for
the same reason.

## 13. GNU make, installed, rather than a Python task runner
**Phase 0.1.** The brief's exit criteria are written as `make up` / `make eval` and CI speaks make.
Recipes are kept to single shell-agnostic commands so they run under both `cmd.exe` and `sh`;
anything conditional lives in `scripts/*.py`.
