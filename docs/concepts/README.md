# The concepts handbook

One file per concept: explained generally first, applied to this project last. The bulk of each file
is **portable knowledge** — it should be useful to someone who has never seen this repository.

Each file follows the same shape: a one-line definition, a 🧊 layman analogy, the problem it solves,
how it works with a diagram and a snippet, variations and trade-offs, **interview questions you
should be able to answer**, and a short "in this project" closing note.

---

## Reading order

Written to be read top to bottom. Each assumes the ones above it.

| # | Concept | One line | Phase |
|---|---|---|---|
| 1 | [Service orchestration](service-orchestration.md) | Declaring a multi-service system in one file so it starts with one command | 0.1 |
| 2 | [Health checks and readiness](health-checks-and-readiness.md) | Asking whether a service can serve *now*, rather than inferring it from the process existing | 0.1 |
| 3 | [Configuration and secrets](configuration-and-secrets.md) | Keeping what differs between environments — and what must never leak — out of the code | 0.1 |
| 4 | [Interface substitution](interface-substitution.md) | Depending on an interface you own, so a vendor becomes a swappable detail | 0.1 design, 0.2 code |

Start with **service orchestration** if you are new to containers. Start with **interface
substitution** if you want the idea the whole project is built on — it is the reason this runs on a
laptop for $0 while remaining one config change from Azure.

---

## Concept to phase map

Which phase introduces which concept. Unlinked rows are **not written yet** — they get written by the
phase that introduces them, per [DOCS_STANDARDS.md](../DOCS_STANDARDS.md) §5.

| Phase | Concepts introduced |
|---|---|
| **0.1** | [Service orchestration](service-orchestration.md) · [Health checks and readiness](health-checks-and-readiness.md) · [Configuration and secrets](configuration-and-secrets.md) · [Interface substitution](interface-substitution.md) |
| 0.2 | Tokenisation and token accounting · the provider abstraction in code |
| 0.3 | Retries, timeouts, circuit breakers, fallback chains |
| 0.4 | Cost modelling and spend guards |
| 0.5 | Distributed tracing and OpenTelemetry · experiment tracking |
| 0.6 | Architectural fitness functions — enforcing layer boundaries in CI |
| 1 | Synthetic data as ground truth · structured extraction · abstention and calibration |
| 2 | Embeddings and vector search · chunking · sparse retrieval and BM25 · hybrid fusion · reranking · context assembly and token budgeting |
| 3 | Retrieval metrics — recall@k, nDCG, MRR · golden sets and sealed sets · LLM-as-judge and its discipline · inter-rater agreement · shadow deployment, A/B and sequential testing |
| 4 | Guardrails and fail-closed design · groundedness and hallucination · content safety classification · PII detection · explainability traces |
| 5 | Agent runtimes and tool calling · state machines and resumability · human-in-the-loop checkpoints · multi-agent handoff |
| 6 | Session and long-term memory · multi-tenancy and row-level security · k-anonymity · right to erasure |
| 7 | Measuring reuse — the platform thesis |
| 8 | Model routing and quality-cost frontiers · semantic caching · batching · load testing and capacity arithmetic |

---

## Why this exists

Per [DOCS_STANDARDS.md](../DOCS_STANDARDS.md) §0, this project is also a teaching artifact. The
handbook is the part that outlives the repository: the phase docs explain *what was built here*, and
these explain *the ideas*, which transfer.
