# LLM Retail Platform

**Reusable RAG, agent-orchestration and evaluation infrastructure for a fashion e-commerce domain.**

> A self-contained platform-engineering project: one platform, three capabilities built on it, and a
> measured answer to *"how much cheaper was the third one?"* Built with **zero external data** and
> **zero paid cloud**, while remaining architecturally one config change away from Azure.

**Status:** Planning
**Owner:** Amey Mohite
**Started:** 2026-08-16
**Target:** ~13 weeks part-time (~10 hrs/week)
**Budget ceiling:** $80

**Naming:** repo `llm-retail-platform` · Python package `atelier` (`platform` is a stdlib module —
never name a package that).

---

## 0. The role this targets, and the one sentence that shapes everything

> *"We're looking for someone who thinks in **systems, not features** — with strong abstraction
> capability and a mindset of **building once and reusing at scale**."*

That is the filter. Most candidates will show a RAG demo. A RAG demo is a *feature*.

This project is therefore structured as **one platform plus three capabilities built on top of it** —
and the headline result is not how good any single capability is, but **how much cheaper the third
capability was to build than the first**. That number is the entire pitch.

| Capability | Built in | New platform code required |
|---|---|---|
| 1. Product understanding (structured attribute extraction) | Phase 1 | *builds the platform* |
| 2. Stylist reasoning (multi-item outfit composition, agentic) | Phase 5 | target: < 40% of #1 |
| 3. Shopping copilot (conversational discovery) | Phase 7 | **target: < 15% of #1** |

If capability #3 takes 300 lines and two days because the platform already does retrieval, memory,
guardrails, evaluation, tracing, routing and cost control — *that* is the proof of platform thinking.
Everything else in this document exists to make that number real and measured.

---

## 1. Hard constraints

1. **No external data.** No scraped catalogs, no licensed datasets, no real customer queries.
   Base model weights are permitted (artifacts, not data). Everything else is synthesised — which,
   as §3 explains, is a methodological *advantage*, not a compromise.
2. **No paid cloud.** Everything runs locally. Azure equivalence is achieved by interface, not by
   spend (§2).
3. **$80 ceiling**, enforced by a hard counter in the gateway. Spent only on the evaluation judge and
   frontier-model baselines.
4. **Every claim reproducible** by `make eval` from a clean checkout at a fixed seed.

---

## 2. Azure-shaped, locally-run

The JD wants Azure OpenAI, Azure AI Studio, Azure ML, Cognitive Services, AKS. Paying for those to
learn them is unnecessary — every one has a local equivalent that exposes the **same architectural
concepts**, and in the most important case (Azure OpenAI) literally the same API.

| Azure component | Local substitute | Cost | How close is it, honestly? |
|---|---|---|---|
| **Azure OpenAI** | **Ollama** OpenAI-compatible endpoint + **OpenRouter** | £0 / metered | **Drop-in.** Same `openai` SDK, different `base_url`. Migration = one env var. |
| **Azure AI Search** (vector + hybrid) | **Qdrant** (Docker, local) | £0 | Very close. HNSW, payload filters, hybrid dense+sparse — same concepts, same tuning decisions. |
| **Azure ML** (experiment tracking, model registry) | **MLflow** (self-hosted) | £0 | Very close. Azure ML *is* MLflow-compatible; runs port over directly. |
| **Azure AI Content Safety** | **Llama Guard 3** via Ollama + rule layer | £0 | Different implementation, identical integration point. Swappable behind the guardrail interface. |
| **Azure Monitor / App Insights** | **Langfuse** (self-hosted) + **OpenTelemetry** | £0 | OTel is the portable layer; exporters swap. |
| **AKS / scalable compute** | **Docker Compose** locally + committed k8s manifests + load test | £0 | Manifests written and validated, not deployed. Scale claims backed by measured throughput math, not adjectives. |
| **Azure Blob / Cosmos** | Local FS + **SQLite** / **Postgres** in Docker | £0 | Storage is the least interesting part; abstracted behind a repository interface. |

**The rule:** every external dependency sits behind an interface with **two implementations** — the
local one, and a documented Azure one. `docs/azure-migration.md` states, per component, exactly what
changes. Where the Azure implementation is trivial (the gateway), it is written and left untested
against real Azure, and *that fact is stated*.

**This is itself the JD's "model selection trade-offs" and "reusable infrastructure" competency
demonstrated in the build, not claimed in a CV bullet.**

---

## 3. Core thesis — synthetic catalog gives *perfect* ground truth

The no-external-data constraint looks like a handicap. In retail RAG it is the opposite.

> If **I author the product catalog**, then for any query I know the exact correct result set —
> so retrieval quality, grounding, and hallucination become **exactly measurable with zero human
> labelling**.

This is the single idea the project's rigour rests on:

