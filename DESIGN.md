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
| Provider interface + enforced token accounting | **1** | Complete: one seam, accounting in the return type |
| Readiness gate (`scripts/health.py`) | **1** | Complete for its purpose |
| Docs format checker (`scripts/check_docs.py`) | **1** | Complete, self-tested |
| Local service stack (Compose) | **2** | Real services and versions, single node, no TLS, no auth, one Postgres role |
| Secret handling | **2** | Correct entropy and idempotent, but plaintext on disk, no rotation or audit |
| `OllamaProvider` | **2** | Real calls, correct usage extraction. No retry, failover or cost yet — Phases 0.3 to 0.4 |
| "Azure-shaped" substitution | **3** | Designed and documented. **Zero lines tested against real Azure** |
| Kubernetes / scale claims | **not built** | Phase 8. Manifests will be written and validated, not deployed — and said so |
| Everything from Phase 1 onward | **not built** | — |

---

## Estimates versus actuals

Budgets from PROJECT_BRIEF.md §9, actuals recorded as phases land.

| Phase | Est. hours | Actual | Est. spend | Actual spend |
|---|---|---|---|---|
| 0.1 | 2 | ~2 | $0 | **$0** |
| 0.2 | 2 | ~2 | $0 | **$0** |
| 0.3 to 0.6 | 6 | — | ~$3 | — |
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

### Phase 0.2 — The provider interface: one seam, and nothing gets through it uncounted

**Exit criterion:** 100 calls through the interface, 0 unhandled exceptions; every response carries
`tokens_in/out`, `model`, `latency_ms`.
**Result: met.** `100/100 complete and fully accounted`, 0 failures, p50/p95 latency 2037/3106 ms,
4109 in / 1124 out tokens, 0.45 calls/s sequential.
**Walkthrough:** [docs/phase0.2.md](docs/phase0.2.md).

**Delivered**

- `atelier/gateway/provider.py` — `Completion` (frozen, self-validating), the `Provider` protocol, and
  `GatewayError`. Accounting lives in the return type, so it cannot be skipped by a caller.
- `atelier/gateway/ollama.py` — the local implementation via Ollama's OpenAI-compatible endpoint.
  Normalises every vendor exception to `GatewayError`, and **raises rather than reporting zero** when a
  response arrives with no usage block.
- `scripts/gate_02.py` — the exit criterion as an executable gate, with a `--self-test` that proves it
  rejects an unaccounted response.
- `make gate-0.2`; `openai` added as the first runtime dependency; decision-log entries 14 to 17.
- Docs: this log, `docs/phase0.2.md`, and the `tokens-and-accounting` concept.

**Skills exercised**

Ports-and-adapters applied to a model provider · making a cross-cutting concern structural rather than
conventional by putting it in a return type · normalising a vendor's exception taxonomy at a seam ·
reading a `usage` block and knowing why a zero is worse than an error · measuring throughput early
enough for it to change a later plan.

**Trade-offs made** (full reasoning in [docs/decision-log.md](docs/decision-log.md) 14 to 17)

| Chose | Over | Because | Cost accepted |
|---|---|---|---|
| Ollama's OpenAI-compatible endpoint | Its native `/api/chat` | Azure and OpenRouter speak the same protocol, so Phase 0.3's adapters become nearly empty | One runtime dependency |
| Accounting enforced by the return type | A helper everyone remembers to call | A guarantee that depends on memory is not a guarantee | A provider without usage data needs an explicit, visible opt-out |
| `max_retries=0` on the client | The client's default retries | Phase 0.3 must *observe* failures to handle them | No resilience at all until 0.3 |
| Raise on a missing usage block | Default to zero tokens | Zero is indistinguishable from a free call and corrupts every later total | A stricter provider contract |
| Venv outside the repo | `.venv` on the Drive | Measured: 149s local versus 9+ min unfinished on the Drive | Venv path is machine-specific, so `PY` is overridable |

**⚠️ Scaffolded — be ready to explain**

- **The seam is not yet enforced.** Nothing stops a future module importing `openai` directly. The
  import-linter contract in Phase 0.6 is what makes the guarantee real; today it is a convention.
- `max_retries=0` — be ready to explain deliberately disabling a resilience feature in order to build
  resilience.
- No `.env` loading yet; the provider falls back to a working default. Phase 0.3 forces the issue.
- `temperature=0` is not determinism — GPU floating-point non-associativity and batching still move
  results between runs.
- **The model does not fully fit in VRAM:** `ollama ps` reports `18%/82% CPU/GPU` for a 7B Q4 at 4096
  context on a 6 GB RTX 2060.

**Not run live**

No Azure call, no OpenRouter call — the "one env var" migration remains untested. No concurrency
tried; every number is sequential. No real failure injection: the provider has never been observed
timing out or being killed mid-request. Nothing has run in CI, on Linux, or on a second machine.

**⚠️ Early warning for Phase 1.6.** 0.45 calls/s sequential. Phase 1.6 requires 20,000 products in
under 6 hours, which is 0.93 items/s — **just over twice the measured rate**, so that batch currently
takes about 12 hours and misses its gate. Levers, to be chosen deliberately in Phase 1 rather than
panicked over now: concurrent requests (`OLLAMA_NUM_PARALLEL`, and the GPU was only at 55%
utilisation), a smaller model on the bulk path, harder output caps, or a smaller context so the model
sits entirely in VRAM.

**Spend:** $0.
