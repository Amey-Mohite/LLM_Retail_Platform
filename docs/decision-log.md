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

## 14. The Ollama provider speaks OpenAI's protocol, not Ollama's native API
**Phase 0.2.** Ollama exposes both `/api/chat` (its own shape) and `/v1/chat/completions`
(OpenAI-compatible). The native API needs no dependency at all — `urllib` would do. The
OpenAI-compatible one costs the `openai` package, and buys the entire Phase 0.3 Azure and
OpenRouter adapters, because all three speak the same protocol: same client, different base URL.
Paying one dependency now to make two later adapters nearly empty is the whole "Azure-shaped,
locally-run" claim, honoured in code rather than asserted. **Cost:** one runtime dependency, and a
provider that ever stops being OpenAI-shaped needs a real adapter rather than a config change.

## 15. Accounting is enforced by the return type, not by convention
**Phase 0.2.** `Completion` is frozen and validates in `__post_init__`: a negative token count or a
missing model name raises rather than being recorded. A provider that cannot report usage raises
instead of reporting zero. The point is that there is no way to obtain a model response in this
codebase that is not already accounted for — a guarantee that depends on every future call site
remembering it is not a guarantee. **Cost:** a provider whose API genuinely omits usage cannot be
adapted without either counting tokens locally or explicitly opting out, and that will have to be a
visible decision.

## 16. No retries, timeouts or fallback in 0.2
**Phase 0.2.** The provider raises `GatewayError` and stops. Retry, circuit-breaking and the
fallback chain are Phase 0.3's exit criterion, and building them early would mean the 0.3 gate tests
code that was never observed failing. The one thing done now is normalising the vendor's exception
type, so callers never catch `openai.APIError`.

## 17. The virtualenv is `.venv` in the repository, with a documented escape hatch
**Phase 0.2.** Measured, not assumed: `pip install` into `.venv` on the Google Drive path was still
unfinished after nine minutes having written two packages, while the identical install into a
local-disk venv finished in 149 seconds. A virtualenv is thousands of small files, the pathological
case for a syncing network filesystem.

**Decided: `.venv` stays in the repository**, because the convention is worth more than the minutes —
`pip install -e ".[dev]"` from the repo root is what every contributor and every CI runner expects,
and the `Makefile` default `PY ?= .venv/Scripts/python` then needs no override. **Cost accepted:**
every dependency install on this machine is slow, and that cost recurs each phase that adds a
library. `PY` is overridable precisely so anyone who finds it intolerable can point at a local-disk
venv without editing a tracked file.
