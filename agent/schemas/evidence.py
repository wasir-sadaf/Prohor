"""
Legal evidence model — structured representation of a piece of
legal information retrieved from the RAG pipeline.

This is the data model that the RAG integration contract returns and
that the agent carries through its state.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LegalEvidence(BaseModel):
    """A single piece of retrieved legal information with full citation metadata."""

    source_title: str = Field(description="Title of the source document or article")
    law_or_regulation: str = Field(description="Name of the law, regulation, or act")
    section_or_provision: Optional[str] = Field(
        default=None,
        description="Specific section, article, or provision number",
    )
    retrieved_content: str = Field(description="The actual text content retrieved")
    source_url: Optional[str] = Field(
        default=None,
        description="URL where the source can be verified",
    )
    issuing_authority: Optional[str] = Field(
        default=None,
        description="Government body or organization that issued this law",
    )
    effective_date: Optional[str] = Field(
        default=None,
        description="Date this law or provision took effect (ISO format when possible)",
    )

    def format_citation(self) -> str:
        """Return a human-readable citation string."""
        parts = [self.law_or_regulation]
        if self.section_or_provision:
            parts.append(f"§ {self.section_or_provision}")
        if self.issuing_authority:
            parts.append(f"({self.issuing_authority})")
        citation = " ".join(parts)
        if self.source_url:
            citation += f" — {self.source_url}"
        return citation
