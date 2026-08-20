"""Phase 0.1 exit criterion: all 5 services healthy. Stdlib only - runs before any venv exists.

Usage: python scripts/health.py [--wait SECONDS]
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable

ROOT = pathlib.Path(__file__).resolve().parents[1]


def http(url: str) -> Callable[[], str | None]:
    def check() -> str | None:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status != 200:
                    return f"HTTP {r.status}"
                return None
        except urllib.error.HTTPError as e:
            return f"HTTP {e.code}"
        except Exception as e:  # connection refused, DNS, timeout
            return type(e).__name__
    return check


def pg_ready() -> str | None:
    p = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres",
         "pg_isready", "-U", "atelier", "-d", "atelier"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if p.returncode == 0:
        return None
    out = (p.stdout + p.stderr).strip()
    return out.splitlines()[-1] if out else "not ready"


# (name, where it runs, check)
SERVICES = [
    ("ollama",   "host :11434",   http("http://localhost:11434/api/tags")),
    ("qdrant",   "docker :6333",  http("http://localhost:6333/healthz")),
    ("postgres", "docker :5433",  pg_ready),
    ("langfuse", "docker :3000",  http("http://localhost:3000/api/public/health")),
    ("mlflow",   "docker :5000",  http("http://localhost:5000/health")),
]


def run(services: list, wait: int = 0, pause: int = 5) -> int:
    deadline = time.monotonic() + wait
    pending = list(services)
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
        time.sleep(pause)

    for name, where, _ in pending:
        print(f"  FAIL  {name:9s} {where}: {results[name]}")

    healthy = len(services) - len(pending)
    print(f"\n{healthy}/{len(services)} services healthy")
    return 1 if pending else 0


def self_test() -> int:
    """The gate must be able to FAIL. A health check that always returns 0 is decoration."""
    ok = lambda: None                      # noqa: E731 - terse on purpose, this is a stub
    bad = lambda: "connection refused"     # noqa: E731

    assert run([("a", "x", ok), ("b", "x", ok)]) == 0, "all-healthy must exit 0"
    assert run([("a", "x", ok), ("b", "x", bad)]) == 1, "one failure must exit 1"
    assert run([("a", "x", bad)]) == 1, "total failure must exit 1"

    # a service that is not ready at first, then becomes ready, must pass within the deadline
    state = {"n": 0}

    def flaky() -> str | None:
        state["n"] += 1
        return None if state["n"] > 2 else "still starting"

    assert run([("late", "x", flaky)], wait=30, pause=0) == 0, "must retry until ready"
    assert state["n"] == 3, f"expected 3 attempts, got {state['n']}"

    # and it must give up rather than hang forever
    assert run([("never", "x", bad)], wait=0, pause=0) == 1, "must stop at the deadline"

    print("self-test ok: gate passes when healthy, fails when not, retries, and gives up")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wait", type=int, default=0,
                    help="seconds to keep retrying unhealthy services")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the gate can fail, no Docker needed")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    return run(SERVICES, wait=args.wait)


if __name__ == "__main__":
    sys.exit(main())
