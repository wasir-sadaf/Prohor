"""Tests for the RAG integration interface and mock implementation."""

from agent.rag.interface import RAGQuery, RAGResult
from agent.rag.mock import MockRAGClient


class TestRAGQuery:
    def test_defaults(self):
        q = RAGQuery(query_text="test")
        assert q.query_text == "test"
        assert q.top_k == 5
        assert q.intent is None

    def test_with_intent(self):
        q = RAGQuery(query_text="test", intent="complaint_gd", top_k=3)
        assert q.intent == "complaint_gd"
        assert q.top_k == 3


class TestRAGResult:
    def test_to_evidence(self):
        result = RAGResult(
            content="Article 27 guarantees equality.",
            source_title="Constitution of Bangladesh",
            law_or_regulation="Constitution of Bangladesh",
            section_or_provision="Article 27",
            source_url="https://constitution.gov.bd/",
            issuing_authority="Parliament of Bangladesh",
            effective_date="1972-11-04",
            relevance_score=0.95,
        )
        evidence = result.to_evidence()
        assert evidence.source_title == "Constitution of Bangladesh"
        assert evidence.section_or_provision == "Article 27"
        assert evidence.retrieved_content == "Article 27 guarantees equality."
        assert evidence.source_url == "https://constitution.gov.bd/"


class TestMockRAGClient:
    def test_is_available(self):
        client = MockRAGClient()
        assert client.is_available is True

    def test_retrieve_rights(self):
        client = MockRAGClient()
        results = client.retrieve(RAGQuery(query_text="What are my fundamental rights?"))
        assert len(results) > 0
        assert any("Constitution" in r.law_or_regulation for r in results)

    def test_retrieve_gd(self):
        client = MockRAGClient()
        results = client.retrieve(RAGQuery(query_text="How do I file a GD?"))
        assert len(results) > 0
        assert any("GD" in r.content or "diary" in r.content.lower() or "police" in r.content.lower() for r in results)

    def test_retrieve_legal_aid(self):
        client = MockRAGClient()
        results = client.retrieve(RAGQuery(query_text="I need legal aid"))
        assert len(results) > 0
        assert any("Legal Aid" in r.law_or_regulation for r in results)

    def test_retrieve_no_match_returns_fallback(self):
        client = MockRAGClient()
        results = client.retrieve(RAGQuery(query_text="xyz random unknown topic"))
        assert len(results) == 1
        assert "mock" in results[0].content.lower()

    def test_top_k_limit(self):
        client = MockRAGClient()
        results = client.retrieve(RAGQuery(query_text="rights", top_k=1))
        assert len(results) <= 1
