"""Ollama, reached through its OpenAI-compatible endpoint.

Ollama speaks the OpenAI wire protocol, and so does Azure OpenAI. Using the `openai` client
here rather than Ollama's native `/api/chat` is what makes Phase 0.3's Azure adapter close to
empty - the difference is a base URL and a key. That is the whole "Azure-shaped, locally-run"
claim, paid for in advance.
"""
from __future__ import annotations

import os
import time

from openai import OpenAI

from atelier.gateway.provider import Completion, GatewayError

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5:7b-instruct-q4_K_M"


class OllamaProvider:
    """Local models. Free and unlimited, which is what makes nightly evaluation possible."""

    name = "ollama"

    def __init__(
        self,
        base_url: str | None = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL)
        # Ollama ignores the key entirely, but the client requires one to be present.
        self._client = OpenAI(
            base_url=self.base_url, api_key="ollama", timeout=timeout, max_retries=0
        )

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
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # perf_counter, not time(), because this is a duration - a clock adjustment
        # mid-call must not turn into a negative latency.
        started = time.perf_counter()
        try:
            r = self._client.chat.completions.create(
                model=model or self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            # Retries, timeouts and fallback chains are Phase 0.3. For now the contract is
            # simply that callers see one exception type, not the vendor's.
            raise GatewayError(f"{type(e).__name__}: {e}") from e
        latency_ms = (time.perf_counter() - started) * 1000

        if r.usage is None:
            raise GatewayError("provider returned no usage block - refusing to report zero tokens")

        return Completion(
            text=(r.choices[0].message.content or ""),
            model=r.model,
            provider=self.name,
            tokens_in=r.usage.prompt_tokens,
            tokens_out=r.usage.completion_tokens,
            latency_ms=latency_ms,
        )
