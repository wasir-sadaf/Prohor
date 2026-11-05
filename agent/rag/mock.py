"""
Mock RAG client — returns canned legal evidence for development and
testing without a real vector store.

The mock data covers the core legal domains Prohor serves so the full
agent pipeline can produce realistic-looking responses.
"""

from __future__ import annotations

from agent.rag.interface import RAGQuery, RAGResult


# ── Mock legal knowledge base ────────────────────────────────────
# Each entry maps keywords to canned RAG results.

_MOCK_KB: list[dict] = [
    {
        "keywords": ["rights", "অধিকার", "fundamental", "constitution"],
        "results": [
            {
                "content": (
                    "Article 27: All citizens are equal before law "
                    "and are entitled to equal protection of law."
                ),
                "source_title": "Constitution of Bangladesh",
                "law_or_regulation": "Constitution of Bangladesh",
                "section_or_provision": "Article 27",
                "source_url": "https://constitution.gov.bd/",
                "issuing_authority": "Parliament of Bangladesh",
                "effective_date": "1972-11-04",
            },
            {
                "content": (
                    "Article 32: No person shall be deprived of life or "
                    "personal liberty save in accordance with law."
                ),
                "source_title": "Constitution of Bangladesh",
                "law_or_regulation": "Constitution of Bangladesh",
                "section_or_provision": "Article 32",
                "source_url": "https://constitution.gov.bd/",
                "issuing_authority": "Parliament of Bangladesh",
                "effective_date": "1972-11-04",
            },
        ],
    },
    {
        "keywords": ["gd", "general diary", "জিডি", "police", "complaint"],
        "results": [
            {
                "content": (
                    "A General Diary (GD) can be filed at any police "
                    "station. The OC must accept and register the GD "
                    "entry. No fee is required for filing a GD."
                ),
                "source_title": "Police Regulations Bengal",
                "law_or_regulation": "Police Regulations, Bengal (PRB)",
                "section_or_provision": "Chapter 24",
                "source_url": None,
                "issuing_authority": "Bangladesh Police",
                "effective_date": None,
            },
            {
                "content": (
                    "To file a complaint (FIR), visit the police station "
                    "with jurisdiction over the area where the incident "
                    "occurred. Under Section 154 CrPC, police must "
                    "register the FIR if a cognizable offense is disclosed."
                ),
                "source_title": "Code of Criminal Procedure",
                "law_or_regulation": "Code of Criminal Procedure, 1898",
                "section_or_provision": "Section 154",
                "source_url": None,
                "issuing_authority": "Parliament of Bangladesh",
                "effective_date": "1898-01-01",
            },
        ],
    },
    {
        "keywords": ["legal aid", "aid", "free lawyer", "সাহায্য"],
        "results": [
            {
                "content": (
                    "Under the Legal Aid Services Act 2000, indigent "
                    "persons are entitled to free legal aid. Eligible "
                    "categories include women, children, disabled persons, "
                    "and those with income below poverty line."
                ),
                "source_title": "Legal Aid Services Act, 2000",
                "law_or_regulation": "Legal Aid Services Act, 2000",
                "section_or_provision": "Section 5",
                "source_url": None,
                "issuing_authority": "National Legal Aid Services Organisation (NLASO)",
                "effective_date": "2000-01-01",
            },
        ],
    },
    {
        "keywords": ["divorce", "talaq", "family", "marriage", "বিবাহ"],
        "results": [
            {
                "content": (
                    "Under Muslim Family Law Ordinance 1961, a husband "
                    "must give 90 days notice of divorce to the local "
                    "Union Parishad chairman. Failure to give notice "
                    "is punishable by imprisonment."
                ),
                "source_title": "Muslim Family Law Ordinance, 1961",
                "law_or_regulation": "Muslim Family Laws Ordinance, 1961",
                "section_or_provision": "Section 7",
                "source_url": None,
                "issuing_authority": "Parliament of Pakistan (as adopted by Bangladesh)",
                "effective_date": "1961-07-15",
            },
        ],
    },
    {
        "keywords": ["document", "contract", "deed", "deed registration"],
        "results": [
            {
                "content": (
                    "Registration of documents is governed by the "
                    "Registration Act 1908. Documents involving transfer "
                    "of immovable property valued above Tk 100 must be "
                    "registered with the Sub-Registrar."
                ),
                "source_title": "Registration Act, 1908",
                "law_or_regulation": "Registration Act, 1908",
                "section_or_provision": "Section 17",
                "source_url": None,
                "issuing_authority": "British India (as adopted by Bangladesh)",
                "effective_date": "1908-01-01",
            },
        ],
    },
]


class MockRAGClient:
    """Deterministic mock RAG client for development."""

    @property
    def is_available(self) -> bool:
        return True

    def retrieve(self, query: RAGQuery) -> list[RAGResult]:
        results: list[RAGResult] = []
        query_lower = query.query_text.lower()

        for entry in _MOCK_KB:
            if any(kw in query_lower for kw in entry["keywords"]):
                for r in entry["results"]:
                    results.append(
                        RAGResult(
                            content=r["content"],
                            source_title=r["source_title"],
                            law_or_regulation=r["law_or_regulation"],
                            section_or_provision=r.get("section_or_provision"),
                            source_url=r.get("source_url"),
                            issuing_authority=r.get("issuing_authority"),
                            effective_date=r.get("effective_date"),
                            relevance_score=0.95 - len(results) * 0.05,
                        )
                    )

        # Always return at least one result so the pipeline exercises
        # the evidence-handling path
        if not results:
            results.append(
                RAGResult(
                    content=(
                        "No specific legal provision found in the mock "
                        "knowledge base for this query."
                    ),
                    source_title="Prohor Mock KB",
                    law_or_regulation="N/A",
                    section_or_provision=None,
                    source_url=None,
                    issuing_authority=None,
                    effective_date=None,
                    relevance_score=0.1,
                )
            )

        return results[:query.top_k]
