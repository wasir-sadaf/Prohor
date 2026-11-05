"""
Workflow router node.

After context analysis and RAG retrieval, this node dispatches to the
appropriate specialized workflow based on the identified intent. The
workflow tools produce structured outputs that are merged into
AgentState.

Routing logic:
    - LEGAL_SCENARIO_GUIDANCE → search_legal_procedures
    - DOCUMENT_EXPLANATION    → explain_legal_document
    - COMPLAINT_GD_DRAFTING   → generate_complaint_draft
    - FIND_LEGAL_HELP         → find_legal_aid
    - KNOW_YOUR_RIGHTS        → (uses existing evidence + response generator)
    - GENERAL_LEGAL_QUESTION  → (uses existing evidence + response generator)
    - OUT_OF_SCOPE            → (handled by response generator)

The node runs AFTER retrieve_evidence so that evidence is available
for workflows that need it.
"""

from __future__ import annotations

from agent.nodes.rag_retriever import get_rag_client
from agent.schemas.state import AgentState, Intent
from agent.tools.scenario_tool import (
    search_legal_procedures,
    ScenarioGuidanceInput,
)
from agent.tools.document_tool import (
    explain_legal_document,
    DocumentAnalysisInput,
)
from agent.tools.complaint_tool import (
    generate_complaint_draft,
    ComplaintDraftInput,
)
from agent.tools.legal_aid_tool import (
    find_legal_aid,
    LegalAidInput,
)


def run_specialized_workflow(state: AgentState) -> AgentState:
    """
    Dispatch to the appropriate specialized workflow based on intent.

    This node runs after RAG retrieval. It calls the specialized tool
    and merges the structured output into the agent state. The
    response generator will use this output to produce the final
    response.

    For intents that don't have a specialized workflow (KNOW_YOUR_RIGHTS,
    GENERAL_LEGAL_QUESTION), this node is a passthrough — the existing
    evidence and context flow directly to the response generator.
    """
    if state.intent == "out_of_scope":
        return state

    rag_client = get_rag_client()

    # ── Route to specialized workflow ────────────────────────────
    if state.intent == "legal_scenario_guidance":
        state = _run_scenario_guidance(state, rag_client)

    elif state.intent == "document_explanation":
        state = _run_document_explanation(state, rag_client)

    elif state.intent == "complaint_gd_drafting":
        state = _run_complaint_drafting(state)

    elif state.intent == "find_legal_help":
        state = _run_find_legal_aid(state, rag_client)

    # KNOW_YOUR_RIGHTS and GENERAL_LEGAL_QUESTION: passthrough
    # Evidence is already in state from retrieve_evidence node

    return state


def _run_scenario_guidance(state: AgentState, rag_client) -> AgentState:
    """Run the legal scenario guidance workflow."""
    input_data = ScenarioGuidanceInput(
        user_query=state.user_query,
        legal_domain=state.legal_domain,
        identified_entities=state.identified_entities,
        legal_situation=state.legal_situation,
        language=state.language if isinstance(state.language, str) else "en",
        conversation_history=[
            {"role": m.role, "content": m.content}
            for m in state.conversation_history
        ],
    )

    result = search_legal_procedures(input_data, rag_client)

    # Merge results into state
    state.evidence = result.evidence if result.evidence else state.evidence
    state.citations = result.citations if result.citations else state.citations
    state.next_steps = result.next_steps
    state.limitations = result.limitations
    state.reasoning_status = "reasoning"

    return state


def _run_document_explanation(state: AgentState, rag_client) -> AgentState:
    """Run the document explanation workflow."""
    # Document text may come from the request context or be embedded
    # in the user query
    doc_text = state.document_text or ""

    # If no explicit document text, check if the user's query contains
    # document-like text (long text with clauses/sections)
    if not doc_text and len(state.user_query) > 100:
        doc_text = state.user_query

    input_data = DocumentAnalysisInput(
        document_text=doc_text,
        user_question=state.user_query if len(state.user_query) < 100 else None,
        language=state.language if isinstance(state.language, str) else "en",
    )

    result = explain_legal_document(input_data, rag_client)

    # Merge results into state
    state.document_type = result.document_type
    state.evidence = result.evidence if result.evidence else state.evidence
    state.limitations = result.limitations

    # Build next_steps from obligations, deadlines, warnings
    steps = []
    for ob in result.obligations[:3]:
        steps.append(f"Obligation: {ob}")
    for dl in result.deadlines[:2]:
        steps.append(f"Deadline: {dl}")
    for wn in result.warnings[:2]:
        steps.append(f"Warning: {wn}")
    state.next_steps = steps

    return state


def _run_complaint_drafting(state: AgentState) -> AgentState:
    """Run the complaint/GD drafting workflow."""
    input_data = ComplaintDraftInput(
        user_query=state.user_query,
        legal_situation=state.legal_situation,
        identified_entities=state.identified_entities,
        language=state.language if isinstance(state.language, str) else "en",
        conversation_history=[
            {"role": m.role, "content": m.content}
            for m in state.conversation_history
        ],
    )

    result = generate_complaint_draft(input_data)

    # Merge results into state
    state.draft_text = result.draft_text
    state.draft_type = result.draft_type
    state.missing_info = result.missing_info
    state.limitations = result.review_reminder

    # If critical info is missing, set clarification
    if result.needs_clarification:
        state.needs_clarification = True
        state.clarification_question = result.clarification_question

    return state


def _run_find_legal_aid(state: AgentState, rag_client) -> AgentState:
    """Run the find legal help workflow."""
    # Extract location from request context if available
    location = None
    # Location could be passed through state in the future

    input_data = LegalAidInput(
        legal_issue=state.user_query,
        location=location,
        language=state.language if isinstance(state.language, str) else "en",
        legal_domain=state.legal_domain,
    )

    result = find_legal_aid(input_data, rag_client)

    # Merge results into state
    state.evidence = result.evidence if result.evidence else state.evidence
    state.citations = result.citations if result.citations else state.citations
    state.legal_aid_providers = [p.model_dump() for p in result.providers]
    state.limitations = result.limitations

    return state
