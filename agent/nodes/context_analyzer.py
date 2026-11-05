"""
Context analysis node.

Analyzes the user's query and conversation history to identify:
- Legal domain
- The actual problem the user is describing
- Relevant entities and circumstances
- Important missing information
- Whether clarification is necessary

Uses rule-based heuristics for the mock mode. When a real LLM is
configured, this can be enhanced with structured LLM outputs.
"""

from __future__ import annotations

from agent.schemas.state import AgentState, Intent


# ── Domain detection patterns ─────────────────────────────────────
# Maps keyword patterns to legal domains.
_DOMAIN_PATTERNS: list[tuple[list[str], str]] = [
    (["landlord", "tenant", "rent", "deposit", "eviction", "বাড়িওয়ালা", "বাড়ি ভাড়া", "ইভিকশন"],
     "landlord-tenant"),
    (["divorce", "talaq", "তালাক", "marriage", "বিবাহ", "maintenance", "dower", "denmohr", "দেনমোহর"],
     "family law"),
    (["gd", "general diary", "জিডি", "fir", "police", "thana", "থানা", "criminal", "crime", "assault", "theft"],
     "criminal procedure"),
    (["property", "land", "জমি", "সম্পত্তি", "mutation", "khatian", "খতিয়ান", "inheritance", "warish", "ওয়ারিশ"],
     "property law"),
    (["employment", "employer", "employee", "worker", "labor", "চাকরি", "salary", "terminated", "termination", "workplace", "শ্রম", "fired", "sacked", "dismissed", "job"],
     "employment law"),
    (["consumer", "product", "warranty", "refund", "defective", "ভোক্তা"],
     "consumer protection"),
    (["legal aid", "free lawyer", "সাহায্য", "ন্যায় সহায়তা", "pro bono"],
     "legal aid services"),
    (["document", "contract", "deed", "দলিল", "মোহরা", "agreement", "clause"],
     "document and contract law"),
    (["rights", "অধিকার", "fundamental", "constitutional", "মৌলিক অধিকার"],
     "constitutional law"),
]

# ── Entity extraction patterns ────────────────────────────────────
_ENTITY_PATTERNS: list[tuple[list[str], str]] = [
    (["landlord", "বাড়িওয়ালা"], "landlord"),
    (["tenant", "ভাড়াটিয়া"], "tenant"),
    (["employer", "মালিক", "boss", "company"], "employer"),
    (["employee", "কর্মী", "worker", "staff"], "employee"),
    (["police", "পুলিশ", "থানা"], "police"),
    (["deposit", "আমানত", "advance"], "security deposit"),
    (["rent", "ভাড়া"], "rent amount"),
    (["written agreement", "চুক্তি", "contract", "দলিল"], "written agreement"),
    (["divorce", "talaq", "তালাক"], "divorce"),
    (["marriage", "বিবাহ"], "marriage"),
    (["property", "জমি", "সম্পত্তি"], "property"),
    (["inheritance", "ওয়ারিশ", "warish"], "inheritance"),
    (["child", "সন্তান", "children"], "children"),
    (["wife", "স্ত্রী"], "wife"),
    (["husband", "স্বামী"], "husband"),
    (["salary", "বেতন", "wage"], "salary"),
    (["termination", "terminated", "fired", "চাকরি ছাড়া", "sacked", "dismissed"], "termination"),
]

# ── Missing info detection ───────────────────────────────────────
# Scenarios where clarification is typically needed.
_CLARIFICATION_TRIGGERS: list[dict] = [
    {
        "domain": "landlord-tenant",
        "keywords": ["deposit", "landlord", "rent", "eviction", "বাড়িওয়ালা"],
        "questions": [
            "Do you have a written rental agreement?",
            "Have you already moved out of the property?",
            "What reason did your landlord give for withholding the deposit?",
        ],
        "max_questions": 1,
    },
    {
        "domain": "family law",
        "keywords": ["divorce", "talaq", "তালাক"],
        "questions": [
            "Are you seeking divorce through mutual consent or one-sided?",
            "Do you have children from this marriage?",
            "Has the 90-day notice period been completed?",
        ],
        "max_questions": 1,
    },
    {
        "domain": "criminal procedure",
        "keywords": ["complaint", "fir", "অভিযোগ"],
        "questions": [
            "When did the incident occur?",
            "Which police station has jurisdiction over the area where the incident happened?",
        ],
        "max_questions": 1,
    },
    {
        "domain": "employment law",
        "keywords": ["termination", "terminated", "fired", "sacked", "চাকরি ছাড়া", "dismissed"],
        "questions": [
            "Were you given any notice or reason for termination?",
            "How long have you been employed there?",
        ],
        "max_questions": 1,
    },
]