- **Retrieval correctness.** I generate a catalog of ~20,000 synthetic products with fully structured
  attributes (category, material, colour, fit, occasion, price band, sizes in stock, season). For the
  query *"linen shirt under £40, in a size 12, for a summer wedding"* the correct answer set is a
  **SQL query over my own data**. So `recall@k`, `nDCG@10`, and `MRR` are computed against exact
  ground truth, on thousands of queries, for free.
- **Hallucination detection is exact, not fuzzy.** If the copilot names a SKU, quotes a price, or
  claims a material — I check it against the catalog. It either exists and matches, or it doesn't.
  No judge, no ambiguity. Most projects approximate this with an LLM grader; here it's a lookup.
- **Groundedness is exact.** Every factual claim in a response must be attributable to a retrieved
  document. Since I control the documents, attribution is verifiable programmatically.
- **Agent trajectory correctness.** For stylist reasoning, I author scenarios *with* the correct tool
  sequence and the correct final outfit constraints, so trajectory accuracy is measurable.

Three things still need a judge: *helpfulness*, *tone*, and *style-sense* (does this outfit actually
work?). Those follow strict judge discipline (§7.3).

**Net: roughly 80% of the evaluation surface is objective, exact, and free.**

---

## 4. Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          CAPABILITIES (thin)                              │
│   Product Understanding  │  Stylist Reasoning  │  Shopping Copilot        │
└───────────┬──────────────────────┬──────────────────────┬─────────────────┘
            │                      │                      │
┌───────────▼──────────────────────▼──────────────────────▼─────────────────┐
│                        ORCHESTRATION LAYER                                 │
│   agent runtime · tool registry · state machine · multi-agent patterns     │
│   human-in-the-loop checkpoints · event-driven step execution              │
├────────────────────────────────────────────────────────────────────────────┤
│                          GROUNDING LAYER                                   │
│   hybrid retrieval (dense+sparse) · rerank · attribute filters             │
│   query understanding · context assembly + token budgeting                 │
├────────────────────────────────────────────────────────────────────────────┤
│                        GUARDRAIL LAYER                                     │
│   catalog-membership check · groundedness scorer · content safety          │
│   PII scrub · explainability trace emitter · fail-closed policy            │
├────────────────────────────────────────────────────────────────────────────┤
│                          MEMORY LAYER                                      │
│   session state · customer profile (tenant-isolated) · preference decay    │
├────────────────────────────────────────────────────────────────────────────┤
│                      MODEL GATEWAY (the foundation)                        │
│   routing · failover · semantic cache · batching · token accounting        │
│   spend guard · OTel traces → Langfuse · Azure-swappable provider iface    │
└────────────────────────────────────────────────────────────────────────────┘
            ▲                                                    ▲
            │                                                    │
   ┌────────┴────────┐                              ┌────────────┴──────────┐
   │  EVAL FRAMEWORK │                              │   LLMOps               │
   │  offline: golden sets, retrieval metrics       │   MLflow experiments   │
   │  online: shadow, A/B, guardrail trip rates     │   CI regression gates  │
   └─────────────────┘                              └────────────────────────┘
