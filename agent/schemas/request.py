"""
Request schema — the structured object the backend sends to the agent.

This is the public contract between the Node.js backend and the Python
agent.  The backend constructs this object and passes it to
``invoke_agent(request)``.

The backend maps:
  - conversation_id → session_id
  - messages history → conversation_history
  - extracted document text → document_text (in context dict)
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from agent.schemas.message import ChatMessage
from agent.schemas.state import Language


class AgentRequest(BaseModel):
    """Incoming request to the Prohor legal agent."""

    query: str = Field(description="The user's question or message")
    language: Language = Field(
        default=Language.ENGLISH,
        description="Preferred response language",
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Prior messages for context (oldest first)",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Authenticated user ID from Supabase, if available",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation ID from the backend (maps to conversations.id)",
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional free-form context (e.g. user location, document text)",
    )

    model_config = {"use_enum_values": True}

    @property
    def document_text(self) -> Optional[str]:
        """Extract document text from the context dict if present."""
        if self.context:
            return self.context.get("document_text")
        return None
