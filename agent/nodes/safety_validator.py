"""
Safety validation node — enhanced with citation verification and
prompt injection protection.

Checks the generated response for:
- Legal advice disclaimers (the agent should inform, not advise).
- Potentially harmful content (instructions for crimes, violence).
- Fabricated legal citations (citations without backing evidence).
- Prompt injection attempts in retrieved/uploaded documents.
- Clarification responses (skip disclaimer for questions).

Citation verification:
    Only allows citations that exist in the retrieved LegalEvidence
    objects. Strips any citations the LLM may have invented.

Runs after the LLM generates a response, not before, because we need
the output text to validate.
"""

from __future__ import annotations

import re

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

# ── Prompt injection patterns ─────────────────────────────────────
# Detected in user queries and in retrieved/uploaded document text.
_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
    r"you\s+are\s+(now|a)\s+(different|new)\s+(ai|agent|assistant)",
    r"disregard\s+(previous|all|above)",
    r"reveal\s+(your|the)\s+(system|hidden)\s+prompt",
    r"show\s+me\s+(your|the)\s+(system|hidden)\s+prompt",
    r"what\s+(is|are)\s+(your|the)\s+(api|secret|environment)\s*(key|variable)",
    r"execute\s+(the\s+)?tool",
    r"run\s+(the\s+)?command",
    r"act\s+as\s+(if you are|a)\s+(different|new|admin|root)",
    r"<\/?system\s*>",
    r"<\/?instruction\s*>",
]

_INJECTION_REGEX = re.compile(
    "|".join(_INJECTION_PATTERNS), re.IGNORECASE
)

# ── Legal section/citation patterns that might be fabricated ──────
# Patterns like "Section 123", "Article 45", "§ 67" in LLM output
# that don't appear in any evidence.
_CITATION_PATTERN = re.compile(
    r"(?:Section|Article|§)\s*\d+[A-Za-z]?",
    re.IGNORECASE
)


def validate_safety(state: AgentState) -> AgentState:
    """
    Validate the agent's output for safety and compliance.

    Sets ``safety_status`` on the state.  If the response is blocked,
    replaces it with a safe fallback.

    Also performs citation verification: only citations backed by
    evidence are kept.
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

    # ── Check for prompt injection in the response ──────────────
    # (The LLM should not echo injection attempts)
    if _INJECTION_REGEX.search(response):
        state.safety_status = SafetyStatus.WARNING
        state.safety_message = "Potential prompt injection detected in response."
        state.generated_response = (
            "I cannot process that request. I'm Prohor, a legal literacy "
            "assistant. Please ask a question about Bangladeshi law."
        )
        return state

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

    # ── Citation verification ────────────────────────────────────
    # Only keep citations that are backed by evidence
    state.citations = _verify_citations(state)

    # ── Check for unverified legal claims ────────────────────────
    # If the LLM generated section/article references that don't
    # appear in evidence, warn about unverified claims
    if state.evidence:
        unverified = _find_unverified_citations(response, state.evidence)
        if unverified:
            state.safety_status = SafetyStatus.WARNING
            state.safety_message = (
                "Response contains legal references not backed by "
                "retrieved evidence. These may be unverified."
            )
            # Don't block — just warn and add disclaimer
            if "disclaimer" not in response_lower and "consult a" not in response_lower:
                state.generated_response = (
                    response
                    + "\n\nDisclaimer: This is general legal information, not "
                    "personal legal advice. Please consult a qualified lawyer "
                    "for your specific situation."
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


def _verify_citations(state: AgentState) -> list[str]:
    """
    Verify that all citations are backed by evidence.

    Only returns citations that correspond to LegalEvidence objects
    in the state. This prevents the LLM from inventing citations.
    """
    if not state.evidence:
        return []

    verified = [ev.format_citation() for ev in state.evidence]

    # If the state has citations set (from response generator), filter
    # them to only those backed by evidence
    if state.citations:
        # Keep only citations that match one of the verified ones
        filtered = []
        for citation in state.citations:
            for v in verified:
                if citation == v or v in citation or citation in v:
                    filtered.append(citation)
                    break
        # If filtering removed everything, fall back to verified
        return filtered if filtered else verified

    return verified


def _find_unverified_citations(response: str, evidence: list) -> list[str]:
    """
    Find legal section/article references in the response that don't
    appear in any evidence object.
    """
    # Extract all section/article references from the response
    response_refs = set(_CITATION_PATTERN.findall(response))

    # Extract all section/article references from evidence
    evidence_refs = set()
    for ev in evidence:
        if ev.section_or_provision:
            evidence_refs.add(ev.section_or_provision)
        # Also search the evidence content for section patterns
        content_refs = _CITATION_PATTERN.findall(ev.retrieved_content)
        for ref in content_refs:
            evidence_refs.add(ref)

    # Normalize for comparison
    def _normalize(ref: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "", ref.lower())

    evidence_normalized = {_normalize(ref) for ref in evidence_refs}

    unverified = []
    for ref in response_refs:
        if _normalize(ref) not in evidence_normalized:
            unverified.append(ref)

    return unverified


def sanitize_user_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection.

    This is a lightweight sanitizer that escapes common injection
    patterns. It's called before user input is passed to the LLM.
    """
    if not text:
        return ""

    # Remove or escape system/instruction tags
    sanitized = re.sub(r"<\/?system\s*>", "[FILTERED]", text, flags=re.IGNORECASE)
    sanitized = re.sub(r"<\/?instruction\s*>", "[FILTERED]", sanitized, flags=re.IGNORECASE)

    # Escape attempts to reference system prompts
    sanitized = re.sub(
        r"(?i)(reveal|show|display|print)\s+(your|the)\s+(system|hidden|secret)\s+(prompt|instructions?)",
        "[FILTERED]",
        sanitized,
    )

    # Escape attempts to execute tools/commands
    sanitized = re.sub(
        r"(?i)(execute|run|invoke|call)\s+(the\s+)?(tool|command|function|script)",
        "[FILTERED]",
        sanitized,
    )

    return sanitized


def sanitize_document_text(text: str) -> str:
    """
    Sanitize retrieved or uploaded document text before passing to LLM.

    Retrieved legal documents and uploaded documents are treated as
    untrusted reference data. Instructions embedded in them are not
    followed by the agent.
    """
    if not text:
        return ""

    # Apply the same sanitization as user input
    sanitized = sanitize_user_input(text)

    # Additionally, escape role markers that could confuse the LLM
    sanitized = re.sub(r"(?i)^user\s*:", "[DOC]", sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r"(?i)^assistant\s*:", "[DOC]", sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r"(?i)^system\s*:", "[DOC]", sanitized, flags=re.MULTILINE)

    return sanitized