```

**Every layer is a dependency of the layer above and knows nothing about it.** A capability may not
call the gateway directly, may not touch Qdrant directly, and may not skip guardrails. Enforced by an
import-linter rule in CI — architectural discipline as a *test*, not a convention.

### 4.1 Stack

Chosen, not surveyed.

| Concern | Choice | Why not the alternative |
|---|---|---|
| Language | Python 3.11+, strict typing | — |
| Bulk inference | **Ollama** (local) | Free + unlimited → the full eval suite runs nightly at £0. Metered inference is what kills eval-driven projects. |
| Judge + frontier baselines | **OpenRouter** | Different model family from the generator (§7.3). Low volume, metered. |
| Vector search | **Qdrant** (Docker) | Real HNSW, payload filtering, hybrid. Maps 1:1 to Azure AI Search decisions. Not pgvector — filtering ergonomics matter for retail attributes. |
| Sparse retrieval | **BM25** (`rank_bm25`) | Hybrid is non-optional in retail — see the §8 case study. |
| Reranking | **bge-reranker** cross-encoder, local | The single highest-leverage retrieval component; cheap on CPU for top-50. |
| Embeddings | **BGE-small / E5** local | Free, fast, and swapping embedding models becomes a measurable experiment rather than a guess. |
| Orchestration | **~400-line custom agent runtime** | See §5.3 — deliberate, and benchmarked against Semantic Kernel in Phase 8. |
| Experiment tracking | **MLflow** self-hosted | Azure ML is MLflow-compatible; runs port over. |
| Observability | **Langfuse** self-hosted + **OpenTelemetry** | OTel keeps it portable; Langfuse gives LLM-native trace views. |
| Storage | **Postgres** (Docker) + local FS | Multi-tenant isolation is a Phase 6 deliverable; needs real row-level security. |
| Eval runner | **pytest** parametrized | Combinatorial matrices + CI gating for free. No custom harness — that's the classic wasted month. |
| Safety classifier | **Llama Guard 3** via Ollama | Swappable behind the guardrail interface with Azure Content Safety. |

### 4.2 Repo layout

```
atelier/
├── gateway/        # provider iface (ollama|openrouter|azure), routing, cache, spend guard, OTel
├── grounding/      # ingestion, chunking, hybrid retrieval, rerank, context assembly
├── guardrails/     # membership check, groundedness, safety, PII, explainability traces
├── memory/         # session state, customer profile, tenant isolation
├── orchestration/  # agent runtime, tool registry, state machine, HITL checkpoints
├── capabilities/
│   ├── product_understanding/
│   ├── stylist/
│   └── copilot/
├── catalog/        # synthetic catalog generator + ground-truth query engine
├── evals/          # offline golden sets, online harness, pytest suites
├── ops/            # docker-compose, k8s manifests, load tests, CI config
└── docs/           # azure-migration, decision-log, findings, governance, scale
```

---

## 5. Key subsystem designs

### 5.1 The synthetic catalog (the foundation of all measurement)

Not a toy. It's generated to be *hostile to naive retrieval*, on purpose:

- ~20,000 products, structured attributes + generated unstructured descriptions
- **Deliberate near-misses:** linen vs. linen-blend vs. "linen-look"; 30 shades of black; "midi" vs.
  "middi" vs. "mid-length"; the same silhouette named differently across categories
- **Realistic stock/price distributions** so `size 12 in stock under £40` is a genuinely restrictive filter
- **Seasonality and trend labels** so recommendations can be temporally wrong
- **A ground-truth query engine:** any natural-language test query is authored alongside the SQL that
  defines its correct answer set

Building the catalog adversarially is what makes the retrieval metrics *mean* something. A catalog of
1,000 obviously-distinct products would make every retriever look perfect.

### 5.2 Grounding layer — retrieval as the real bottleneck

The §8 case study argues that in retail, **retrieval failure masquerades as hallucination**. The
layer is therefore built to be measured component-by-component:

- **Query understanding:** decompose NL query → `{semantic intent, hard filters, soft preferences}`.
  Hard filters (size, price, stock) go to the DB, never to the embedding. This is where most retail
  RAG dies — `under £40` embedded into a vector is meaningless.
- **Hybrid retrieval:** dense (BGE) + sparse (BM25) with Reciprocal Rank Fusion. Retail has exact
  tokens — brand names, SKUs, "cargo", "peplum" — that dense retrieval smears.
- **Rerank:** cross-encoder over top-50 → top-8.
- **Context assembly:** token-budgeted, priority-slotted, overflow degrades predictably and is logged.

Each stage is independently ablatable, so "retrieval improved 22%" can be attributed to a *component*.

### 5.3 Orchestration — and the framework decision, made explicitly

The JD names Semantic Kernel and LangChain. The core is nonetheless a **~400-line custom agent
runtime**, for three stated reasons:

1. The orchestration layer *is* the deliverable. A framework hides exactly the abstraction being
   demonstrated.
2. Token accounting, trace emission, and guardrail enforcement must be *unbypassable*. Framework
   escape hatches make that a convention rather than a guarantee.
3. Debuggability. A senior engineer should be able to justify a build-vs-buy call with evidence.

**And then it is tested honestly:** Phase 8 reimplements the stylist agent in **Semantic Kernel** and
publishes a comparison — LOC, latency, token overhead, trace fidelity, debuggability, time-to-first-
working. If SK wins, that goes in `docs/findings.md`. Demonstrating the *judgment* is the point;
"I built my own because frameworks are bad" without a comparison is not senior, it's stubborn.

Runtime supports: tool registry with typed schemas, a step state machine (resumable, event-driven),
multi-agent handoff, **human-in-the-loop checkpoints** (JD requirement: *"autonomous + human-in-the-
loop patterns"*), and per-run token/cost budgets that halt rather than overrun.

### 5.4 Guardrails — fail-closed, with exact ground truth

Ordered pipeline, every stage emitting to the explainability trace:

| Guard | Mechanism | Ground truth |
|---|---|---|
| **Catalog membership** | Every SKU / price / material claim checked against the catalog | **Exact.** Non-existent product = hard fail, response blocked |
| **Groundedness** | Every factual claim attributed to a retrieved doc | Exact — I control the docs |
| **Attribute fidelity** | Claimed attributes vs. actual attributes | Exact |
| **Content safety** | Llama Guard 3 + rule layer | Adversarial prompt set, authored |
| **PII** | NER scrub inbound + outbound, verified second pass | Injected synthetic PII, exact recall measurable |
| **Budget** | Token/cost ceiling per request | Exact |

**Fail-closed policy:** a guardrail failure blocks the response and returns a degraded-but-safe
answer. It never logs a warning and ships. This is the *"partner with Trust & Security to embed AI
risk controls by design"* line, implemented.

**Explainability output** for every response: which products were retrieved and why, which filters
fired, which tools ran, which guards passed, what it cost, which model served it. Retail
recommendations that can't be explained can't be debugged, defended to a regulator, or trusted by
merchandisers.

### 5.5 Memory and multi-tenant isolation

Customer preference data (sizes, brands, style history) is personal data under UK GDPR — real, not
theoretical, for a UK retailer.

- **Session state** — ephemeral, TTL'd
- **Customer profile** — durable, tenant-partitioned, Postgres row-level security, right-to-erasure implemented as an actual working endpoint
- **Global patterns** — abstracted, k-anonymised (≥ 50 customers), entity-scrubbed before promotion

**Isolation test, CI-blocking:** plant unique canary tokens in 200 customer profiles, run 10,000
requests as *other* customers, grep every output, trace, cache entry and log. **Any hit fails the
build.** Semantic caches are a notorious cross-tenant leak vector — the cache key includes the tenant
scope, and this test is what proves it.

### 5.6 Cost and token-aware design

JD nice-to-have, treated as core because it's where platform thinking shows:

- **Model routing:** a cheap classifier decides small-vs-large model per request. Measured: quality
  delta vs. cost delta, plotted as a frontier. The deliverable is *the curve*, so a product owner can
  choose a point.
- **Semantic cache:** embedding-similarity cache with tenant-scoped keys; hit rate and false-hit rate both measured (a semantic cache that returns a *wrong* cached answer is worse than no cache).
- **Batching** for offline capabilities (product understanding over 20k items).
- **Token budgeting** enforced in context assembly, not hoped for.
- Every response carries `cost_usd`, `tokens_in/out`, `model`, `cache_hit`, `route_reason`.

---

## 6. Evaluation framework — offline and online

The JD asks for both explicitly.

### 6.1 Offline

| Suite | Size | Runtime | Gate |
|---|---|---|---|
| Smoke | 60 cases | < 3 min | every commit (pre-commit hook) |
| Retrieval golden set | 2,000 queries | ~20 min | every PR |
| Full capability matrix | 5,000+ cases | ~4 hrs | nightly |
| **Sealed adversarial set** | 300 cases | ~30 min | **release only — never used during iteration** |

Metrics: `recall@k`, `nDCG@10`, `MRR`, groundedness rate, hallucination rate, attribute fidelity,
trajectory accuracy, guardrail precision/recall, p50/p95 latency, cost/request.

### 6.2 Online

There are no real users, so "online" is simulated — but the *mechanism* is the real one:

- **Simulated shopper population:** intent × urgency × specificity × budget-sensitivity × patience,
  combinatorially sampled and seeded
- **Shadow mode:** new version scored on live-ish traffic without serving it
- **A/B harness** with proper sequential testing, not eyeballed averages
- **Online guardrail telemetry:** trip rates, degradation rates, fallback depth
- **Automatic rollback** on gate regression

### 6.3 Judge discipline

For the three subjective dimensions (helpfulness, tone, style-sense):

- **Pairwise only**, never absolute scores
- **Judge family ≠ generator family**; judge version pinned per release and recorded
- **Position-swapped duplicate**; disagreement counts as a tie
- **200-pair human calibration** rated by me → Cohen's κ reported. If κ < 0.4, judged metrics are
  labelled *directional only* in the README

**The closed-loop risk is stated, not hidden:** synthetic data + LLM judging can measure improvement
against your own biases. Mitigation is that the objective metrics (§3) are the primary gate and never
touch a judge; the sealed set is opened once per release; and κ is always published.

---

## 7. The reuse metric — the headline result

Measured, not asserted. For each capability:

- Lines of **capability-specific** code vs. platform code reused
- Number of new platform primitives required
- Wall-clock hours from spec to passing eval gate
- Which platform layers were used unchanged

Published as `docs/findings.md#reuse`. The target curve is **~2,500 → ~900 → ~350 lines**. If it
doesn't bend, the platform failed and I say so — a flat curve means the abstraction was wrong, which
is a genuine, publishable finding about my own design.

