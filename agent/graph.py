"""
LangGraph orchestration — defines the agent's reasoning flow with
conditional routing and specialized workflow integration.

Pipeline:
    START
      → classify_intent
      → (out_of_scope? → generate_response → END)
      → analyze_context
      → (needs_clarification? → generate_response → END)
      → retrieve_evidence
      → run_specialized_workflow
      → generate_response
      → validate_safety
      → END

The run_specialized_workflow node dispatches to the appropriate
specialized tool (scenario guidance, document explanation, complaint
drafting, or legal aid discovery) based on the identified intent.
For intents without a specialized workflow (KNOW_YOUR_RIGHTS,
GENERAL_LEGAL_QUESTION), the node is a passthrough.

For out-of-scope queries and clarification-needed cases, the graph
skips directly to response generation.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from agent.nodes.intent_classifier import classify_intent
from agent.nodes.context_analyzer import analyze_context
from agent.nodes.rag_retriever import retrieve_evidence
from agent.nodes.workflow_router import run_specialized_workflow
from agent.nodes.response_generator import generate_response
from agent.nodes.safety_validator import validate_safety
from agent.schemas.state import AgentState


def _route_after_context(state: AgentState) -> str:
    """
    Conditional routing after context analysis.

    - If clarification is needed → skip to response generation
    - If intent is out_of_scope → skip to response generation
    - Otherwise → proceed to RAG retrieval
    """
    if state.needs_clarification:
        return "generate_response"
    if state.intent == "out_of_scope":
        return "generate_response"
    return "retrieve_evidence"


def _route_after_classification(state: AgentState) -> str:
    """
    Conditional routing after intent classification.

    - Out of scope → skip context analysis, go straight to response
    - Everything else → proceed to context analysis
    """
    if state.intent == "out_of_scope":
        return "generate_response"
    return "analyze_context"


def build_graph():
    """
    Build and compile the LangGraph agent graph with conditional routing
    and specialized workflow integration.

    Returns a compiled graph that can be invoked with a state dict.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ───────────────────────────────────────────
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("analyze_context", analyze_context)
    graph.add_node("retrieve_evidence", retrieve_evidence)
    graph.add_node("run_workflow", run_specialized_workflow)
    graph.add_node("generate_response", generate_response)
    graph.add_node("validate_safety", validate_safety)

    # ── Define edges with conditional routing ────────────────────

    # START → classify_intent
    graph.add_edge(START, "classify_intent")

    # classify_intent → (out_of_scope? → generate_response : analyze_context)
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classification,
        {
            "analyze_context": "analyze_context",
            "generate_response": "generate_response",
        },
    )

    # analyze_context → (needs_clarification? → generate_response : retrieve_evidence)
    graph.add_conditional_edges(
        "analyze_context",
        _route_after_context,
        {
            "retrieve_evidence": "retrieve_evidence",
            "generate_response": "generate_response",
        },
    )

    # retrieve_evidence → run_workflow
    graph.add_edge("retrieve_evidence", "run_workflow")

    # run_workflow → generate_response
    graph.add_edge("run_workflow", "generate_response")

    # generate_response → validate_safety
    graph.add_edge("generate_response", "validate_safety")

    # validate_safety → END
    graph.add_edge("validate_safety", END)

    return graph.compile()


# ── Compiled graph singleton ─────────────────────────────────────
_compiled_graph = None


def get_graph():
    """Return the compiled graph (cached)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def reset_graph():
    """Clear the cached graph. Useful in tests."""
    global _compiled_graph
    _compiled_graph = None
