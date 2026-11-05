"""
Document Explanation tool.

Analyzes document text (potentially extracted by the backend) and
produces a structured explanation:
- Document type identification
- Important clause extraction
- Plain-language explanation of legal terms
- Obligations and responsibilities
- Deadlines and conditions
- Potentially important or unclear clauses

IMPORTANT: This tool does not assume the document is legally valid.
It does not invent missing clauses or claim clauses are unlawful
without sufficient evidence.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field

from agent.rag.interface import RAGQuery
from agent.schemas.evidence import LegalEvidence


class DocumentAnalysisInput(BaseModel):
    """Input for the document explanation workflow."""

    document_text: str = Field(description="Extracted text of the document to analyze")
    user_question: Optional[str] = Field(
        default=None,
        description="Specific question about the document (if any)",
    )
    language: str = Field(default="en")
    page_references: Optional[dict] = Field(
        default=None,
        description="Mapping of text sections to page numbers, if available",
    )


class DocumentClause(BaseModel):
    """A single identified clause from the document."""

    clause_text: str = Field(description="The clause text as found in the document")
    explanation: str = Field(description="Plain-language explanation")
    category: str = Field(
        description="Category: 'obligation', 'condition', 'deadline', 'warning', 'general'",
    )
    page_reference: Optional[str] = Field(default=None)


class DocumentAnalysisResult(BaseModel):
    """Structured output from the document explanation workflow."""

    document_type: Optional[str] = Field(
        default=None,
        description="Identified type (e.g. 'rental agreement', 'employment contract')",
    )
    summary: str = Field(description="Overall summary of the document")
    clauses: list[DocumentClause] = Field(
        default_factory=list,
        description="Important identified clauses with explanations",
    )
    obligations: list[str] = Field(
        default_factory=list,
        description="Obligations and responsibilities identified",
    )
    deadlines: list[str] = Field(
        default_factory=list,
        description="Deadlines or time-sensitive conditions identified",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Potentially important or unclear clauses",
    )
    evidence: list[LegalEvidence] = Field(
        default_factory=list,
        description="Legal evidence retrieved for context",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="What could not be determined from the document",
    )


def explain_legal_document(
    input_data: DocumentAnalysisInput,
    rag_client,
) -> DocumentAnalysisResult:
    """
    Analyze a legal document and produce a structured explanation.

    Parameters
    ----------
    input_data : DocumentAnalysisInput
        Document text and optional question.
    rag_client : RAGClient
        RAG client for retrieving relevant legal context.

    Returns
    -------
    DocumentAnalysisResult
        Structured analysis with clauses, obligations, deadlines, warnings.
    """
    text = input_data.document_text
    lang = input_data.language

    # ── Identify document type ────────────────────────────────────
    doc_type = _identify_document_type(text)

    # ── Retrieve relevant legal context via RAG ──────────────────
    evidence: list[LegalEvidence] = []
    if rag_client.is_available:
        # Build a query from the document type + key terms
        query_text = doc_type or "legal document"
        if input_data.user_question:
            query_text = f"{query_text} {input_data.user_question}"

        rag_query = RAGQuery(
            query_text=query_text,
            top_k=3,
            language=lang,
        )
        results = rag_client.retrieve(rag_query)
        evidence = [r.to_evidence() for r in results]

    # ── Extract clauses ──────────────────────────────────────────
    clauses = _extract_clauses(text, input_data.page_references, lang)

    # ── Extract obligations ──────────────────────────────────────
    obligations = _extract_obligations(text, clauses, lang)

    # ── Extract deadlines ────────────────────────────────────────
    deadlines = _extract_deadlines(text, clauses, lang)

    # ── Extract warnings ─────────────────────────────────────────
    warnings = _extract_warnings(text, clauses, lang)

    # ── Build summary ────────────────────────────────────────────
    summary = _build_summary(doc_type, clauses, lang, input_data.user_question)

    # ── Build limitations ────────────────────────────────────────
    if lang == "bn":
        limitations = (
            "এই বিশ্লেষণ কেবল তথ্যের জন্য। এটি আইনি পরামর্শ নয়। "
            "নির্দিষ্ট পরিস্থিতির জন্য আইনজীবীর পরামর্শ নিন। "
            "এই বিশ্লেষণ নিশ্চিত করে না যে দলিলটি আইনি বৈধ।"
        )
    else:
        limitations = (
            "This analysis is for informational purposes only and does not "
            "constitute legal advice. Please consult a lawyer for your specific "
            "situation. This analysis does not verify the legal validity of "
            "the document."
        )

    return DocumentAnalysisResult(
        document_type=doc_type,
        summary=summary,
        clauses=clauses,
        obligations=obligations,
        deadlines=deadlines,
        warnings=warnings,
        evidence=evidence,
        limitations=limitations,
    )


# ── Document type detection ──────────────────────────────────────

_DOC_TYPE_PATTERNS: list[tuple[list[str], str]] = [
    (["rental agreement", "tenancy", "landlord", "tenant", "lease"],
     "rental agreement"),
    (["employment contract", "employment agreement", "job offer", "appointment letter"],
     "employment contract"),
    (["sale deed", "deed of sale", "property sale", "বাকি দলিল"],
     "sale deed"),
    (["loan agreement", "mortgage", "pledge"],
     "loan agreement"),
    (["partnership deed", "partnership agreement"],
     "partnership deed"),
    (["terms and conditions", "terms of service", "user agreement"],
     "terms and conditions"),
    (["non-disclosure", "nda", "confidentiality"],
     "non-disclosure agreement"),
    (["general diary", "gd application", "জিডি"],
     "GD application"),
    (["power of attorney", "এর অধিকার"],
     "power of attorney"),
]


def _identify_document_type(text: str) -> Optional[str]:
    """Identify the document type from its text content."""
    text_lower = text.lower()
    for keywords, doc_type in _DOC_TYPE_PATTERNS:
        if any(kw in text_lower for kw in keywords):
            return doc_type
    return None


# ── Clause extraction ────────────────────────────────────────────

# Patterns that indicate a clause boundary
_CLAUSE_PATTERNS = [
    re.compile(r"(\d+\.\s+[A-Z][^.]*\.)", re.DOTALL),
    re.compile(r"(Section\s+\d+[^.]*\.)", re.IGNORECASE),
    re.compile(r"(Article\s+\d+[^.]*\.)", re.IGNORECASE),
    re.compile(r"(\([a-z]\)\s+[A-Z][^.]*\.)", re.DOTALL),
    re.compile(r"(Clause\s+\d+[^.]*\.)", re.IGNORECASE),
]

# Keywords that indicate obligations
_OBLIGATION_KEYWORDS = [
    "shall", "must", "required to", "obliged to", "responsible for",
    "agrees to", "undertakes to", "বাধ্য", "দায়িত্ব",
]

# Keywords that indicate deadlines
_DEADLINE_KEYWORDS = [
    "within", "days of", "prior to", "not later than",
    "deadline", "expiry", "effective date", "until",
    "মেয়াদ", "অবধি", "দিনের মধ্যে",
]

# Keywords that indicate potentially problematic clauses
_WARNING_KEYWORDS = [
    "without notice", "at the discretion of", "sole discretion",
    "non-refundable", "waives the right", "auto-renew",
    "indemnify", "liability for", "penalty",
    "termination without cause", "binding arbitration",
]


def _extract_clauses(
    text: str,
    page_refs: Optional[dict],
    lang: str,
) -> list[DocumentClause]:
    """Extract and categorize important clauses from the document text."""
    clauses: list[DocumentClause] = []
    seen_texts: set[str] = set()

    # Try each pattern
    for pattern in _CLAUSE_PATTERNS:
        for match in pattern.finditer(text):
            clause_text = match.group(1).strip()
            # Avoid duplicates
            if clause_text.lower() in seen_texts:
                continue
            seen_texts.add(clause_text.lower())

            # Determine category
            lower = clause_text.lower()
            category = "general"
            if any(kw in lower for kw in _OBLIGATION_KEYWORDS):
                category = "obligation"
            elif any(kw in lower for kw in _DEADLINE_KEYWORDS):
                category = "deadline"
            elif any(kw in lower for kw in _WARNING_KEYWORDS):
                category = "warning"

            # Generate explanation
            explanation = _explain_clause(clause_text, lang)

            # Page reference
            page_ref = None
            if page_refs:
                for key, page in page_refs.items():
                    if key.lower() in clause_text.lower():
                        page_ref = f"Page {page}"
                        break

            clauses.append(DocumentClause(
                clause_text=clause_text,
                explanation=explanation,
                category=category,
                page_reference=page_ref,
            ))

    # If no structured clauses found, split by sentences and pick important ones
    if not clauses:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
        for sentence in sentences[:10]:  # Limit to 10 clauses
            lower = sentence.lower()
            category = "general"
            if any(kw in lower for kw in _OBLIGATION_KEYWORDS):
                category = "obligation"
            elif any(kw in lower for kw in _DEADLINE_KEYWORDS):
                category = "deadline"
            elif any(kw in lower for kw in _WARNING_KEYWORDS):
                category = "warning"

            explanation = _explain_clause(sentence + ".", lang)

            clauses.append(DocumentClause(
                clause_text=sentence + ".",
                explanation=explanation,
                category=category,
                page_reference=None,
            ))

    return clauses


def _explain_clause(clause_text: str, lang: str) -> str:
    """Generate a plain-language explanation of a clause."""
    lower = clause_text.lower()

    if any(kw in lower for kw in _OBLIGATION_KEYWORDS):
        if lang == "bn":
            return "এই ধারায় একটি দায়িত্ব বা বাধ্যবাধকতা নির্ধারণ করা হয়েছে।"
        return "This clause creates an obligation or responsibility."

    if any(kw in lower for kw in _DEADLINE_KEYWORDS):
        if lang == "bn":
            return "এই ধারায় একটি সময়সীমা বা তারিখ নির্ধারণ করা হয়েছে। তারিখটি মনে রাখুন।"
        return "This clause sets a deadline or time-sensitive condition. Make note of the date."

    if any(kw in lower for kw in _WARNING_KEYWORDS):
        if lang == "bn":
            return "এই ধারাটি বিশেষ মনোযোগের প্রয়োজন হতে পারে। বিস্তারিত বুঝতে আইনজীবীর পরামর্শ নিন।"
        return "This clause may require special attention. Consider consulting a lawyer for full understanding."

    if lang == "bn":
        return "সাধারণ ধারা। সম্পূর্ণ বোঝার জন্য পুরো পাঠ্যটি পড়ুন।"
    return "General clause. Read the full text for complete understanding."


def _extract_obligations(
    text: str,
    clauses: list[DocumentClause],
    lang: str,
) -> list[str]:
    """Extract obligations and responsibilities from clauses."""
    obligations = []
    for clause in clauses:
        if clause.category == "obligation":
            obligations.append(clause.clause_text)

    # Also scan raw text for obligation keywords
    text_lower = text.lower()
    for kw in _OBLIGATION_KEYWORDS:
        # Find sentences containing the keyword
        sentences = text.split(".")
        for sentence in sentences:
            if kw in sentence.lower() and sentence.strip() not in obligations:
                obligations.append(sentence.strip())

    # Deduplicate
    seen = set()
    unique = []
    for ob in obligations:
        if ob.lower() not in seen and len(ob) > 10:
            seen.add(ob.lower())
            unique.append(ob)

    return unique[:10]


def _extract_deadlines(
    text: str,
    clauses: list[DocumentClause],
    lang: str,
) -> list[str]:
    """Extract deadlines and time-sensitive conditions."""
    deadlines = []
    for clause in clauses:
        if clause.category == "deadline":
            deadlines.append(clause.clause_text)

    # Also scan raw text
    text_lower = text.lower()
    sentences = text.split(".")
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in _DEADLINE_KEYWORDS):
            if sentence.strip() not in deadlines:
                deadlines.append(sentence.strip())

    seen = set()
    unique = []
    for d in deadlines:
        if d.lower() not in seen and len(d) > 10:
            seen.add(d.lower())
            unique.append(d)

    return unique[:10]


def _extract_warnings(
    text: str,
    clauses: list[DocumentClause],
    lang: str,
) -> list[str]:
    """Extract potentially important or unclear clauses."""
    warnings = []
    for clause in clauses:
        if clause.category == "warning":
            warnings.append(clause.clause_text)

    # Also scan raw text
    sentences = text.split(".")
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in _WARNING_KEYWORDS):
            if sentence.strip() not in warnings:
                warnings.append(sentence.strip())

    seen = set()
    unique = []
    for w in warnings:
        if w.lower() not in seen and len(w) > 10:
            seen.add(w.lower())
            unique.append(w)

    return unique[:10]


def _build_summary(
    doc_type: Optional[str],
    clauses: list[DocumentClause],
    lang: str,
    user_question: Optional[str],
) -> str:
    """Build an overall summary of the document."""
    parts = []

    if doc_type:
        if lang == "bn":
            parts.append(f"দলিলের ধরন: {doc_type}")
        else:
            parts.append(f"Document type: {doc_type}")
    else:
        if lang == "bn":
            parts.append("দলিলের ধরন নির্ধারণ করা যায়নি।")
        else:
            parts.append("Document type could not be determined.")

    if clauses:
        obligation_count = sum(1 for c in clauses if c.category == "obligation")
        deadline_count = sum(1 for c in clauses if c.category == "deadline")
        warning_count = sum(1 for c in clauses if c.category == "warning")
        if lang == "bn":
            parts.append(
                f"বিশ্লেষণে {len(clauses)}টি ধারা পাওয়া গেছে "
                f"({obligation_count}টি দায়িত্ব, "
                f"{deadline_count}টি সময়সীমা, "
                f"{warning_count}টি সতর্কতা)।"
            )
        else:
            parts.append(
                f"Found {len(clauses)} clauses "
                f"({obligation_count} obligations, "
                f"{deadline_count} deadlines, "
                f"{warning_count} warnings)."
            )

    if user_question:
        if lang == "bn":
            parts.append(f"\nআপনার প্রশ্ন: {user_question}")
        else:
            parts.append(f"\nYour question: {user_question}")

    return "\n".join(parts)
