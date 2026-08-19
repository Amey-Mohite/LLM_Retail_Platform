# Working rules for this repo

## 1. Docs standard — binding

**[docs/DOCS_STANDARDS.md](docs/DOCS_STANDARDS.md) governs every doc in this repo. Read it before
writing or editing any markdown.** It is not a suggestion and not a style preference.

The rules below are the ones that get silently skipped, restated here so they cannot be. Everything
else lives in that file.

### Never commit, never push, never open PRs
The author does all git operations, per phase, themselves. Write files, validate them, stop there.
No `git commit`, no `git push`, no `gh pr create` — **unless asked in the moment, that session.**
Branching at the start of a phase only if asked.

### A phase is not delivered until its docs are delivered
Code and docs ship together, whole phase at a time. Per phase that means:

| Artifact | What it must contain |
|---|---|
| `docs/phaseN.md` | Header callout · honesty tier of each part · mermaid **sequence** diagram · function-by-function flow naming real `file::function` with **dummy input→output at each hop** · file-by-file rationale · **⚠️ Scaffolded — be ready to explain** list · mini-glossary · Q&A of real questions asked |
| `docs/concepts/*.md` | One file per *new* concept, in the §3 order: one-liner → 🧊 layman box → problem it solves → how it works (mermaid + snippet) → trade-offs → **interview questions with answers** → "In this project" note |
| `docs/concepts/README.md` | Kept current: reading order + concept→phase map |
| `DESIGN.md` | Phase log appended: delivered / skills / trade-offs / scaffolded / not-run-live |
| `README.md` | Status table, quick-start, repo layout kept current |

### Honesty tiering, everywhere
**Tier 1** load-bearing (real, production terms) · **Tier 2** demonstrative (correct, simplified or
small-scale) · **Tier 3** showcase (runnable and validated, not operated for real). Label features
and phases. A Tier-3 thing must never read as Tier 1.

### Explain from scratch
Assume no prior knowledge of the pattern. Snippet, then a **bolded plain-English translation**.
Non-trivial functions carry an `# in :` / `# out:` example comment. Dense concepts get a 🧊 box
*before* the technical explanation.

### Mermaid parse-breakers — check every diagram after writing it
No `;` in labels · no parentheses in participant aliases, use `·` · no `<...>` except `<br/>` ·
quote edge labels containing special chars · never start a message with `[{`, put JSON in a `Note`.

### Verify, and say what was verified
Balanced code fences after every markdown edit — run `python scripts/check_docs.py`. Validate code and
config you write — YAML parse, `py_compile`, `docker compose config`, linters. **State explicitly
what was actually run and what was not.** Never present an unrun snippet as tested.

## 2. Project

Design, phases and numeric exit criteria: **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)**.
Decisions as made: **[docs/decision-log.md](docs/decision-log.md)**.
No phase is done because the code runs — it is done when it hits its number.