---

## 8. Case study (the template every finding follows)

Numbers are **illustrative targets**, replaced by measured values as the project runs.

> ### CASE: The hallucination that wasn't a hallucination
>
> **1. SIGNAL**
> Nightly full matrix flags attribute-fidelity failures at 18% on the copilot. The model describes
> products with materials and fits they don't have. Classic hallucination signature.
>
> **2. CLUSTER**
> 1,847 failing turns cluster hard: 71% involve a **material or fit constraint** in the query
> ("linen", "oversized", "high-waisted", "non-sheer").
>
> **3. ROOT CAUSE — three hypotheses, ablated rather than assumed**
> - *(a)* Model hallucinating attributes → the obvious read
> - *(b)* Prompt insufficiently strict about only using retrieved data
> - *(c)* **Retrieval returning attribute-wrong items**, which the model then describes *faithfully*
>
> Ablation results:
> - Strengthen prompt constraints *(b)* → 18% → 15.2%
> - Swap to a larger, stronger model *(a)* → 18% → 16.1%
> - Inspect retrieval directly *(c)* → **`recall@8` for material-constrained queries is 0.41.**
>   Dense embeddings place "linen shirt" and "cotton shirt" at cosine 0.94. The retriever hands the
>   model cotton; the model accurately describes cotton; the eval calls it a hallucination.
>
> **Cause is (c). The model was never hallucinating.** It was correctly describing wrong inputs.
>
> **4. FIX**
> Query understanding extracts material/fit as **hard filters** routed to Qdrant payload filters and
> BM25, not to the dense vector. Hybrid fusion + cross-encoder rerank on top.
>
> **5. REGRESSION GATE**
> | Metric | Before | After | Gate |
> |---|---|---|---|
> | Attribute fidelity failure | 18.0% | 2.3% | ✅ target < 5% |
> | `recall@8` (material-constrained) | 0.41 | 0.89 | ✅ |
> | `nDCG@10` (all queries) | 0.62 | 0.79 | ✅ no regression |
> | Catalog-membership violations | 0 | 0 | ✅ must be 0 |
> | Tenant leakage canaries | 0 | 0 | ✅ must be 0 |
> | p95 latency | 840ms | 910ms | ✅ < 1200ms |
> | Cost / request | $0.0021 | $0.0019 | ✅ (smaller model now sufficient) |
> | Judged helpfulness (sealed, pairwise) | — | 64% win | ✅ > 55% |
>
> **6. SHADOW → CANARY → PROMOTE**
> Shadow 5,000 requests, canary 10%, no gate regression, promoted.
>
> **7. WHAT THIS DEMONSTRATES**
> Three of the four instincts a team would reach for — bigger model, stricter prompt, more context —
> were worth ~3 points between them. Fixing the **retrieval architecture** was worth 15.7.
> *And it made the system cheaper, because a smaller model suffices once the inputs are correct.*
>
> This is the argument the whole project exists to make: **at scale, the bottleneck is almost never
> the model.** Finding that requires evaluation infrastructure, which is why the platform is built
> evaluation-first.

