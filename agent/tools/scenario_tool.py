"""
Legal Scenario Guidance tool.

Provides step-by-step legal information for common legal situations
like landlord-tenant disputes, workplace issues, consumer rights, etc.

This tool retrieves relevant laws through the RAG interface and
generates structured guidance. It does NOT make definitive legal
judgments — it provides information and suggests next steps.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from agent.rag.interface import RAGQuery
from agent.schemas.evidence import LegalEvidence


class ScenarioGuidanceInput(BaseModel):
    """Input for the legal scenario guidance workflow."""

    user_query: str = Field(description="The user's situation description")
    legal_domain: Optional[str] = Field(default=None, description="Detected legal domain")
    identified_entities: list[str] = Field(default_factory=list)
    legal_situation: Optional[str] = Field(default=None)
    language: str = Field(default="en")
    conversation_history: list[dict] = Field(
        default_factory=list,
        description="Prior conversation for context",
    )


class ScenarioGuidanceResult(BaseModel):
    """Structured output from the scenario guidance workflow."""

    guidance_text: str = Field(description="Step-by-step legal guidance")
    legal_domain: str = Field(default="general")
    evidence: list[LegalEvidence] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(
        default_factory=list,
        description="Actionable next steps for the user",
    )
    limitations: Optional[str] = Field(
        default=None,
        description="What remains uncertain or requires professional advice",
    )


def search_legal_procedures(
    input_data: ScenarioGuidanceInput,
    rag_client,
) -> ScenarioGuidanceResult:
    """
    Retrieve legal procedures and generate guidance for the user's scenario.

    Uses the existing RAG client to retrieve relevant laws, then
    structures the guidance into steps and next steps.

    Parameters
    ----------
    input_data : ScenarioGuidanceInput
        The user's situation and context.
    rag_client : RAGClient
        The RAG client to use for legal evidence retrieval.

    Returns
    -------
    ScenarioGuidanceResult
        Structured guidance with evidence, citations, and next steps.
    """
    # ── Build enriched RAG query ─────────────────────────────────
    query_text = input_data.user_query
    if input_data.legal_domain and input_data.legal_domain != "general legal":
        query_text = f"{input_data.legal_domain} {query_text}"

    rag_query = RAGQuery(
        query_text=query_text,
        top_k=5,
        language=input_data.language,
    )

    # ── Retrieve evidence ────────────────────────────────────────
    evidence: list[LegalEvidence] = []
    if rag_client.is_available:
        results = rag_client.retrieve(rag_query)
        evidence = [r.to_evidence() for r in results]

    # ── Build guidance text ──────────────────────────────────────
    domain_label = input_data.legal_domain or "general legal"
    domain_display = domain_label.replace("-", " ").title()

    lang_prefix = ""
    if input_data.language == "bn":
        lang_prefix = "আপনার পরিস্থিতি বিবেচনায় নিচের আইনি তথ্যটি দেওয়া হলো।"
    else:
        lang_prefix = f"Based on your {domain_display} situation, here is the relevant legal information."

    # ── Build step-by-step guidance from evidence ────────────────
    steps: list[str] = []
    citations: list[str] = []

    for i, ev in enumerate(evidence):
        citation = ev.format_citation()
        citations.append(citation)
        step_text = f"{i+1}. {ev.retrieved_content}"
        if ev.section_or_provision:
            step_text += f" ({citation})"
        steps.append(step_text)

    # ── Generate next steps ──────────────────────────────────────
    next_steps = _generate_next_steps(domain_label, input_data.language)

    # ── Generate limitations ─────────────────────────────────────
    if input_data.language == "bn":
        limitations = (
            "এই তথ্য সাধারণ আইনি গাইডেন্স হিসেবে দেওয়া হয়েছে। "
            "আপনার নির্দিষ্ট পরিস্থিতির জন্য একজন যোগ্য আইনজীবীর "
            "পরামর্শ নেওয়ার পরামর্শ দেওয়া হলো।"
        )
    else:
        limitations = (
            "This guidance is based on general legal information. "
            "For your specific situation, please consult a qualified lawyer."
        )

    guidance_parts = [lang_prefix]
    if steps:
        if input_data.language == "bn":
            guidance_parts.append("\n\nপ্রাসঙ্গিক আইন:")
        else:
            guidance_parts.append("\n\nRelevant Legal Information:")
        guidance_parts.append("\n" + "\n".join(steps))

    if next_steps:
        if input_data.language == "bn":
            guidance_parts.append("\n\nপরবর্তী পদক্ষেপ:")
        else:
            guidance_parts.append("\n\nNext Steps:")
        for i, step in enumerate(next_steps):
            guidance_parts.append(f"\n{i+1}. {step}")

    guidance_text = "\n".join(guidance_parts)

    return ScenarioGuidanceResult(
        guidance_text=guidance_text,
        legal_domain=domain_label,
        evidence=evidence,
        citations=citations,
        next_steps=next_steps,
        limitations=limitations,
    )


def _generate_next_steps(domain: str, language: str) -> list[str]:
    """Generate domain-specific next steps."""
    bn = language == "bn"

    if domain == "landlord-tenant":
        if bn:
            return [
                "ভাড়া চুক্তি এবং সম্পর্কিত কাগজপত্র সংরক্ষণ করুন।",
                "বাড়িওয়ালার সাথে লিখিতভাবে যোগাযোগ করুন।",
                "প্রয়োজনে একজন আইনজীবীর পরামর্শ নিন।",
            ]
        return [
            "Keep copies of your rental agreement and related documents.",
            "Communicate with your landlord in writing.",
            "If unresolved, consult a lawyer or file a case in the Rent Controller court.",
        ]

    if domain == "employment law":
        if bn:
            return [
                "চাকরির চুক্তি এবং সম্পর্কিত কাগজপত্র সংরক্ষণ করুন।",
                "নিয়োগকর্তার কাছে লিখিতভাবে কারণ জানতে চান।",
                "প্রয়োজনে শ্রম আদালতে মামলা করতে পারেন।",
            ]
        return [
            "Keep copies of your employment contract and termination letter.",
            "Request written reasons for termination from your employer.",
            "If unresolved, you may file a case in the Labour Court.",
        ]

    if domain == "family law":
        if bn:
            return [
                "বিবাহের নিবন্ধন এবং সম্পর্কিত কাগজপত্র সংগ্রহ করুন।",
                "একজন পারিবারিক আইনজীবীর পরামর্শ নিন।",
                "প্রয়োজনে পারিবারিক আদালতে মামলা দায়ের করতে পারেন।",
            ]
        return [
            "Gather marriage registration documents and relevant records.",
            "Consult a family law lawyer for proper guidance.",
            "If needed, file a case in the Family Court.",
        ]

    if domain == "consumer protection":
        if bn:
            return [
                "পণ্যের রসিদ এবং ওয়ারেন্টি কার্ড সংরক্ষণ করুন।",
                "বিক্রেতার কাছে অভিযোগ জানান।",
                "প্রয়োজনে ভোক্তা অধিকার সংরক্ষণ অধিদপ্তরে অভিযোগ করুন।",
            ]
        return [
            "Keep receipts, warranty cards, and proof of purchase.",
            "File a formal complaint with the seller.",
            "If unresolved, complain to the Department of Consumer Protection.",
        ]

    # Default next steps
    if bn:
        return [
            "সম্পর্কিত কাগজপত্র সংরক্ষণ করুন।",
            "একজন আইনজীবীর পরামর্শ নিন।",
        ]
    return [
        "Gather and preserve all relevant documents.",
        "Consult a qualified lawyer for your specific situation.",
    ]
