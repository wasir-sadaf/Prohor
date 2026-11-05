"""
LLM abstraction layer.

Provides a single ``LLMClient`` protocol so that OpenAI, Google, and
mock back-ends can be swapped without changing agent code.
"""

from __future__ import annotations

from typing import Protocol

from agent.schemas.message import ChatMessage


class LLMClient(Protocol):
    """Minimal interface that every LLM backend must satisfy."""

    def chat(self, messages: list[ChatMessage]) -> str:
        """Return the assistant's text response for the given chat history."""
        ...

    @property
    def model_name(self) -> str:
        """Name of the underlying model, for logging / citation."""
        ...
