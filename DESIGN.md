# DESIGN

The full design — requirements, architecture, subsystem detail, phase plan with numeric exit
criteria, budget and risk register — lives in **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** and is not
duplicated here.

This file holds the two things that change as the project runs:

1. **[Honesty tiering](#honesty-tiering)** — what is load-bearing versus demonstrative versus
   showcase, for the project as a whole.
2. **[The phase log](#phase-log)** — appended every phase: delivered, skills, trade-offs, scaffolded,
   not run live.

Decisions as they are made: [docs/decision-log.md](docs/decision-log.md).
Per-phase walkthroughs: `docs/phaseN.md`. Concepts: [docs/concepts/](docs/concepts/README.md).

---

## The thesis, in one paragraph

One platform, three capabilities built on it, and a measured answer to *"how much cheaper was the
third one?"* The headline result is not how good any single capability is — it is whether
capability-specific code falls from roughly 2,500 lines to 900 to 350 as the platform absorbs the
work. If that curve does not bend, the abstraction was wrong, and the post-mortem gets published
instead. Everything else exists to make that number real and measured.

The measurement is possible at all because the catalog is **authored**, not scraped: for any query
the correct answer set is a SQL query over data we control, so retrieval quality, grounding and
hallucination are exactly measurable with no human labelling. Roughly 80% of the evaluation surface
is objective and free. The remaining three dimensions — helpfulness, tone, style-sense — need a
judge, and get judge discipline (PROJECT_BRIEF.md §6.3) rather than trust.

---

## Honesty tiering

Per [docs/DOCS_STANDARDS.md](docs/DOCS_STANDARDS.md) §4. Updated each phase. A Tier-3 item must never
be described in language that makes it sound Tier 1.

| Area | Tier | Standing |
|---|---|---|
| Readiness gate (`scripts/health.py`) | **1** | Complete for its purpose |
| Docs format checker (`scripts/check_docs.py`) | **1** | Complete, self-tested |
| Local service stack (Compose) | **2** | Real services and versions, single node, no TLS, no auth, one Postgres role |
| Secret handling | **2** | Correct entropy and idempotent, but plaintext on disk, no rotation or audit |
| Ollama as model server | **2** | Real and GPU-backed, but no routing, failover or accounting yet — Phases 0.2 to 0.4 |
| "Azure-shaped" substitution | **3** | Designed and documented. **Zero lines tested against real Azure** |
| Kubernetes / scale claims | **not built** | Phase 8. Manifests will be written and validated, not deployed — and said so |
| Everything from Phase 1 onward | **not built** | — |

---

## Estimates versus actuals

Budgets from PROJECT_BRIEF.md §9, actuals recorded as phases land.

| Phase | Est. hours | Actual | Est. spend | Actual spend |
|---|---|---|---|---|
| 0.1 | 2 | ~2 | $0 | **$0** |
| 0.2 to 0.6 | 8 | — | ~$3 | — |
| 1 to 8 | ~120 | — | ~$52 | — |

Running spend against the **$80 hard ceiling**: **$0**. Nothing metered has been called yet.

---

## Phase log

### Phase 0.1 — Platform foundation: services up, and proven up

**Exit criterion:** `make up` → all 5 services healthy · `make down` leaves no orphans.
**Result: met.** `5/5 services healthy`, warm start 24s; `make down` → 0 containers, 0 networks,
3 volumes deliberately kept.
**Walkthrough:** [docs/phase0.md](docs/phase0.md).

**Delivered**

- `docker-compose.yml` — Postgres 16, Qdrant v1.12.4, Langfuse v2, MLflow v2.19.0. Images pinned,
  named volumes, no bind mounts, `langfuse` database created by an inlined Compose config.
- Ollama running natively on the host for GPU access, health-checked as the fifth service.
- `scripts/health.py` — the exit criterion as an executable gate. Standard library only, retries to a
  deadline, exits non-zero on failure.
- `scripts/env_init.py` — idempotent secret generation into a gitignored `.env`.
- `scripts/check_docs.py` — mechanical enforcement of the DOCS_STANDARDS formatting rules, with a
  self-test.
- `Makefile`, `pyproject.toml` (ruff, mypy strict, `dependencies = []`), `atelier/` layer skeleton,
  `.gitattributes` forcing LF, `CLAUDE.md`, decision-log entries 9 to 13.
- Docs: this log, `docs/phase0.md`, four concept files and the handbook index.

**Skills exercised**

Container orchestration and lifecycle · the liveness/readiness distinction and why it causes real
outages · designing a gate that fails loudly rather than a report that gets ignored · cryptographic
secret generation and idempotency · treating documentation rules as testable rather than aspirational.

**Trade-offs made** (full reasoning in [docs/decision-log.md](docs/decision-log.md) 9 to 13)

| Chose | Over | Because | Cost accepted |
|---|---|---|---|
| Ollama native on host | Ollama in Compose | GPU without WSL2 passthrough | Stack is not one-command portable to a fresh Linux box |
| Langfuse v2 | Langfuse v3 | 1 container instead of 6, reuses existing Postgres | Postgres-backed ingest will bottleneck at Phase 3 trace volume |
| MLflow on SQLite | MLflow on Postgres | No driver, no second database, no credentials | Single writer only — fine, since there is one |
| Named volumes | Bind mounts | Repo sits on a syncing Google Drive path | Service data is not browsable from the host |
| Host-side health script | More Compose healthchecks | Tests the path a real client uses; Qdrant image has no curl | Docker itself cannot act on the result |
| GNU make | A Python task runner | The brief and CI both speak make | One more tool to install |

**⚠️ Scaffolded — be ready to explain**

- `docker compose up --wait` reports `Healthy` for merely-*running* containers where no `HEALTHCHECK`
  is declared. Verified: only Postgres declares one. This is precisely why the real gate is
  host-side.
- Compose `configs:` with inline `content:` is a recent feature — know the alternatives.
- Langfuse v3's architecture (ClickHouse, Redis, MinIO) and *why* trace analytics wants an OLAP store.
- One Postgres role, and it is the owner. Row-level security in Phase 6 requires this to change.
- No auth on Qdrant or MLflow, no TLS anywhere. Correct for localhost, wrong if exposed.
- 6 GB of VRAM (RTX 2060) is an unanswered question for Phase 4, when a generator, an embedding model
  and Llama Guard 3 may need to coexist.

**Not run live**

Nothing tested against real Azure. No Kubernetes manifest exists yet. No model pulled, so no
inference has happened. Stack only ever started on one Windows machine — never on Linux, never in CI,
never on a second machine. `make clean` never executed.

**Spend:** $0.
