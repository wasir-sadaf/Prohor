"""
LLM factory — selects the correct backend based on configuration.

The factory creates the client on first call and caches it, so
repeated calls are cheap.
"""

from __future__ import annotations

from agent.config.settings import LLMProvider, get_settings
from agent.llm.base import LLMClient


_client_cache: LLMClient | None = None


def get_llm() -> LLMClient:
    """Return the configured LLM client (cached after first creation)."""

    global _client_cache
    if _client_cache is not None:
        return _client_cache

    settings = get_settings()

    if settings.llm_provider == LLMProvider.OPENAI:
        if not settings.openai_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Set the environment variable or switch to LLM_PROVIDER=mock."
            )
        from agent.llm.openai_client import OpenAIClient

        _client_cache = OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout,
        )

    elif settings.llm_provider == LLMProvider.GOOGLE:
        if not settings.google_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=google but GOOGLE_API_KEY is not set. "
                "Set the environment variable or switch to LLM_PROVIDER=mock."
            )
        from agent.llm.google_client import GoogleLLMClient

        _client_cache = GoogleLLMClient(
            api_key=settings.google_api_key,
            model=settings.google_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout,
        )

    elif settings.llm_provider == LLMProvider.MOCK:
        from agent.llm.mock import MockLLMClient

        _client_cache = MockLLMClient()

    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")

    return _client_cache


def reset_llm_cache() -> None:
    """Clear the cached client. Useful in tests."""
    global _client_cache
    _client_cache = None
