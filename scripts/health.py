"""Phase 0.1 exit criterion: all 5 services healthy. Stdlib only - runs before any venv exists.

Usage: python scripts/health.py [--wait SECONDS]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request


def http(url: str, *, expect: int = 200):
    def check() -> str | None:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status != expect:
                    return f"HTTP {r.status}"
                return None
        except urllib.error.HTTPError as e:
            return f"HTTP {e.code}"
        except Exception as e:  # connection refused, DNS, timeout
            return type(e).__name__
    return check


def pg_ready() -> str | None:
    p = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "atelier", "-d", "atelier"],
        capture_output=True, text=True,
    )
    if p.returncode == 0:
        return None
    out = (p.stdout + p.stderr).strip()
    return out.splitlines()[-1] if out else "not ready"


# (name, where it runs, check)
SERVICES = [
    ("ollama",   "host :11434",   http("http://localhost:11434/api/tags")),
    ("qdrant",   "docker :6333",  http("http://localhost:6333/healthz")),
    ("postgres", "docker :5432",  pg_ready),
    ("langfuse", "docker :3000",  http("http://localhost:3000/api/public/health")),
    ("mlflow",   "docker :5000",  http("http://localhost:5000/health")),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=0, help="seconds to keep retrying unhealthy services")
    args = ap.parse_args()

    deadline = time.monotonic() + args.wait
    pending = list(SERVICES)
    results: dict[str, str | None] = {}

    while True:
        still = []
        for name, where, check in pending:
            err = check()
            results[name] = err
            if err is None:
                print(f"  ok    {name:9s} {where}")
            else:
                still.append((name, where, check))
        pending = still
        if not pending or time.monotonic() >= deadline:
            break
        print(f"  ...   waiting on {', '.join(n for n, _, _ in pending)}")
        time.sleep(5)

    for name, where, _ in pending:
        print(f"  FAIL  {name:9s} {where}: {results[name]}")

    healthy = len(SERVICES) - len(pending)
    print(f"\n{healthy}/{len(SERVICES)} services healthy")
    return 1 if pending else 0


if __name__ == "__main__":
    sys.exit(main())
