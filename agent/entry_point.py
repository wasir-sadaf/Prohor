"""
Agent entry point — the single function the backend calls.

    from agent import invoke_agent, AgentRequest

    response = invoke_agent(AgentRequest(query="How do I file a GD?"))
    print(response.response)

This function is the public contract between the Node.js backend
and the Python agent. It accepts an AgentRequest, runs the full
LangGraph pipeline, and returns an AgentResponse.

Conversation Memory:
    The entry point detects follow-up queries by checking conversation
    history. When the last assistant message was a clarification question,
    the agent knows the user is now answering it, and preserves the
    previous intent and context.
"""

from __future__ import annotations

from agent.graph import get_graph
from agent.llm.factory import get_llm
from agent.schemas.request import AgentRequest
from agent.schemas.response import AgentResponse
from agent.schemas.state import AgentState


def _detect_followup(conversation_history: list) -> bool:
    """
    Detect if this is a follow-up query by checking if there's
    conversation history with prior assistant responses.
    """
    if not conversation_history:
        return False
    # Check if there's at least one prior assistant message
    for msg in conversation_history:
        if hasattr(msg, "role"):
            if msg.role == "assistant":
                return True
        elif isinstance(msg, dict):
            if msg.get("role") == "assistant":
                return True
    return False


def _detect_awaiting_clarification(conversation_history: list) -> bool:
    """
    Check if the last assistant message was a clarification question.

    If so, the user's current message is likely an answer to that
    question, and the agent should preserve the previous context.
    """
    if not conversation_history:
        return False

    # Find the last assistant message
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

    # Check if the last assistant message looks like a clarification question
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
    """
    Extract previously asked clarification questions from conversation
    history to avoid asking them again.
    """
    asked = []
    for msg in conversation_history:
        content = ""
        if hasattr(msg, "content"):
            content = msg.content
        elif isinstance(msg, dict):
            content = msg.get("content", "")

        lower = content.lower()
        # Look for clarification question patterns
        if "to better understand your situation" in lower or "আপনার পরিস্থিতি" in lower:
            # Extract the question part
            asked.append(content)
    return asked


def invoke_agent(request: AgentRequest) -> AgentResponse:
    """
    Run the Prohor legal agent pipeline.

    Parameters
    ----------
    request : AgentRequest
        Structured request containing the user query, language,
        conversation history, and optional context.

    Returns
    -------
    AgentResponse
        Structured response with the agent's answer, citations,
        evidence, safety status, and any error information.
    """
    # ── Detect follow-up and clarification state ─────────────────
    is_followup = _detect_followup(request.conversation_history)
    awaiting_clarification = _detect_awaiting_clarification(request.conversation_history)
    clarification_history = _extract_clarification_history(request.conversation_history)

    # ── Build initial state from the request ─────────────────────
    initial_state = AgentState(
        user_query=request.query,
        conversation_history=request.conversation_history,
        language=request.language,
        is_followup=is_followup,
        awaiting_clarification=awaiting_clarification,
        clarification_history=clarification_history,
    )

    # ── Run the LangGraph pipeline ──────────────────────────────
    graph = get_graph()
    final_state = graph.invoke(initial_state)

    # ── Handle state returned as dict (LangGraph may return dict) ─
    if isinstance(final_state, dict):
        final_state = AgentState(**final_state)

    # ── Determine which model was used ──────────────────────────
    try:
        model_used = get_llm().model_name
    except Exception:
        model_used = "unknown"

    # ── Build the response ──────────────────────────────────────
    return AgentResponse(
        response=final_state.generated_response or "",
        intent=final_state.intent,
        citations=final_state.citations,
        evidence=final_state.evidence,
        needs_clarification=final_state.needs_clarification,
        clarification_question=final_state.clarification_question,
        safety_status=final_state.safety_status,
        safety_message=final_state.safety_message,
        error=final_state.error,
        model_used=model_used,
    )
