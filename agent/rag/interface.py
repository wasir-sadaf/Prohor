"""
RAG integration contract — the interface the agent uses to retrieve
legal information.

The actual RAG pipeline (embeddings, vector store, retrieval logic)
is implemented as a separate component.  This module defines the
contract that both sides agree on:

    Agent  ──→  RAGClient.retrieve(query)  ──→  list[RAGResult]

A mock implementation (``MockRAGClient``) is provided for development
and testing.  A backend adapter (``BackendRAGClient``) connects to the
real Node.js legal search API.
"""

from __future__ import annotations

from typing import Optional, Protocol

from pydantic import BaseModel, Field

from agent.schemas.evidence import LegalEvidence
from agent.schemas.state import Intent


class RAGQuery(BaseModel):
    """Structured query sent to the RAG pipeline."""

    query_text: str = Field(description="Natural-language search query")
    intent: Optional[str] = Field(
        default=None,
        description="Detected intent to narrow retrieval scope",
    )
    top_k: int = Field(default=5, description="Max results to return")
    language: Optional[str] = Field(
        default=None,
        description="Preferred language of retrieved content",
    )


class RAGResult(BaseModel):
    """Raw result from the RAG pipeline before mapping to LegalEvidence."""

    content: str = Field(description="Retrieved text chunk")
    source_title: str = Field(default="")
    law_or_regulation: str = Field(default="")
    section_or_provision: Optional[str] = Field(default=None)
    source_url: Optional[str] = Field(default=None)
    issuing_authority: Optional[str] = Field(default=None)
    effective_date: Optional[str] = Field(default=None)
    relevance_score: float = Field(default=0.0)

    # ── Backend integration IDs ──────────────────────────────────
    source_id: Optional[str] = Field(default=None, description="UUID of legal_sources row")
    chunk_id: Optional[str] = Field(default=None, description="UUID of legal_chunks row")
    is_verified: bool = Field(default=False, description="Whether source is verified in DB")

    def to_evidence(self) -> LegalEvidence:
        """Convert this raw RAG result to the agent's evidence model."""
        return LegalEvidence(
            source_title=self.source_title,
            law_or_regulation=self.law_or_regulation,
            section_or_provision=self.section_or_provision,
            retrieved_content=self.content,
            source_url=self.source_url,
            issuing_authority=self.issuing_authority,
            effective_date=self.effective_date,
            source_id=self.source_id,
            chunk_id=self.chunk_id,
            is_verified=self.is_verified,
        )


class RAGClient(Protocol):
    """
    Protocol every RAG backend must implement.

    The agent only calls ``retrieve``; it never touches vector stores,
    embeddings, or any RAG-internal logic directly.
    """

    def retrieve(self, query: RAGQuery) -> list[RAGResult]:
        """
        Retrieve legal information relevant to ``query``.

        Returns a list of ``RAGResult`` objects, sorted by relevance.
        """
        ...

    @property
    def is_available(self) -> bool:
        """Whether the RAG backend is connected and ready."""
        ...