---

## 9. Phases

Every phase has a **numeric exit criterion**. No phase is done because the code runs.

Each phase splits into **subphases sized to one sitting** (~1–4 hrs at 10 hrs/week), and every subphase
carries its own number. Progress is therefore visible weekly rather than fortnightly, and a subphase
that misses its number is a stop-and-look signal before two weeks of work is built on top of it.
Hour estimates are budgets, not predictions; the `h` column sums to the phase's week allocation.

---

### Phase 0 — Platform foundation: gateway, telemetry, LLMOps
**Week 1** · ~10 hrs · ~$3

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **0.1** | Repo skeleton, `atelier/` package layout, Docker Compose: Ollama, Qdrant, Postgres, Langfuse, MLflow | `make up` → all 5 services healthy; `make down` leaves no orphans | 2 |
| **0.2** | Provider interface + `ollama` implementation; token accounting on every response | 100 calls through the interface, 0 unhandled exceptions; every response carries `tokens_in/out`, `model`, `latency_ms` | 2 |
| **0.3** | `openrouter` + `azure` implementations; retry, timeout, circuit-break, fallback chain; `docs/azure-migration.md` §gateway | Kill the primary provider mid-request → completes on fallback, traced, no exception surfaces | 2 |
| **0.4** | Hard spend guard that raises; cumulative cost ledger | Spend counter within 2% of the OpenRouter dashboard; guard raises at the ceiling in test; 1,000 sequential calls, 0 unhandled exceptions | 1.5 |
| **0.5** | OpenTelemetry instrumentation → self-hosted Langfuse; MLflow tracking server | One call → one complete trace carrying cost, model and route reason; one MLflow run logged end-to-end | 1.5 |
| **0.6** | CI skeleton, import-linter architectural rule (§4), `make` targets `smoke` / `eval` / `report` | Import-linter fails the build on a deliberate `capabilities → gateway` import (committed as a red test, then reverted) | 1 |

---

