"""
Response schema — the structured object the agent returns to the backend.

The backend receives this from ``invoke_agent(request)`` and can
directly serialize it to JSON for the frontend.

Each evidence item includes source_id and chunk_id so the backend can
save citation relationships through the message_sources table.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from agent.schemas.evidence import LegalEvidence
from agent.schemas.state import Intent, SafetyStatus


class CitationEntry(BaseModel):
    """A single citation with backend linkage IDs."""

    citation_text: str = Field(description="Human-readable citation string")
    source_id: Optional[str] = Field(default=None, description="legal_sources UUID")
    chunk_id: Optional[str] = Field(default=None, description="legal_chunks UUID")
    law_or_regulation: Optional[str] = Field(default=None)
    section_or_provision: Optional[str] = Field(default=None)
    is_verified: bool = Field(default=False, description="Whether source is verified in DB")


class AgentResponse(BaseModel):
    """Outgoing response from the Prohor legal agent."""

    response: str = Field(description="The agent's text response to the user")
    intent: Optional[str] = Field(
        default=None,
        description="Detected intent category",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Human-readable citation strings",
    )
    citation_entries: list[CitationEntry] = Field(
        default_factory=list,
        description="Structured citations with source/chunk IDs for backend linkage",
    )
    evidence: list[LegalEvidence] = Field(
        default_factory=list,
        description="Legal evidence backing the response (includes source_id, chunk_id)",
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether the agent needs more info from the user",
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question to ask the user if clarification is needed",
    )
    safety_status: SafetyStatus = Field(
        default=SafetyStatus.OK,
        description="Result of safety validation",
    )
    safety_message: Optional[str] = Field(
        default=None,
        description="Warning or block message if safety check triggered",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the agent encountered a problem",
    )
    model_used: str = Field(
        default="unknown",
        description="Name of the LLM model that produced the response",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation/session ID passed through from the request",
    )

    model_config = {"use_enum_values": True}
