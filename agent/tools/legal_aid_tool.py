"""
Find Legal Help tool.

Discovers relevant legal aid services and authorities. Provides a
clean provider interface for connecting to a verified legal aid
directory or backend API.

IMPORTANT: This tool does NOT fabricate organization names, contact
numbers, addresses, government services, or availability of legal
assistance. If verified information is unavailable, it clearly
acknowledges that limitation.
"""

from __future__ import annotations

from typing import Optional, Protocol

from pydantic import BaseModel, Field

from agent.rag.interface import RAGQuery
from agent.schemas.evidence import LegalEvidence


# ── Legal aid provider protocol ───────────────────────────────────
class LegalAidProvider(Protocol):
    """
    Protocol for a legal aid directory service.

    The real implementation will connect to a verified legal aid
    directory or backend API. The mock implementation returns
    clearly-labeled placeholder data.
    """

    def search_providers(
        self,
        legal_issue: str,
        location: Optional[str] = None,
        language: str = "en",
    ) -> list["LegalAidProvider"]:
        """
        Search for verified legal aid providers.

        Returns a list of providers with verified contact information.
        If no verified data is available, returns an empty list.
        """
        ...

    @property
    def is_available(self) -> bool:
        """Whether the provider directory is connected and ready."""
        ...


class LegalAidProvider(BaseModel):
    """A single legal aid service provider with verified information."""

    name: str = Field(description="Official name of the organization")
    service_type: str = Field(
        description="Type of service (e.g. 'government', 'ngo', 'pro bono')",
    )
    address: Optional[str] = Field(default=None, description="Verified address")
    phone: Optional[str] = Field(default=None, description="Verified phone number")
    website: Optional[str] = Field(default=None, description="Official website")
    eligibility: Optional[str] = Field(
        default=None,
        description="Eligibility criteria for this service",
    )
    languages_served: list[str] = Field(
        default_factory=list,
        description="Languages in which service is available",
    )
    verified: bool = Field(
        default=False,
        description="Whether this information has been verified against a reliable source",
    )


# ── Input/Output schemas ─────────────────────────────────────────
class LegalAidInput(BaseModel):
    """Input for the find legal aid workflow."""

    legal_issue: str = Field(description="The user's legal issue or category")
    location: Optional[str] = Field(
        default=None,
        description="User's general location (district/city), if voluntarily provided",
    )
    language: str = Field(default="en")
    legal_domain: Optional[str] = Field(default=None)


class LegalAidResult(BaseModel):
    """Structured output from the find legal aid workflow."""

    guidance_text: str = Field(description="Information about legal aid services")
    providers: list[LegalAidProvider] = Field(
        default_factory=list,
        description="Verified legal aid providers found",
    )
    evidence: list[LegalEvidence] = Field(
        default_factory=list,
        description="Legal evidence about legal aid rights and services",
    )
    citations: list[str] = Field(default_factory=list)
    limitations: Optional[str] = Field(
        default=None,
        description="What information is unavailable or unverified",
    )


# ── Mock provider (clearly labeled, no fabricated contacts) ──────
class MockLegalAidProvider:
    """
    Mock legal aid provider that does NOT fabricate contact information.

    Returns only the general legal framework for legal aid without
    inventing specific organization names, phone numbers, or addresses.
    """

    @property
    def is_available(self) -> bool:
        return True

    def search_providers(
        self,
        legal_issue: str,
        location: Optional[str] = None,
        language: str = "en",
    ) -> list[LegalAidProvider]:
        """
        Returns an empty list because the mock does not have access to
        verified provider data. The real implementation should connect
        to a verified legal aid directory.
        """
        return []


# ── Provider singleton ───────────────────────────────────────────
_provider: LegalAidProvider | None = None


def get_legal_aid_provider() -> LegalAidProvider:
    """Return the legal aid provider (mock by default)."""
    global _provider
    if _provider is None:
        _provider = MockLegalAidProvider()
    return _provider


def set_legal_aid_provider(provider: LegalAidProvider) -> None:
    """Inject a custom legal aid provider (for tests or real implementation)."""
    global _provider
    _provider = provider