### Phase 1 — Synthetic catalog + Capability #1: Product Understanding
**Weeks 2–3** · ~20 hrs · ~$5

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **1.1** | Attribute schema + taxonomy; the near-miss table (linen / linen-blend / "linen-look", midi / middi / mid-length, 30 shades of black) authored *before* generation | ≥ 8 attribute families defined; ≥ 40 near-miss families enumerated and committed | 2 |
| **1.2** | Catalog generator → 20k products: structured attributes + generated descriptions, realistic stock / price / season distributions | 20k products generated; the fixed seed regenerates byte-identical output | 4 |
| **1.3** | Adversarial hardening pass, measured with a throwaway ~20-line dense-only probe retriever (a difficulty meter, **not** the Phase 2 retriever) | Probe scores `recall@8` **< 0.6** on attribute-constrained queries. Higher means the catalog is too easy → regenerate. §11's top risk, checked in week 2 instead of week 5 | 3 |
| **1.4** | Ground-truth query engine: NL query ↔ authored SQL answer set | 50 seed queries each with its SQL; 10 hand-verified row by row | 3 |
| **1.5** | Capability #1: description → structured attributes, with confidence + abstention | Attribute extraction F1 ≥ 0.85; **abstention precision ≥ 0.80** — when it declines, it is right to decline | 4 |
| **1.6** | Batch pipeline over all 20k items | Full batch < 6 hrs locally at £0; throughput and cost/item recorded | 2 |
| **1.7** | **Reuse baseline.** The LOC counting rule — what is capability code vs platform code — written down | Rule committed **before Phase 7 is designed**; Phase 1 LOC, wall-clock hours and primitives-built recorded | 1 |

---

### Phase 2 — Grounding layer: hybrid retrieval
**Weeks 4–5** · ~20 hrs · ~$4

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **2.1** | Ingestion + chunking strategy comparison, tracked as MLflow experiments | ≥ 3 strategies logged as runs; the winner chosen on a logged number, not on taste | 3 |
| **2.2** | Dense-only retrieval in Qdrant — deliberately the naive baseline | `recall@8` and `nDCG@10` recorded. **This is the number every later gain is measured against** | 2 |
| **2.3** | Query understanding → `{intent, hard filters, soft preferences}` | Filter-extraction F1 ≥ 0.90; a test asserts hard filters (size, price, stock) **never reach the embedding** | 4 |
| **2.4** | BM25 sparse retrieval + Reciprocal Rank Fusion | `recall@8` on exact-token queries (brand names, "cargo", "peplum") beats 2.2 by a recorded delta | 3 |
| **2.5** | Cross-encoder rerank, top-50 → top-8 | `nDCG@10` ≥ 0.75; rerank latency fits inside the p95 budget | 2 |
| **2.6** | Context assembly: token-budgeted, priority-slotted | A test asserts the budget is never exceeded; overflow degrades predictably and is logged | 2 |
| **2.7** | 2,000-query golden set, each with its authored SQL answer set | Committed, seeded, reproducible | 3 |
| **2.8** | Ablation harness — every stage independently switchable | `recall@8` ≥ 0.85 overall **and** ≥ 0.85 on attribute-constrained queries (the §8 trap); retrieval p95 < 200 ms; ablation table published | 1 |

---

### Phase 3 — Evaluation framework (offline + online)
**Weeks 6–7** · ~20 hrs · ~$12

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **3.1** | Metric implementations: `recall@k`, `nDCG@10`, `MRR`, groundedness, hallucination rate, attribute fidelity, trajectory accuracy | **Every metric has a unit test with a hand-computed expected value.** An untested metric is a rumour | 4 |
| **3.2** | Four-tier parametrized pytest suites (§6.1) + pre-commit wiring | Smoke < 3 min on pre-commit; full matrix < 4 hrs; tiers selectable by marker | 3 |
| **3.3** | Sealed adversarial set, 300 cases | Committed and git-locked, content hash recorded in the README, **unopened** | 2 |
| **3.4** | Judge harness: cross-family, position-swapped, version-pinned | A test asserts position disagreement scores as a tie; judge model + version recorded on every run | 3 |
| **3.5** | 200-pair human calibration, rated by me | Cohen's κ computed and published; README labels judged metrics *directional only* if κ < 0.4 | 3 |
| **3.6** | Simulated shopper population: intent × urgency × specificity × budget-sensitivity × patience | Seeded, combinatorially sampled, reproducible across runs | 2 |
| **3.7** | Shadow mode + A/B harness with sequential testing; automatic rollback on gate regression | Harness detects a **deliberately planted 5% regression** at the declared power; rollback fires | 3 |
| **3.8** | MLflow-backed run comparison + static HTML report generator | `make report <run-id>` produces the HTML from a run id | 1 |

---

