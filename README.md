# LLM Retail Platform (`atelier`)

**Reusable RAG, agent-orchestration and evaluation infrastructure for a fashion e-commerce domain.**

One platform, three capabilities built on it, and a measured answer to *"how much cheaper was the
third one?"* — built with **zero external data**, **zero paid cloud**, and an $80 hard ceiling
enforced in code.

The catalog is authored rather than scraped, which is the point: if we write the products, then for
any query the correct answer set is a SQL query over our own data — so retrieval quality, grounding
and hallucination become **exactly measurable with no human labelling**.

| | |
|---|---|
| **Design, phases, exit criteria** | [PROJECT_BRIEF.md](PROJECT_BRIEF.md) |
| **Honesty tiering + phase log** | [DESIGN.md](DESIGN.md) |
| **Concepts handbook** | [docs/concepts/](docs/concepts/README.md) |
| **Decisions, as made** | [docs/decision-log.md](docs/decision-log.md) |
| **Spend against the $80 ceiling** | **$0** |

---

## Status

| Phase | Delivers | Exit criterion | Tier | Status |
|---|---|---|---|---|
| **0.1** | Service stack, readiness gate, repo skeleton | 5/5 services healthy · clean `down` | 2 | ✅ **met** — [walkthrough](docs/phase0.md) |
| 0.2 | Provider interface + Ollama, token accounting | 100 calls, 0 unhandled exceptions | — | next |
| 0.3 | OpenRouter + Azure providers, failover | Kill primary mid-request → completes on fallback | — | — |
| 0.4 | Spend guard, cost ledger | Counter within 2% of dashboard; guard raises at ceiling | — | — |
| 0.5 | OpenTelemetry → Langfuse, MLflow tracking | One call → one complete trace with cost and route reason | — | — |
| 0.6 | CI, import-linter layer rule | Build fails on a deliberate layer violation | — | — |
| 1 | Synthetic catalog + product understanding | Extraction F1 ≥ 0.85, abstention precision ≥ 0.80 | — | — |
| 2 | Hybrid retrieval | recall@8 ≥ 0.85, p95 < 200 ms | — | — |
| 3 | Evaluation framework | Every metric unit-tested against a hand-computed value | — | — |
| 4 | Guardrails | 0 catalog-membership violations, hallucination ≤ 2% | — | — |
| 5 | Orchestration + stylist | Trajectory accuracy ≥ 0.80 | — | — |
| 6 | Memory, tenant isolation | 0 canary leaks across 10,000 cross-tenant requests | — | — |
| 7 | Shopping copilot | **Capability LOC < 15% of Phase 1** — the headline number | — | — |
| 8 | Routing, caching, framework comparison, scale | ≥ 40% cost cut at ≤ 3% quality loss, as a curve | — | — |

Tiers: **1** load-bearing · **2** demonstrative · **3** showcase. See [DESIGN.md](DESIGN.md).

---

## Quick start

Requires Docker Desktop, Python 3.12+, GNU make, and [Ollama](https://ollama.com) installed natively
(it runs on the host, not in Compose, so it reaches the GPU without WSL2 passthrough).

> **Windows:** if a freshly installed tool reports *"not recognized as the name of a cmdlet"* even
> though it is on PATH, sign out and back in. Terminals inherit their environment from the Explorer
> process that spawned them, so a new window is not enough — see
> [phase0.md §8](docs/phase0.md#8-qa).

```bash
make up
```

First run pulls ~2 GB of images and generates `.env`. It finishes by printing `5/5 services healthy`
— and exits non-zero if it cannot, so it will not tell you the stack is ready when it is not.

| Target | Does |
|---|---|
| `make up` | Generate `.env` if absent, start the stack, **then verify all five services answer** |
| `make health` | Re-check without starting anything |
| `make down` | Stop, remove orphans, **keep** data |
| `make clean` | Stop and **drop the volumes** — catalog, traces and MLflow runs are gone |
| `make ps` / `make logs` | Status · follow logs |

Docs are checked mechanically too:

```bash
python scripts/check_docs.py
```

---

## Services

Every one is a local stand-in for an Azure component, chosen so the *architectural decisions* are the
same even though the spend is $0. Full mapping and migration notes: [PROJECT_BRIEF.md](PROJECT_BRIEF.md) §2.

| Service | Where | URL | Stands in for | Swap difficulty |
|---|---|---|---|---|
| **Ollama** | host, native | http://localhost:11434 | Azure OpenAI | Base URL — both speak the OpenAI protocol |
| **Qdrant** | docker | http://localhost:6333/dashboard | Azure AI Search | Real work: different filter and hybrid APIs |
| **Postgres** | docker | `localhost:5432` — dbs `atelier`, `langfuse` | Cosmos / Azure DB | Low |
| **Langfuse** | docker | http://localhost:3000 | Azure Monitor / App Insights | OpenTelemetry is the portable layer |
| **MLflow** | docker | http://localhost:5000 | Azure ML | Low — Azure ML is MLflow-compatible |

⚠️ **Nothing here has been tested against real Azure.** The substitution is a design, labelled Tier 3.

---

## Repo layout

```
atelier/
├── gateway/        # provider iface (ollama|openrouter|azure), routing, cache, spend guard, OTel
├── grounding/      # ingestion, chunking, hybrid retrieval, rerank, context assembly
├── guardrails/     # membership check, groundedness, safety, PII, explainability traces
├── memory/         # session state, customer profile, tenant isolation
├── orchestration/  # agent runtime, tool registry, state machine, HITL checkpoints
├── capabilities/   # product_understanding · stylist · copilot  (deliberately thin)
├── catalog/        # synthetic catalog generator + ground-truth query engine
└── evals/          # offline golden sets, online harness, pytest suites

docs/               # phaseN.md walkthroughs · concepts/ handbook · decision-log · standards
ops/                # docker-compose, k8s manifests, load tests, CI config
scripts/            # health gate, secret generation, docs checker
```

**Each layer is a dependency of the layer above and knows nothing about it.** A capability may not
call the gateway directly, may not touch Qdrant directly, and may not skip guardrails — enforced from
Phase 0.6 by an import-linter rule in CI, so the architecture is a *test*, not a convention.

---

## Working rules

Contributing, or driving an assistant on this repo? [CLAUDE.md](CLAUDE.md) and
[docs/DOCS_STANDARDS.md](docs/DOCS_STANDARDS.md) are binding. The short version: docs ship with the
code every phase, everything carries an honesty tier, and no phase is done because the code runs —
it is done when it hits its number.
