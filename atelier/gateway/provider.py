"""The seam every model call goes through.

Nothing above this layer may talk to a model SDK directly. That rule is what makes token
accounting a guarantee rather than a habit: the only way to get a response is to receive a
`Completion`, and a `Completion` cannot exist without its accounting fields.

Phase 0.6 enforces the rule mechanically with an import-linter contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class GatewayError(RuntimeError):
    """A model call failed in a way the caller is expected to handle."""


@dataclass(frozen=True)
class Completion:
    """One model response, and what it cost to get it.

    Frozen because a response is a record of something that already happened. Nothing
    downstream should be able to edit the token count it is later billed against.
    """

    text: str
    model: str          # what actually served it, which is not always what was asked for
    provider: str
    tokens_in: int
    tokens_out: int
    latency_ms: float

    def __post_init__(self) -> None:
        # Accounting is not optional. A provider that cannot report usage must fail
        # loudly here rather than quietly report zero and corrupt every later total.
        # in : Completion(text="hi", model="m", provider="p", tokens_in=-1, ...)
        # out: GatewayError
        if self.tokens_in < 0 or self.tokens_out < 0:
            raise GatewayError(f"negative token count: in={self.tokens_in} out={self.tokens_out}")
        if not self.model or not self.provider:
            raise GatewayError("completion must name its model and provider")

    @property
    def tokens_total(self) -> int:
        return self.tokens_in + self.tokens_out


class Provider(Protocol):
    """Anything that turns a prompt into text and reports what that cost.

    Deliberately small. The interface is shaped by what this application needs, not by the
    union of what every vendor offers - see docs/concepts/interface-substitution.md.
    """

    name: str

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> Completion:
        # in : complete("name one primary colour", max_tokens=5)
        # out: Completion(text="Red", model="qwen2.5:7b-instruct-q4_K_M", provider="ollama",
        #                 tokens_in=38, tokens_out=2, latency_ms=412.7)
        ...
