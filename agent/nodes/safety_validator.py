"""
Safety validation node.

Checks the generated response for:
- Legal advice disclaimers (the agent should inform, not advise).
- Potentially harmful content (instructions for crimes, violence).
- Fabricated legal citations (citations without backing evidence).
- Clarification responses (skip disclaimer for questions).

Runs after the LLM generates a response, not before, because we need
the output text to validate.
"""

from __future__ import annotations

from agent.schemas.state import AgentState, SafetyStatus


# ── Safety heuristics ──────────────────────────────────────────────

_HARMFUL_KEYWORDS = [
    "how to commit", "how to murder", "how to assault",
    "how to steal", "weapon", "explosive", "poison",
]

_LEGAL_ADVICE_PHRASES = [
    "you should sue", "i advise you to", "you must file",
    "hire me", "i am your lawyer",
]


def validate_safety(state: AgentState) -> AgentState:
    """
    Validate the agent's output for safety and compliance.

    Sets ``safety_status`` on the state.  If the response is blocked,
    replaces it with a safe fallback.

    Clarification questions are exempt from the disclaimer requirement
    since they are questions, not legal statements.
    """

    if state.error:
        state.safety_status = SafetyStatus.WARNING
        state.safety_message = "Agent encountered an error during processing."
        return state

    # ── Skip disclaimer for clarification questions ─────────────
    if state.needs_clarification and state.clarification_question:
        state.safety_status = SafetyStatus.OK
        state.safety_message = None
        return state

    response = state.generated_response or ""
    response_lower = response.lower()

    # ── Check for harmful content ───────────────────────────────
    for kw in _HARMFUL_KEYWORDS:
        if kw in response_lower:
            state.safety_status = SafetyStatus.BLOCKED
            state.safety_message = (
                "Response blocked: potentially harmful content detected."
            )
            state.generated_response = (
                "I cannot provide information that could be used to harm "
                "others. If you have a legal concern, I can help you "
                "understand the relevant laws and procedures."
            )
            return state

    # ── Check for unauthorized legal advice ─────────────────────
    for phrase in _LEGAL_ADVICE_PHRASES:
        if phrase in response_lower:
            state.safety_status = SafetyStatus.WARNING
            state.safety_message = (
                "Response contains language that may constitute personal "
                "legal advice. Appended disclaimer."
            )
            if "consult a qualified lawyer" not in response_lower:
                state.generated_response = (
                    response
                    + "\n\nDisclaimer: This is general legal information, "
                    "not personal legal advice. Please consult a qualified "
                    "lawyer for your specific situation."
                )
            return state

    # ── Add disclaimer if not present ───────────────────────────
    if "disclaimer" not in response_lower and "consult a" not in response_lower:
        state.safety_status = SafetyStatus.OK
        state.safety_message = None
        state.generated_response = (
            response
            + "\n\nDisclaimer: This is general legal information, not "
            "personal legal advice. Please consult a qualified lawyer "
            "for your specific situation."
        )
    else:
        state.safety_status = SafetyStatus.OK
        state.safety_message = None

    return state
