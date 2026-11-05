"""
RAG retrieval node.

Bridges the agent pipeline to the RAG interface. Takes the current
state (with classified intent and context analysis), calls the RAG
client, and stores the returned evidence in state.

When context analysis has identified a legal domain, the retrieval
query is enriched to improve relevance.
"""

from __future__ import annotations

from agent.rag.interface import RAGClient, RAGQuery
from agent.rag.mock import MockRAGClient
from agent.schemas.state import AgentState


# ── RAG client singleton ─────────────────────────────────────────
_rag_client: RAGClient | None = None


def get_rag_client() -> RAGClient:
    """Return the RAG client (mock by default). Replace with real impl later."""
    global _rag_client
    if _rag_client is None:
        _rag_client = MockRAGClient()
    return _rag_client


def set_rag_client(client: RAGClient) -> None:
    """Inject a custom RAG client (used by tests or real implementation)."""
    global _rag_client
    _rag_client = client


def retrieve_evidence(state: AgentState) -> AgentState:
    """
    Retrieve legal evidence from the RAG pipeline.

    Skips retrieval if the intent is OUT_OF_SCOPE or no tools include
    'rag_retrieve'. Enriches the query with context analysis results
    when available.
    """
    if "rag_retrieve" not in state.selected_tools:
        return state

    client = get_rag_client()

    if not client.is_available:
        state.error = "RAG service unavailable"
        return state

    # ── Build enriched query ────────────────────────────────────
    # If context analysis identified a legal domain, enrich the query
    # to improve retrieval relevance.
    query_text = state.user_query
    if state.legal_domain and state.legal_domain != "general legal":
        query_text = f"{state.legal_domain} {query_text}"

    rag_query = RAGQuery(
        query_text=query_text,
        intent=state.intent,
        top_k=5,
        language=state.language if isinstance(state.language, str) else None,
    )

    try:
        results = client.retrieve(rag_query)
        state.evidence = [r.to_evidence() for r in results]
        state.reasoning_status = "retrieving"
    except Exception as exc:
        state.error = f"RAG retrieval failed: {exc!s}"

    return state