### Phase 4 — Guardrails and safety
**Week 8** · ~10 hrs · ~$5

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **4.1** | Ordered guard pipeline (§5.4), fail-closed, with the degraded-but-safe fallback response | A deliberately failing guard blocks the response; a test asserts **no bypass path exists** | 1.5 |
| **4.2** | Catalog-membership + attribute-fidelity checkers (exact, §3) | Catalog-membership violations: **0** on the full matrix — build-breaking | 2 |
| **4.3** | Groundedness scorer — every factual claim attributed to a retrieved doc | Groundedness ≥ 0.95; hallucination rate ≤ 2% | 2 |
| **4.4** | Llama Guard 3 behind the safety interface + rule layer + 400-case adversarial prompt set | Safety recall ≥ 0.95 **and** false-positive rate ≤ 5% — both directions gated, because blocking legitimate shopping queries is a product failure, not a safety win | 2.5 |
| **4.5** | PII scrub inbound + outbound, verified on a second pass | PII recall ≥ 0.98 on injected synthetic PII | 1.5 |
| **4.6** | Explainability trace emitter on every response | Smoke asserts every response carries a complete, human-readable trace: what was retrieved and why, which filters fired, which tools ran, which guards passed, what it cost, which model served it | 1.5 |

---

### Phase 5 — Orchestration + Capability #2: Stylist Reasoning
**Weeks 9–10** · ~20 hrs · ~$10

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **5.1** | Tool registry with typed schemas | A tool invoked with wrong types is rejected **before** execution, not inside it | 2 |
| **5.2** | Step state machine — resumable, event-driven | Kill mid-run → resume from serialised state → identical final outcome | 4 |
| **5.3** | Per-run token/cost budget that halts rather than overruns | A deliberately looping agent halts cleanly at the ceiling; never loops | 1.5 |
| **5.4** | Human-in-the-loop checkpoints | Demonstrably pauses, serialises and resumes **across a process restart** | 2.5 |
| **5.5** | Multi-agent handoff | Handoff preserves context *and* budget accounting across agents; asserted | 2 |
| **5.6** | 500 authored scenarios, each with its correct tool sequence and outfit constraints | Committed, seeded | 3 |
| **5.7** | Capability #2: multi-item outfit composition under constraints (occasion, budget, sizes in stock, weather, existing wardrobe) | Trajectory accuracy ≥ 0.80 against authored sequences; constraint satisfaction ≥ 0.95 (budget, stock, size — all objectively checkable) | 4 |
| **5.8** | **Reuse metric #2**, recorded under the 1.7 counting rule | Capability-specific LOC < 40% of Phase 1's; platform layers used unchanged listed | 1 |

---

### Phase 6 — Memory, personalisation, tenant isolation
**Week 11** · ~10 hrs · ~$4

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **6.1** | Session state — ephemeral, TTL'd | Expires on schedule; asserted in a test, not assumed | 1.5 |
| **6.2** | Customer profile — durable, tenant-partitioned, Postgres row-level security | RLS blocks a cross-tenant read **at the database**, proven over a raw connection that bypasses the app | 2.5 |
| **6.3** | Tenant scope threaded through semantic cache keys, traces and logs | A test asserts the cache key contains the tenant scope — the notorious leak vector, closed *before* 6.4 runs | 1.5 |
| **6.4** | **Canary isolation suite**, CI-blocking (§5.5): 200 planted canaries, 10,000 cross-tenant requests | **0 leaks** across outputs, traces, cache entries and logs. Any hit fails the build | 2 |
| **6.5** | Preference learning with decay; global-pattern abstraction gate | k ≥ 50 enforced and entity-scrubbing verified; `nDCG@10` measurably better for returning customers vs. cold start | 2 |
| **6.6** | Right-to-erasure endpoint | A plant-then-erase test proves removal from Postgres, Qdrant, cache **and** traces | 1.5 |

---

### Phase 7 — Capability #3: Shopping Copilot (the reuse proof)
**Week 12** · ~10 hrs · ~$8

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **7.1** | Commit the constraint: no new platform code unless genuinely unavoidable; empty exception log created | Rule and log committed **before the first line of copilot code** | 0.5 |
| **7.2** | Conversational discovery loop over the catalog: multi-turn, tool-using, on the existing runtime | 0 new orchestration primitives; every exception logged with its justification | 3 |
| **7.3** | Memory + guardrail wiring | Passes the existing guard pipeline unchanged; 0 new guards written | 2 |
| **7.4** | Run the full existing eval matrix | Passes with **no new metric infrastructure written** | 2 |
| **7.5** | **Reuse metric #3** + `docs/findings.md#reuse` writeup | Capability-specific LOC **< 15% of Phase 1's** — the headline number. If missed, the design post-mortem is published instead | 2.5 |

---

### Phase 8 — Cost/performance, framework comparison, scale
**Week 13** · ~10 hrs · ~$8

