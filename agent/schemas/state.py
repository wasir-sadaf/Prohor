"""
Agent state schema — the typed object that flows through every node
in the LangGraph pipeline.

Using Pydantic for validation means any node that produces malformed
state will fail fast with a clear error.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from agent.schemas.evidence import LegalEvidence
from agent.schemas.message import ChatMessage


class Intent(str, Enum):
    """Categories of legal queries the agent can handle."""

    GENERAL_LEGAL_QUESTION = "general_legal_question"
    KNOW_YOUR_RIGHTS = "know_your_rights"
    LEGAL_SCENARIO_GUIDANCE = "legal_scenario_guidance"
    DOCUMENT_EXPLANATION = "document_explanation"
    COMPLAINT_GD_DRAFTING = "complaint_gd_drafting"
    FIND_LEGAL_HELP = "find_legal_help"
    OUT_OF_SCOPE = "out_of_scope"


class Language(str, Enum):
    """Supported interface languages."""

    BANGLA = "bn"
    ENGLISH = "en"


class SafetyStatus(str, Enum):
    """Result of the safety validation step."""

    OK = "ok"
    WARNING = "warning"
    BLOCKED = "blocked"


class AgentState(BaseModel):
    """
    Typed state object carried through the LangGraph pipeline.

    Every node reads from and writes to this object. Using a Pydantic
    model instead of a raw dict gives us validation, autocompletion,
    and a clear contract between nodes.
    """

    # ── Input ───────────────────────────────────────────────────
    user_query: str = Field(default="")
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    language: Language = Field(default=Language.ENGLISH)

    # ── Intent classification ─────────────────────────────────────
    intent: Optional[Intent] = Field(default=None)

    # ── Context understanding ─────────────────────────────────────
    legal_domain: Optional[str] = Field(
        default=None,
        description="Legal domain (e.g. 'landlord-tenant', 'family law', 'criminal procedure')",
    )
    legal_situation: Optional[str] = Field(
        default=None,
        description="Brief description of the identified legal situation",
    )
    identified_entities: list[str] = Field(
        default_factory=list,
        description="Entities and circumstances identified from the query (e.g. 'landlord', 'deposit', 'written agreement')",
    )
    missing_info: list[str] = Field(
        default_factory=list,
        description="Important missing information that may require clarification",
    )

    # ── RAG retrieval results ────────────────────────────────────
    evidence: list[LegalEvidence] = Field(default_factory=list)

    # ── Clarification handling ───────────────────────────────────
    needs_clarification: bool = Field(default=False)
    clarification_question: Optional[str] = Field(default=None)
    clarification_history: list[str] = Field(
        default_factory=list,
        description="Questions already asked in this conversation to avoid repetition",
    )
    awaiting_clarification: bool = Field(
        default=False,
        description="True when agent has asked a question and is waiting for the user's answer",
    )

    # ── Tool selection ───────────────────────────────────────────
    selected_tools: list[str] = Field(
        default_factory=list,
        description="Names of tools the agent decided to invoke",
    )

    # ── Reasoning & response ─────────────────────────────────────
    reasoning_status: str = Field(
        default="pending",
        description="One of: 'pending', 'retrieving', 'reasoning', 'complete', 'error'",
    )
    generated_response: Optional[str] = Field(default=None)
    citations: list[str] = Field(default_factory=list)

    # ── Error & safety ───────────────────────────────────────────
    safety_status: SafetyStatus = Field(default=SafetyStatus.OK)
    safety_message: Optional[str] = Field(default=None)
    error: Optional[str] = Field(default=None)

    # ── Metadata ─────────────────────────────────────────────────
    iterations: int = Field(
        default=0,
        description="Number of graph iterations for the current query",
    )

    # ── Conversation memory ──────────────────────────────────────
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for conversation continuity",
    )
    is_followup: bool = Field(
        default=False,
        description="True if this query appears to be a follow-up to a previous conversation",
    )

    # ── Specialized workflow output ──────────────────────────────
    document_text: Optional[str] = Field(
        default=None,
        description="Document text passed from the backend for document explanation workflow",
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Identified document type (set by document analysis workflow)",
    )
    draft_text: Optional[str] = Field(
        default=None,
        description="Generated complaint/GD draft text (set by complaint drafting workflow)",
    )
    draft_type: Optional[str] = Field(
        default=None,
        description="Type of draft: 'gd', 'complaint', or 'fir'",
    )
    legal_aid_providers: list[dict] = Field(
        default_factory=list,
        description="Legal aid provider results (set by find legal help workflow)",
    )
    next_steps: list[str] = Field(
        default_factory=list,
        description="Actionable next steps generated by specialized workflows",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="What remains uncertain or requires professional advice",
    )

    model_config = {"use_enum_values": True}
