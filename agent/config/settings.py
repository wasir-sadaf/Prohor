"""
Centralized LLM and application configuration.

All sensitive values are read from environment variables. No keys
are ever hard-coded.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    MOCK = "mock"


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # ── LLM provider ────────────────────────────────────────────
    llm_provider: LLMProvider = Field(
        default=LLMProvider.MOCK,
        description="Which LLM backend to use",
    )

    # ── OpenAI ──────────────────────────────────────────────────
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4o")

    # ── Google / Gemini ──────────────────────────────────────────
    google_api_key: Optional[str] = Field(default=None)
    google_model: str = Field(default="gemini-1.5-flash")

    # ── Generation parameters ────────────────────────────────────
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)
    timeout: int = Field(default=30, gt=0)

    model_config = {"extra": "ignore"}


def _bool_from_env(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes")


def get_settings() -> Settings:
    """Build a Settings instance from the current environment."""

    provider_raw = os.getenv("LLM_PROVIDER", "mock").lower()

    return Settings(
        llm_provider=LLMProvider(provider_raw),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        google_model=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
        timeout=int(os.getenv("LLM_TIMEOUT", "30")),
    )
