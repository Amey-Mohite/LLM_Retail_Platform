"""Phase 0.2 exit criterion, as an executable gate.

Brief: "100 calls through the interface, 0 unhandled exceptions; every response carries
tokens_in/out, model, latency_ms."

Usage:
  python scripts/gate_02.py [--calls 100]
  python scripts/gate_02.py --self-test    # prove the gate can fail, no model needed
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
import time

from atelier.gateway import Completion, GatewayError, OllamaProvider

SUBJECTS = ["a linen shirt", "a wool coat", "a denim jacket", "a silk scarf", "a cotton dress",
            "a leather belt", "a knit jumper", "a pleated skirt", "a canvas tote", "a suede boot"]
ASKS = ["Name its main material in one word.", "Give one occasion to wear it.",
        "Name one colour it suits.", "Say which season it belongs to.",
        "Give one word for its fit."]


def prompts(n: int, seed: int = 0) -> list[str]:
    """Varied but reproducible, so a rerun is comparable and nothing is served from a cache."""
    # in : prompts(3, seed=0)
    # out: ['Consider a suede boot. Name one colour it suits.', ...]
    rng = random.Random(seed)
    return [f"Consider {rng.choice(SUBJECTS)}. {rng.choice(ASKS)}" for _ in range(n)]


def missing_fields(c: Completion) -> list[str]:
    """The exit criterion, checked literally rather than assumed."""
    # in : Completion(text="Red", model="m", provider="ollama",
    #                 tokens_in=8, tokens_out=1, latency_ms=12.0)
    # out: []
    bad = []
    if c.tokens_in <= 0:
        bad.append("tokens_in")
    if c.tokens_out <= 0:
        bad.append("tokens_out")
    if not c.model:
        bad.append("model")
    if c.latency_ms <= 0:
        bad.append("latency_ms")
    return bad


def run(provider, calls: int) -> int:
    latencies: list[float] = []
    tokens_in = tokens_out = 0
    failures: list[str] = []

    started = time.perf_counter()
    for i, prompt in enumerate(prompts(calls), 1):
        try:
            c = provider.complete(prompt, max_tokens=16)
        except GatewayError as e:          # expected failure mode, still a gate failure
            failures.append(f"call {i}: GatewayError {e}")
            continue
        except Exception as e:             # unhandled - the thing the criterion forbids
            failures.append(f"call {i}: UNHANDLED {type(e).__name__}: {e}")
            continue

        gaps = missing_fields(c)
        if gaps:
            failures.append(f"call {i}: response missing {', '.join(gaps)}")
            continue

        latencies.append(c.latency_ms)
        tokens_in += c.tokens_in
        tokens_out += c.tokens_out
        if i % 10 == 0:
            print(f"  {i:>4}/{calls}  last {c.latency_ms:7.0f} ms  {c.text[:40]!r}", flush=True)

    wall = time.perf_counter() - started
    ok = len(latencies)
    print(f"\n  calls           : {ok}/{calls} complete and fully accounted")
    print(f"  failures        : {len(failures)}")
    if latencies:
        ordered = sorted(latencies)
        print(f"  latency p50/p95 : {statistics.median(ordered):.0f} / "
              f"{ordered[int(len(ordered) * 0.95) - 1]:.0f} ms")
        print(f"  tokens in/out   : {tokens_in} / {tokens_out}")
        print(f"  throughput      : {ok / wall:.2f} calls/s over {wall:.0f}s")
    for f in failures[:10]:
        print(f"  FAIL {f}")

    passed = ok == calls and not failures
    print(f"\nPhase 0.2 gate: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


class _StubProvider:
    """Returns a deliberately unaccounted response, to prove the gate rejects it."""

    name = "stub"

    def __init__(self, tokens_out: int) -> None:
        self._tokens_out = tokens_out

    def complete(self, prompt: str, **kw) -> Completion:
        return Completion(text="x", model="stub", provider="stub",
                          tokens_in=1, tokens_out=self._tokens_out, latency_ms=1.0)


def self_test() -> int:
    """A gate that cannot fail is decoration. Prove both directions without a model."""
    assert run(_StubProvider(tokens_out=1), calls=3) == 0, "fully accounted responses must pass"
    assert run(_StubProvider(tokens_out=0), calls=3) == 1, "unaccounted output tokens must fail"

    try:
        Completion(text="x", model="m", provider="p", tokens_in=-1, tokens_out=1, latency_ms=1.0)
    except GatewayError:
        pass
    else:
        raise AssertionError("Completion must reject a negative token count")

    try:
        Completion(text="x", model="", provider="p", tokens_in=1, tokens_out=1, latency_ms=1.0)
    except GatewayError:
        pass
    else:
        raise AssertionError("Completion must reject a missing model name")

    print("\nself-test ok: gate passes accounted responses, rejects unaccounted ones")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", type=int, default=100)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return run(OllamaProvider(), args.calls)


if __name__ == "__main__":
    sys.exit(main())
