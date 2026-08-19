# Learning-Docs & Writing Standards

A reusable standard for building projects that double as teaching artifacts. Copy this file
(or the kickoff prompt at the bottom) into any new repo so the learning docs get created
**alongside the code**, in a consistent style.

---

## 0. Philosophy

Every project is also a **teaching artifact**. Docs are written *as the code is built*, not
bolted on after. A reader (including future-you, or an interviewer) should understand the
*what*, the *why*, and the *trade-offs* — from scratch, in plain language, with the honesty to
say what's real vs. demo.

Three non-negotiables:
1. **From scratch** — assume no prior knowledge of the specific pattern; explain the concept
   before the code.
2. **Honesty** — label what's production-grade vs. demonstrative (see tiering).
3. **Interview-depth** — every concept doc ends with questions you should be able to answer.

---

## 1. The file set (create these per project)

| File | Purpose |
|---|---|
| **`README.md`** | Front door: what it is, status table, quick-start run steps, API table, repo layout. |
| **`DESIGN.md`** | The design document + a **phase log** updated every phase. Requirements, estimates, architecture, trade-offs, honesty tiering. |
| **`docs/phaseN.md`** | One per phase — a **from-scratch walkthrough of every file built that phase**, with a function-level flow and a glossary. |
| **`docs/concepts/*.md`** | The **concepts handbook** — one file per concept, explained generally, then applied to this project. |
| **`docs/concepts/README.md`** | Index of the handbook (reading order + concept→phase map). |
| **`docs/index.html`** | Self-contained portfolio landing page (GitHub Pages). |

---

## 2. `docs/phaseN.md` structure (per-phase walkthrough)

- **Header callout** — one paragraph: what this phase adds, in plain terms.
- **Honesty up front** — which parts are Tier 1/2/3.
- **The end-to-end flow** — a **mermaid sequence diagram**.
- **Function-by-function flow with *dummy inputs & outputs*** — name the actual
  `file::function`, show a concrete value at each hop.
- **File-by-file** — for each file built, what it does and why.
- **⚠️ Scaffolded — be ready to explain** — a list of things included but not fully mastered
  (be honest).
- **Mini-glossary** — new terms this phase, one line each.
- **(Optional) Q&A section** — capture the real questions asked while learning, with answers.

---

## 3. `docs/concepts/*.md` structure (the handbook)

Each concept file, in this order:

1. **One-line "what this is."**
2. **🧊 Layman box** — an everyday analogy, no jargon:
   > 🧊 **Layman box.** [Analogy in plain English — a restaurant, a freezer aisle, a filing cabinet…]
3. **The problem it solves** — why this exists at all.
4. **How it works** — with a **mermaid diagram** and a **concrete code snippet**.
5. **Variations & trade-offs** — when to use it, when not.
6. **Interview questions you should be able to answer** — bulleted questions + short answers.
7. **In `<Project>`** — a short closing section mapping the general concept to how *this* project
   uses it (with `file` references).

The bulk is **portable knowledge**; the project-specific part is a short note at the end.

---

## 4. Cross-cutting writing rules

### Honesty tiering (use everywhere)
- **Tier 1 — load-bearing:** real, runs, does the job in production terms.
- **Tier 2 — demonstrative:** correct and shown, but simplified / at small scale.
- **Tier 3 — showcase:** validated and runnable, but not operated for real (e.g., deployed only
  locally).

Label features/phases with their tier. Never let a Tier-3 thing masquerade as Tier 1.

### "Code, explained simply" pattern
Show a snippet, then a **bolded plain-English translation** of what it does — line by line for
anything non-obvious:
> ```python
> resp = provider.generate(system, history, tools)
> ```
> **"Ask the model for its next move — it either answers, or asks to run a tool."**

### I/O example comments on functions
Non-trivial functions carry an input→output example in a comment:
```python
def execute(name, args, principal) -> str:
    # in : ("get_balances", {}, principal)
    # out: '[{"code":"CASH","balance":500}]'
```

### Layman boxes (🧊)
Any dense concept gets a 🧊 box with a real-world analogy *before* the technical explanation.

### "Interview questions you should be able to answer"
Every concept doc ends with these. They force the doc to actually teach, and double as prep.

### Diagrams — use mermaid, and avoid these parse pitfalls
(These break rendering repeatedly — bake them in from the start.)
- **No `;`** inside diagram labels/messages (it's a statement separator).
- **No parentheses in participant aliases** — use `·` instead: `AI · FastAPI`.
- **No `<...>`** in labels — mermaid reads it as an HTML tag. Only `<br/>` is allowed.
- **Quote edge labels** with special chars: `-->|"on main"|`.
- **Don't start a message with `[{`** — put JSON in a `Note`, not inline.
- After writing any diagram, **scan it** for `;` and stray `<`.

### Always verify formatting
- After editing a markdown file, **check code fences are balanced** (even count of ` ``` `).
- Validate config/code you write (`helm lint`, `terraform validate`, YAML parse, `py_compile`) —
  don't ship unrun snippets as if tested; **state what was and wasn't actually run.**

---

## 5. Workflow

- **Docs are written *with* the code each phase**, not at the end.
- **Update `DESIGN.md`'s phase log every phase** (delivered / skills / trade-offs / scaffolded /
  not-run-live).
- **Deliver a whole phase at once** — code + all its docs + explanation — rather than
  checkpointing piecemeal.
- **Capture real questions** asked while learning into the phase doc's Q&A, so confusion becomes
  documentation.
- **DO NOT commit or push code.** The author commits and opens PRs themselves, per phase. The
  assistant writes/edits files and validates them, but never runs `git commit`, `git push`, or
  creates PRs unless explicitly asked in the moment. Branch when starting a phase only if asked.

---

## 6. Ready-to-paste kickoff prompt

> **Documentation standard for this project.** As we build, create learning docs *alongside* the
> code, following this standard:
> - **Per phase**, write `docs/phaseN.md`: a from-scratch walkthrough of every file built, a
>   mermaid sequence diagram, a **function-by-function flow with dummy inputs/outputs**, a
>   "⚠️ scaffolded — be ready to explain" list, and a mini-glossary.
> - Maintain a **`docs/concepts/` handbook**: one file per concept, each with a **🧊 layman
>   analogy**, the problem it solves, a **mermaid diagram + code snippet**, trade-offs, an
>   **"Interview questions you should be able to answer"** section, and a short "In this project"
>   closing note. Keep an index at `docs/concepts/README.md`.
> - Keep **`DESIGN.md`** updated with a **phase log** each phase (delivered / skills / trade-offs
>   / scaffolded / not-run-live).
> - Keep **`README.md`** current: status table, quick-start run steps, API table, repo layout.
> - Apply **honesty tiering** everywhere — Tier 1 (load-bearing) / Tier 2 (demonstrative) /
>   Tier 3 (showcase); never let a Tier-3 thing look Tier 1.
> - Use the **"code, then plain-English translation"** style; add **input→output example
>   comments** to non-trivial functions; explain everything **from scratch, in easy language.**
> - For diagrams use **mermaid**, avoiding these parse-breakers: no `;` in labels, no parens in
>   participant aliases (use `·`), no `<...>` except `<br/>`, quote edge labels, no `[{` at a
>   message start.
> - Write docs **as we go, whole phase at a time**; capture the real questions I ask into the
>   phase doc.
> - After editing any doc, **verify code fences are balanced**; validate any code/config you
>   write and state what was and wasn't actually run.
> - **Do NOT commit or push code, and do not open PRs** — I handle all git commits/PRs myself.
>   Just write and validate the files.