def analyze_context(state: AgentState) -> AgentState:
    """
    Analyze the user's legal situation and determine if clarification
    is needed before proceeding with retrieval and reasoning.

    Sets: legal_domain, legal_situation, identified_entities,
    missing_info, needs_clarification, clarification_question.
    """
    # Skip context analysis if intent is out of scope
    if state.intent == "out_of_scope":
        return state

    query_lower = state.user_query.lower()

    # ── Detect legal domain ─────────────────────────────────────
    state.legal_domain = _detect_domain(query_lower)

    # ── Extract entities ─────────────────────────────────────────
    state.identified_entities = _extract_entities(query_lower)

    # ── Summarize legal situation ────────────────────────────────
    state.legal_situation = _summarize_situation(state, query_lower)

    # ── Check for missing info / clarification needs ─────────────
    # Only ask for clarification if this is not a follow-up answer
    if not state.awaiting_clarification:
        state = _check_clarification_needed(state, query_lower)
    else:
        # The user was previously asked a question and is now answering.
        # Clear the awaiting flag — we're proceeding with the answer.
        state.awaiting_clarification = False

    return state


def _detect_domain(query_lower: str) -> str:
    """Detect the legal domain from the query text."""
    for keywords, domain in _DOMAIN_PATTERNS:
        if any(kw in query_lower for kw in keywords):
            return domain
    return "general legal"


def _extract_entities(query_lower: str) -> list[str]:
    """Extract relevant entities and circumstances from the query."""
    entities = []
    for keywords, entity in _ENTITY_PATTERNS:
        if any(kw in query_lower for kw in keywords):
            if entity not in entities:
                entities.append(entity)
    return entities


def _summarize_situation(state: AgentState, query_lower: str) -> str:
    """Generate a brief description of the identified legal situation."""
    if not state.legal_domain or state.legal_domain == "general legal":
        return f"User has a general legal question about: {state.user_query[:120]}"

    domain_label = state.legal_domain.replace("-", " ")
    entity_str = ", ".join(state.identified_entities) if state.identified_entities else "unspecified parties"
    return f"User is seeking guidance on a {domain_label} matter involving {entity_str}."


def _check_clarification_needed(state: AgentState, query_lower: str) -> AgentState:
    """
    Determine if the user's query is missing important information
    that would benefit from clarification before proceeding.

    Only triggers clarification for scenario-based intents where
    specifics matter. General rights questions and simple queries
    don't need clarification.
    """
    # ── Don't ask for clarification on certain intents ──────────
    # KNOW_YOUR_RIGHTS and FIND_LEGAL_HELP are informational queries
    # that don't require situation-specific details
    if state.intent in ("know_your_rights", "find_legal_help", "out_of_scope", "document_explanation"):
        state.needs_clarification = False
        return state

    # ── Don't ask if we've already asked enough questions ───────
    if len(state.clarification_history) >= 1:
        state.needs_clarification = False
        return state

    # ── Check clarification triggers for matching domain ────────
    for trigger in _CLARIFICATION_TRIGGERS:
        if state.legal_domain == trigger["domain"]:
            if any(kw in query_lower for kw in trigger["keywords"]):
                # Find a question we haven't asked yet
                for question in trigger["questions"]:
                    if question not in state.clarification_history:
                        state.needs_clarification = True
                        state.clarification_question = question
                        state.missing_info.append(question)
                        state.awaiting_clarification = True
                        state.clarification_history.append(question)
                        return state

    state.needs_clarification = False
    return state