def find_legal_aid(
    input_data: LegalAidInput,
    rag_client,
) -> LegalAidResult:
    """
    Find legal aid services and provide guidance.

    Uses the RAG interface to retrieve legal framework information
    about legal aid rights. Uses the legal aid provider to search for
    verified service providers.

    Parameters
    ----------
    input_data : LegalAidInput
        The user's legal issue, location, and language.
    rag_client : RAGClient
        RAG client for retrieving legal aid-related laws.

    Returns
    -------
    LegalAidResult
        Guidance text, verified providers (if any), and limitations.
    """
    # ── Retrieve legal framework via RAG ──────────────────────────
    evidence: list[LegalEvidence] = []
    citations: list[str] = []

    if rag_client.is_available:
        query_text = "legal aid services free lawyer Bangladesh"
        if input_data.legal_domain:
            query_text = f"{input_data.legal_domain} legal aid"

        rag_query = RAGQuery(
            query_text=query_text,
            top_k=3,
            language=input_data.language,
        )
        results = rag_client.retrieve(rag_query)
        evidence = [r.to_evidence() for r in results]
        citations = [ev.format_citation() for ev in evidence]

    # ── Search for verified providers ─────────────────────────────
    provider = get_legal_aid_provider()
    providers = []
    if provider.is_available:
        providers = provider.search_providers(
            legal_issue=input_data.legal_issue,
            location=input_data.location,
            language=input_data.language,
        )

    # ── Build guidance text ──────────────────────────────────────
    bn = input_data.language == "bn"
    parts = []

    if bn:
        parts.append(
            "বাংলাদেশে আইনি সহায়তা পাওয়ার জন্য নিম্নলিখিত তথ্য দেওয়া হলো:"
        )
    else:
        parts.append(
            "Here is information about legal aid services in Bangladesh:"
        )

    # ── Add legal framework ──────────────────────────────────────
    if evidence:
        if bn:
            parts.append("\nআইনি কাঠামো:")
        else:
            parts.append("\nLegal Framework:")
        for i, ev in enumerate(evidence):
            citation = ev.format_citation()
            parts.append(f"\n{i+1}. {ev.retrieved_content}")
            if ev.section_or_provision:
                parts.append(f"   ({citation})")

    # ── Add provider information ──────────────────────────────────
    if providers:
        verified = [p for p in providers if p.verified]
        if verified:
            if bn:
                parts.append("\n\nযাচাই করা আইনি সহায়তা প্রদানকারী:")
            else:
                parts.append("\n\nVerified Legal Aid Providers:")
            for p in verified:
                parts.append(f"\n- {p.name} ({p.service_type})")
                if p.address:
                    parts.append(f"  ঠিকানা: {p.address}" if bn else f"  Address: {p.address}")
                if p.phone:
                    parts.append(f"  ফোন: {p.phone}" if bn else f"  Phone: {p.phone}")
                if p.website:
                    parts.append(f"  ওয়েবসাইট: {p.website}" if bn else f"  Website: {p.website}")
                if p.eligibility:
                    parts.append(f"  যোগ্যতা: {p.eligibility}" if bn else f"  Eligibility: {p.eligibility}")
    else:
        if bn:
            parts.append(
                "\n\nবর্তমানে যাচাই করা আইনি সহায়তা প্রদানকারীদের তথ্য "
                "উপলব্ধ নেই। অনুগ্রহ করে নিম্নলিখিত উৎস থেকে তথ্য সংগ্রহ করুন:"
            )
            parts.append(
                "\n- জাতীয় আইনগত সহায়তা প্রদান সংস্থা (NLASO) - "
                "আপনার নিকটস্থ জেলা আইনগত সহায়তা কমিটির সাথে যোগাযোগ করুন"
            )
            parts.append(
                "- বাংলাদেশ বার কাউন্সিল - আইনজীবী রেফারেলের জন্য"
            )
        else:
            parts.append(
                "\n\nCurrently, verified legal aid provider information "
                "is not available. Please contact the following sources for "
                "legal aid information:"
            )
            parts.append(
                "\n- National Legal Aid Services Organisation (NLASO) - "
                "Contact your nearest District Legal Aid Committee"
            )
            parts.append(
                "- Bangladesh Bar Council - For lawyer referrals"
            )

    # ── Build limitations ─────────────────────────────────────────
    if not providers:
        if bn:
            limitations = (
                "নির্দিষ্ট প্রতিষ্ঠানের নাম, ঠিকানা, বা ফোন নম্বর যাচাই "
                "করা হয়নি। উপরের তথ্য সাধারণ গাইডেন্স হিসেবে ব্যবহার করুন "
                "এবং নিকটস্থ আইনি সহায়তা কমিটির সাথে সরাসরি যোগাযোগ করুন।"
            )
        else:
            limitations = (
                "Specific organization names, addresses, or phone numbers "
                "have not been verified. Use the information above as general "
                "guidance and contact your nearest legal aid committee directly."
            )
    else:
        limitations = None

    return LegalAidResult(
        guidance_text="\n".join(parts),
        providers=providers,
        evidence=evidence,
        citations=citations,
        limitations=limitations,
    )
