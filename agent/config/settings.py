"""
Centralized LLM and application configuration.

All sensitive values are read from environment variables. No keys
are ever hard-coded.

Loads from agent/.env file if present (via python-dotenv), then
falls back to OS environment variables.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# ── Load .env file if present ────────────────────────────────────
# python-dotenv is already a dependency through langchain-core.
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GOOGLE = "google"
    MOCK = "mock"


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # ── LLM provider ────────────────────────────────────────────
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="Which LLM backend to use (openai, google, mock)",
    )

    # ── OpenAI ──────────────────────────────────────────────────
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-6-luna")

    # ── Google / Gemini ──────────────────────────────────────────
    google_api_key: Optional[str] = Field(default=None)
    google_model: str = Field(default="gemini-1.5-flash")

    # ── Generation parameters ────────────────────────────────────
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, gt=0)
    timeout: int = Field(default=30, gt=0)

    model_config = {"extra": "ignore"}


def get_settings() -> Settings:
    """Build a Settings instance from the current environment."""

    provider_raw = os.getenv("LLM_PROVIDER", "openai").lower()

    return Settings(
        llm_provider=LLMProvider(provider_raw),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        google_model=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
        timeout=int(os.getenv("LLM_TIMEOUT", "30")),
    )
