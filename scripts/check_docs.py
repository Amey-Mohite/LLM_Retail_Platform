"""Mechanical enforcement of docs/DOCS_STANDARDS.md formatting rules.

The standard lists parse-breakers that "break rendering repeatedly". Vigilance does not
scale, so they are checked instead. Run after editing any markdown.

Usage: python scripts/check_docs.py [path ...]     (default: every .md in the repo)
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__"}

Finding = tuple[pathlib.Path, int, str]


def check_fences(path: pathlib.Path, lines: list[str]) -> list[Finding]:
    # in : ["```python", "x = 1", "```"]  -> []
    # out: ["```python", "x = 1"]         -> [(path, 1, "unclosed code fence ...")]
    opens = [i for i, ln in enumerate(lines, 1) if ln.lstrip().startswith("```")]
    if len(opens) % 2:
        return [(path, opens[-1], f"unclosed code fence (odd count: {len(opens)})")]
    return []


def mermaid_blocks(lines: list[str]):
    """Yield (start_lineno, block_lines) for each ```mermaid ... ``` block."""
    inside, start, buf = False, 0, []
    for i, ln in enumerate(lines, 1):
        stripped = ln.strip()
        if not inside and stripped.startswith("```mermaid"):
            inside, start, buf = True, i, []
        elif inside and stripped.startswith("```"):
            yield start, buf
            inside = False
        elif inside:
            buf.append((i, ln))


def check_mermaid(path: pathlib.Path, lines: list[str]) -> list[Finding]:
    out: list[Finding] = []
    for _start, block in mermaid_blocks(lines):
        for lineno, raw in block:
            ln = raw.strip()
            if ln.startswith("%%") or not ln:
                continue
            if ";" in ln:
                out.append((path, lineno, "mermaid: ';' is a statement separator - remove it"))
            if re.match(r"(participant|actor)\b", ln) and ("(" in ln or ")" in ln):
                out.append((path, lineno, "mermaid: parentheses in participant alias - use '·'"))
            for tag in re.findall(r"<[^>]*>", ln):
                if tag != "<br/>":
                    out.append((path, lineno, f"mermaid: '{tag}' parses as HTML - only <br/> allowed"))
            for label in re.findall(r"\|([^|]*)\|", ln):
                if re.search(r"[()\[\]{}:,]", label) and not label.strip().startswith('"'):
                    out.append((path, lineno, f'mermaid: quote the edge label - |"{label}"|'))
            if re.search(r":\s*\[\{", ln):
                out.append((path, lineno, "mermaid: message starts with '[{' - put JSON in a Note"))
    return out


BAD = """```mermaid
sequenceDiagram
  participant A as AI (FastAPI)
  A->>B: hello; world
  A->>B: [{"sku": 1}]
  B-->>A: see <span>x</span>
  B->>C: fine <br/> here
  A-->>B: ok
```

```python
unclosed
"""


def self_test() -> int:
    """Every rule in DOCS_STANDARDS.md section 4 fires at least once, and clean text stays clean."""
    lines = BAD.splitlines()
    path = pathlib.Path("<self-test>")
    msgs = [m for _, _, m in check_fences(path, lines) + check_mermaid(path, lines)]
    for expected in ["statement separator", "participant alias", "parses as HTML",
                     "put JSON in a Note", "unclosed code fence"]:
        assert any(expected in m for m in msgs), f"rule did not fire: {expected} | got: {msgs}"
    assert not any("'<br/>'" in m for m in msgs), "<br/> is legal and must not be flagged"

    clean = ["```mermaid", "sequenceDiagram", "  participant A as AI · FastAPI",
             "  A->>B: hello world", "```"]
    assert not check_fences(path, clean) + check_mermaid(path, clean), "clean diagram flagged"
    print("self-test ok: 5 rules fire, clean input passes")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--self-test"]:
        return self_test()
    targets = [pathlib.Path(a) for a in argv] or [
        p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)
    ]
    findings: list[Finding] = []
    for path in sorted(targets):
        lines = path.read_text(encoding="utf-8").splitlines()
        findings += check_fences(path, lines) + check_mermaid(path, lines)

    for path, lineno, msg in findings:
        print(f"{path.relative_to(ROOT) if path.is_absolute() else path}:{lineno}: {msg}")
    print(f"\n{len(targets)} file(s) checked, {len(findings)} problem(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
