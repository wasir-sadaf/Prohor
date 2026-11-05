"""
RAG retrieval node.

Bridges the agent pipeline to the RAG interface. Takes the current
state (with classified intent and context analysis), calls the RAG
client, and stores the returned evidence in state.

When context analysis has identified a legal domain, the retrieval
query is enriched to improve relevance.

RAG client selection:
    - If PROHOR_BACKEND_URL is set, uses BackendRAGClient
    - Otherwise, uses MockRAGClient for local development
    - Can be overridden via set_rag_client() for testing
"""

from __future__ import annotations

import os

from agent.rag.interface import RAGClient, RAGQuery
from agent.rag.mock import MockRAGClient
from agent.rag.backend_client import BackendRAGClient
from agent.schemas.state import AgentState


# ── RAG client singleton ─────────────────────────────────────────
_rag_client: RAGClient | None = None


def get_rag_client() -> RAGClient:
    """Return the RAG client (auto-selected, cached)."""
    global _rag_client
    if _rag_client is not None:
        return _rag_client

    backend_url = os.getenv("PROHOR_BACKEND_URL", "").strip()
    if backend_url:
        _rag_client = BackendRAGClient(
            backend_url=backend_url,
            backend_token=os.getenv("PROHOR_BACKEND_TOKEN"),
        )
    else:
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
    when available. Handles empty results gracefully.
    """
    if "rag_retrieve" not in state.selected_tools:
        return state

    client = get_rag_client()

    if not client.is_available:
        state.error = "RAG service unavailable"
        return state

    # ── Build enriched query ────────────────────────────────────
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

        # ── Handle empty results ────────────────────────────────
        if not state.evidence:
            state.evidence = []
            # The response generator will acknowledge the gap
    except Exception as exc:
        state.error = f"RAG retrieval failed: {exc!s}"
        state.evidence = []

    return state
