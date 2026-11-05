"""
Mock LLM backend for development and testing without API credentials.

Produces deterministic, context-aware responses so the full agent
pipeline can be exercised end-to-end.
"""

from __future__ import annotations

from agent.schemas.message import ChatMessage


class MockLLMClient:
    """Deterministic mock that echoes intent and returns a canned reply."""

    def __init__(self, model_name: str = "mock-llm-v1") -> None:
        self._model_name = model_name

    # ── public API ──────────────────────────────────────────────

    def chat(self, messages: list[ChatMessage]) -> str:
        system_prompt = ""
        user_query = ""

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                user_query = msg.content

        # Detect simple patterns to give slightly varied mock responses
        query_lower = user_query.lower()

        if any(kw in query_lower for kw in ["gd", "general diary", "জিডি"]):
            return (
                "To file a General Diary (GD) in Bangladesh:\n\n"
                "1. Visit your nearest police station.\n"
                "2. Write a GD application describing the incident.\n"
                "3. Submit it to the Officer-in-Charge (OC).\n"
                "4. Keep the GD number receipt for reference.\n\n"
                "Note: This is a mock response for development purposes."
            )

        if any(kw in query_lower for kw in ["rights", "অধিকার"]):
            return (
                "As a Bangladeshi citizen, you have fundamental rights "
                "guaranteed by the Constitution, including:\n"
                "- Right to life and personal liberty (Article 32)\n"
                "- Right to equality before law (Article 27)\n"
                "- Right to protection of law (Article 31)\n\n"
                "Note: This is a mock response for development purposes."
            )

        return (
            f"I understand your question about: \"{user_query}\". "
            "This is a mock response from the Prohor agent. "
            "Configure a real LLM provider to get actual legal guidance."
        )

    @property
    def model_name(self) -> str:
        return self._model_name
