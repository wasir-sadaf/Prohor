"""
Chat message schema used across the agent pipeline.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(description="One of: 'system', 'user', 'assistant'")
    content: str = Field(description="Text content of the message")
