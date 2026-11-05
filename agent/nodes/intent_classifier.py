"""
Intent classification node.

Classifies the user's query into one of the predefined Intent
categories. Uses rule-based keyword matching (Bangla + English) which
is fast and deterministic — ideal for the current development phase.
When a real LLM is configured, the classification can be enhanced with
structured LLM outputs without changing the node signature.
"""

from __future__ import annotations

from agent.schemas.state import AgentState, Intent


# ── Keyword maps for rule-based classification ────────────────────
# Order matters: more specific intents are checked before general ones
# so that "how do I file a GD" matches COMPLAINT_GD_DRAFTING, not LEGAL_SCENARIO.
_INTENT_KEYWORDS: dict[Intent, list[str]] = {
    Intent.COMPLAINT_GD_DRAFTING: [
        "gd", "general diary", "জিডি", "fir", "first information report",
        "complaint", "police", "অভিযোগ", "থানা",
        "draft", "write application", "অভিযোগ লিখব",
    ],
    Intent.FIND_LEGAL_HELP: [
        "legal aid", "free lawyer", "সাহায্য", "ন্যায় সহায়তা",
        "pro bono", "poor", "can't afford", "নাজায়",
        "legal help", "legal assistance", "lawyer near",
        "legal services organisation", "nlaso",
    ],
    Intent.DOCUMENT_EXPLANATION: [
        "document", "contract", "deed", "clause", "দলিল",
        "চুক্তির ধারা", "what does it mean", "explain this",
        "analyze this", "terms and conditions", "মোহরা",
        "explain the clause", "what does this section mean",
        "explain this document", "explain this contract",
        "analyze this document", "analyze this contract",
    ],
    Intent.KNOW_YOUR_RIGHTS: [
        "rights", "অধিকার", "fundamental rights", "constitutional",
        "মৌলিক অধিকার", "human rights", "consumer rights",
        "worker rights", "tenant rights", "what am i entitled",
        "আমার অধিকার",
    ],
    Intent.LEGAL_SCENARIO_GUIDANCE: [
        "how to", "procedure", "process", "প্রক্রিয়া", "কীভাবে",
        "steps", "apply", "register", "file", "what should i do",
        "what can i do", "landlord", "employer", "eviction",
        "divorce", "talaq", "inheritance", "property dispute",
        "বাড়িওয়ালা", "চাকরি", "তালাক", "সম্পত্তি",
    ],
    Intent.OUT_OF_SCOPE: [
        "weather", "recipe", "game", "movie", "song",
        "cook", "restaurant", "hotel booking", "travel",
    ],
}


def classify_intent(state: AgentState) -> AgentState:
    """
    Classify user query into an Intent category.

    Uses rule-based keyword matching. Checks the most specific intent
    categories first so overlapping queries resolve to the right one.
    Falls back to GENERAL_LEGAL_QUESTION when nothing matches.
    """
    # ── Check if this is a follow-up / clarification answer ───────
    if state.awaiting_clarification:
        # User is answering a previous clarification question.
        # Preserve the intent from the previous turn.
        if state.intent is None:
            state.intent = Intent.GENERAL_LEGAL_QUESTION
        state.selected_tools = _select_tools_for_intent(state.intent)
        return state

    query_lower = state.user_query.lower()

    # Check each intent's keywords — first match wins
    for intent, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                state.intent = intent
                state.selected_tools = _select_tools_for_intent(intent)
                return state

    # Default to general legal question
    state.intent = Intent.GENERAL_LEGAL_QUESTION
    state.selected_tools = _select_tools_for_intent(Intent.GENERAL_LEGAL_QUESTION)
    return state


def _select_tools_for_intent(intent: Intent) -> list[str]:
    """Choose which tools the agent should invoke for this intent."""
    mapping: dict[Intent, list[str]] = {
        Intent.KNOW_YOUR_RIGHTS: ["rag_retrieve", "safety_check"],
        Intent.LEGAL_SCENARIO_GUIDANCE: ["rag_retrieve", "safety_check", "context_analysis"],
        Intent.DOCUMENT_EXPLANATION: ["rag_retrieve", "safety_check"],
        Intent.COMPLAINT_GD_DRAFTING: ["rag_retrieve", "safety_check", "context_analysis", "format_template"],
        Intent.FIND_LEGAL_HELP: ["rag_retrieve", "safety_check"],
        Intent.GENERAL_LEGAL_QUESTION: ["rag_retrieve", "safety_check", "context_analysis"],
        Intent.OUT_OF_SCOPE: [],
    }
    return mapping.get(intent, [])
