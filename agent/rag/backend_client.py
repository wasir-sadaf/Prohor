"""
Backend RAG client — connects to the Prohor Node.js backend legal
search API.

Uses the existing /api/legal/search endpoint to retrieve legal chunks
from Supabase PostgreSQL. Maps the backend response into RAGResult
objects that carry source_id and chunk_id for citation linkage.

Backend API response format (from legalController.js):
    {
        "success": true,
        "results": [
            {
                "id": "<chunk_uuid>",
                "source_id": "<source_uuid>",
                "chunk_index": 0,
                "content": "...",
                "page_number": null,
                "metadata": null
            },
            ...
        ]
    }

The legal_chunks table contains: id, source_id, chunk_index, content,
page_number, metadata.

The legal_sources table contains: id, title, source_type,
issuing_authority, url, language, publication_date, is_verified.

NOTE: The search endpoint returns legal_chunks only. To get full
source metadata (title, issuing_authority, url, is_verified), a second
request to /api/legal/sources/:id would be needed. This adapter makes
that request when source_id is available.

Environment variables:
    PROHOR_BACKEND_URL  — Base URL of the Node.js backend
    PROHOR_BACKEND_TOKEN — Bearer token for authenticated endpoints
"""

from __future__ import annotations

import os
from typing import Optional

from agent.rag.interface import RAGQuery, RAGResult


class BackendRAGClient:
    """
    RAG client that calls the Prohor Node.js backend legal search API.

    Uses the `requests` library (lazy import) to call:
      GET /api/legal/search?q=...
      GET /api/legal/sources/:id

    Falls back gracefully when the backend is unreachable.
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        backend_token: Optional[str] = None,
    ) -> None:
        self._backend_url = (backend_url or os.getenv("PROHOR_BACKEND_URL", "")).rstrip("/")
        self._backend_token = backend_token or os.getenv("PROHOR_BACKEND_TOKEN")
        self._session = None  # Lazy-init requests.Session

    @property
    def is_available(self) -> bool:
        """Check if the backend URL is configured."""
        return bool(self._backend_url)

    def _get_session(self):
        if self._session is None:
            import requests  # type: ignore
            self._session = requests.Session()
            if self._backend_token:
                self._session.headers.update({
                    "Authorization": f"Bearer {self._backend_token}"
                })
        return self._session

    def retrieve(self, query: RAGQuery) -> list[RAGResult]:
        """
        Retrieve legal chunks from the backend search API.

        Returns an empty list if the backend is unavailable or returns
        no results. Never raises — callers should check is_available
        first and handle empty results gracefully.
        """
        if not self.is_available:
            return []

        session = self._get_session()

        # ── Search legal chunks ────────────────────────────────────
        search_url = f"{self._backend_url}/api/legal/search"
        params = {"q": query.query_text}

        try:
            resp = session.get(search_url, params=params, timeout=10)
            if resp.status_code != 200:
                return []
            data = resp.json()
            if not data.get("success"):
                return []
        except Exception:
            return []

        raw_chunks = data.get("results", [])
        if not raw_chunks:
            return []

        # ── Fetch source metadata for unique source_ids ────────────
        source_cache: dict[str, dict] = {}
        unique_source_ids = set()
        for chunk in raw_chunks:
            sid = chunk.get("source_id")
            if sid:
                unique_source_ids.add(sid)

        for sid in unique_source_ids:
            source_info = self._fetch_source_metadata(sid)
            if source_info:
                source_cache[sid] = source_info

        # ── Map to RAGResult ───────────────────────────────────────
        results: list[RAGResult] = []
        for chunk in raw_chunks:
            sid = chunk.get("source_id")
            source = source_cache.get(sid, {}) if sid else {}

            results.append(RAGResult(
                content=chunk.get("content", ""),
                source_title=source.get("title", ""),
                law_or_regulation=source.get("title", ""),
                section_or_provision=None,  # Not directly available from chunk
                source_url=source.get("url"),
                issuing_authority=source.get("issuing_authority"),
                effective_date=source.get("publication_date"),
                relevance_score=0.9 - len(results) * 0.05,
                source_id=sid,
                chunk_id=chunk.get("id"),
                is_verified=source.get("is_verified", False),
            ))

        return results[:query.top_k]

    def _fetch_source_metadata(self, source_id: str) -> dict:
        """Fetch legal_sources metadata for a given source_id."""
        session = self._get_session()
        url = f"{self._backend_url}/api/legal/sources/{source_id}"

        try:
            resp = session.get(url, timeout=10)
            if resp.status_code != 200:
                return {}
            data = resp.json()
            if data.get("success") and data.get("source"):
                return data["source"]
        except Exception:
            pass

        return {}