| # | Builds | Exit (numeric) | h |
|---|---|---|---|
| **8.1** | Model router with a cheap classifier; the quality-vs-cost frontier | ≥ 40% cost reduction at ≤ 3% quality loss, shown **as a curve, not a point**, so a product owner can choose the operating point | 2 |
| **8.2** | Semantic cache with tenant-scoped keys | Hit rate *and* false-hit rate both measured; false-hit rate < 1% | 2 |
| **8.3** | Batching for offline paths | Throughput and cost delta measured on the 20k product-understanding batch | 1 |
| **8.4** | **Semantic Kernel reimplementation of the stylist agent** (§5.3) | Comparison table published **whatever it concludes**: LOC, latency, token overhead, trace fidelity, debuggability, time-to-first-working | 2.5 |
| **8.5** | Load test + k8s manifest validation | Throughput and p95 under concurrency measured; manifests validate. Not deployed — and stated as such | 1.5 |
| **8.6** | `docs/`: `azure-migration.md`, `scale.md`, `governance.md`, `findings.md` | `scale.md` is arithmetic from measured throughput with stated assumptions — not adjectives | 1 |

---

## 10. Budget

| Item | Estimate |
|---|---|
| OpenRouter — judge + frontier baselines, all phases | $55 |
| Everything else (Ollama, Qdrant, Postgres, MLflow, Langfuse, embeddings, reranker) | **$0** |
| **Total** | **~$55** (hard ceiling $80, enforced in the gateway) |

---

## 11. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **Synthetic catalog too easy → every metric looks great and means nothing** | **Highest** | Adversarial generation (§5.1) is an explicit design goal; a retriever scoring > 0.95 on v1 is evidence the catalog is broken, not that retrieval is solved |
| Reuse metric gamed by writing bloated Phase 1 code | High | Phase 1 LOC is recorded before Phase 7 is designed; the rule is committed in advance |
| Closed-loop self-validation | High | §6.3 in full — objective-first gates, cross-family judge, sealed set, published κ |
| Local models too weak to show real differences | Medium | Metrics are relative (A vs B); weak models *widen* measurable gaps. Frontier baselines via OpenRouter for absolute anchoring |
| "Azure-shaped" is a claim I can't back | Medium | Azure implementations written for gateway + tracking; untested-against-real-Azure status stated explicitly rather than glossed |
| Scope creep into "build a nice demo" | High | Every phase gated on a number |
| Metrics subtly wrong | Medium | Every metric requires a hand-computed unit test |

---

## 12. Mapping to the job description

| JD requirement | Where it lives |
|---|---|
| LLM-powered systems: RAG, fine-tuning, tool use, multi-agent | Phases 2, 5; fine-tuning trade-off analysis in `findings.md` |
| Agentic workflows for automation, reasoning, conversation | Phase 5 runtime + Phases 5/7 capabilities |
| Autonomous + human-in-the-loop patterns | Phase 5 HITL checkpoints |
| Azure AI stack | §2 substitution table + `docs/azure-migration.md` |
| Reusable infra: prompt orchestration, vector/retrieval, eval + observability | Phases 0, 2, 3 — the three platform layers |
| LLM evaluation frameworks (offline + online) | Phase 3 — the core deliverable |
| AI safety guardrails: hallucination, filtering, explainability | Phase 4 |
| Partner with Trust & Security; risk controls by design | Phase 4 fail-closed + Phase 6 isolation + `governance.md` |
| Reusable capabilities (stylist reasoning, product understanding, copilots) | Phases 1, 5, 7 — **exactly the three the JD names** |
| Horizontal reuse — build once, scale many | §7 reuse metric — the headline result |
| Performance, cost, reliability; token-aware design | Phase 8 + gateway from Phase 0 |
| Embeddings, tokenisation, context management | Phase 2 grounding layer |
| State, memory, event-driven pipelines | Phases 5, 6 |
| Semantic Kernel / LangChain | Phase 8 comparison, with a justified build-vs-buy verdict |
| LLMOps: CI/CD, experiment tracking, observability | Phase 0 (MLflow, Langfuse, OTel) + CI gates throughout |
| Caching, batching, model routing | Phase 8 |
| Scalable compute (AKS or similar) | Phase 8 load test + validated manifests, honestly scoped as not-deployed |

---

## 13. Decision log

Recorded as made, with reasoning, in `docs/decision-log.md`. Seed entries:

1. **Azure-shaped, locally-run.** Interface equivalence over spend. Azure OpenAI is OpenAI-compatible; migration is one env var.
2. **Custom agent runtime, then benchmarked against Semantic Kernel.** The orchestration layer is the deliverable; a framework would hide it. But the comparison gets published either way.
3. **Qdrant, not pgvector.** Retail retrieval is filter-heavy; payload-filter ergonomics decide this.
4. **Hybrid retrieval from day one.** Retail queries contain exact tokens dense retrieval smears (§8).
5. **pytest as the eval harness.** Parametrization + CI gating free; a custom harness is the classic wasted month.
6. **Ollama for bulk, OpenRouter for judging.** Unlimited free eval runs is what makes evaluation-driven development possible at all.
7. **Adversarial synthetic catalog.** Ground truth for free is only valuable if the ground truth is hard.
8. **Guardrails fail closed.** A blocked response is recoverable; a wrong product recommendation at retail scale is not.
