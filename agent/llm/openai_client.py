"""
OpenAI LLM backend.

Uses the ``openai`` Python SDK. The dependency is imported lazily so
that the agent can run without the package when using the mock backend.
"""

from __future__ import annotations

from agent.schemas.message import ChatMessage


class OpenAIClient:
    """Thin wrapper around the OpenAI Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: int = 30,
    ) -> None:
        # Lazy import — only required when OpenAI is the active provider
        from openai import OpenAI  # type: ignore

        self._client = OpenAI(api_key=api_key, timeout=timeout)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages: list[ChatMessage]) -> str:
        payload = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        response = self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content or ""

    @property
    def model_name(self) -> str:
        return self._model
