"""
Agent entry point — the single function the backend calls.

    from agent import invoke_agent, AgentRequest

    response = invoke_agent(AgentRequest(query="How do I file a GD?"))
    print(response.response)

This function is the public contract between the Node.js backend
and the Python agent. It accepts an AgentRequest, runs the full
LangGraph pipeline, and returns an AgentResponse.

The backend maps:
    conversation_id → session_id (in AgentRequest)
    messages history → conversation_history
    extracted document text → context["document_text"]

The response includes citation_entries with source_id and chunk_id
so the backend can save message_sources relationships.
"""

from __future__ import annotations

from agent.graph import get_graph, reset_graph
from agent.llm.factory import get_llm, reset_llm_cache
from agent.schemas.request import AgentRequest
from agent.schemas.response import AgentResponse, CitationEntry
from agent.schemas.state import AgentState


def _detect_followup(conversation_history: list) -> bool:
    """Detect if this is a follow-up query by checking for prior assistant messages."""
    if not conversation_history:
        return False
    for msg in conversation_history:
        if hasattr(msg, "role"):
            if msg.role == "assistant":
                return True
        elif isinstance(msg, dict):
            if msg.get("role") == "assistant":
                return True
    return False


def _detect_awaiting_clarification(conversation_history: list) -> bool:
    """Check if the last assistant message was a clarification question."""
    if not conversation_history:
        return False

    last_assistant = None
    for msg in reversed(conversation_history):
        if hasattr(msg, "role"):
            if msg.role == "assistant":
                last_assistant = msg.content
                break
        elif isinstance(msg, dict):
            if msg.get("role") == "assistant":
                last_assistant = msg.get("content", "")
                break

    if not last_assistant:
        return False

    lower = last_assistant.lower()
    question_markers = [
        "to better understand your situation",
        "আপনার পরিস্থিতি আরও ভালোভাবে বুঝতে হলে",
        "do you have a written",
        "have you already moved",
        "what reason did",
        "are you seeking divorce",
        "do you have children",
        "when did the incident",
        "which police station",
        "were you given any notice",
        "how long have you been employed",
    ]
    return any(marker in lower for marker in question_markers)


def _extract_clarification_history(conversation_history: list) -> list[str]:
    """Extract previously asked clarification questions from conversation history."""
    asked = []
    for msg in conversation_history:
        content = ""
        if hasattr(msg, "content"):
            content = msg.content
        elif isinstance(msg, dict):
            content = msg.get("content", "")

        lower = content.lower()
        if "to better understand your situation" in lower or "আপনার পরিস্থিতি" in lower:
            asked.append(content)
    return asked


def _build_citation_entries(evidence: list) -> list[CitationEntry]:
    """Build structured citation entries with source/chunk IDs for backend linkage."""
    entries = []
    for ev in evidence:
        entries.append(CitationEntry(
            citation_text=ev.format_citation(),
            source_id=ev.source_id,
            chunk_id=ev.chunk_id,
            law_or_regulation=ev.law_or_regulation,
            section_or_provision=ev.section_or_provision,
            is_verified=ev.is_verified,
        ))
    return entries


def invoke_agent(request: AgentRequest) -> AgentResponse:
    """
    Run the Prohor legal agent pipeline.

    Parameters
    ----------
    request : AgentRequest
        Structured request containing the user query, language,
        conversation history, session_id, and optional context.

    Returns
    -------
    AgentResponse
        Structured response with the agent's answer, citations,
        evidence (with source_id/chunk_id), safety status, and
        citation entries for backend message_sources linkage.
    """
    # ── Detect follow-up and clarification state ─────────────────
    is_followup = _detect_followup(request.conversation_history)
    awaiting_clarification = _detect_awaiting_clarification(request.conversation_history)
    clarification_history = _extract_clarification_history(request.conversation_history)

    # ── Extract document text from request context ──────────────
    document_text = request.document_text

    # ── Build initial state from the request ─────────────────────
    initial_state = AgentState(
        user_query=request.query,
        conversation_history=request.conversation_history,
        language=request.language,
        is_followup=is_followup,
        awaiting_clarification=awaiting_clarification,
        clarification_history=clarification_history,
        session_id=request.session_id,
        document_text=document_text,
    )

    # ── Run the LangGraph pipeline ──────────────────────────────
    try:
        graph = get_graph()
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        # ── Fallback for graph execution failure ─────────────────
        return AgentResponse(
            response=(
                "I apologize, an error occurred while processing your request. "
                "Please try again later."
            ),
            error=f"Agent pipeline failed: {exc!s}",
            safety_status="warning",
            safety_message="Pipeline execution error",
            session_id=request.session_id,
        )

    # ── Handle state returned as dict (LangGraph may return dict) ─
    if isinstance(final_state, dict):
        final_state = AgentState(**final_state)

    # ── Determine which model was used ──────────────────────────
    try:
        model_used = get_llm().model_name
    except Exception:
        model_used = "unknown"

    # ── Build citation entries from evidence ───────────────────
    citation_entries = _build_citation_entries(final_state.evidence)

    # ── Build the response ──────────────────────────────────────
    return AgentResponse(
        response=final_state.generated_response or "",
        intent=final_state.intent,
        citations=final_state.citations,
        citation_entries=citation_entries,
        evidence=final_state.evidence,
        needs_clarification=final_state.needs_clarification,
        clarification_question=final_state.clarification_question,
        safety_status=final_state.safety_status,
        safety_message=final_state.safety_message,
        error=final_state.error,
        model_used=model_used,
        session_id=request.session_id,
    )
