"""
Response generation node.

Constructs a structured response by analyzing the user's situation,
evaluating retrieved legal evidence, and generating a response with:
- Understanding of the problem
- Relevant legal information
- Simple explanation
- Suggested next steps
- Supporting legal citations
- Important limitations or uncertainty

When a specialized workflow has produced structured output (draft text,
document analysis, legal aid providers), the response generator
incorporates that output into the final response.

Uses the LLM to produce the final response text. When the mock LLM
is active, produces deterministic, structured responses.
"""

from __future__ import annotations

from agent.llm.factory import get_llm
from agent.schemas.message import ChatMessage
from agent.schemas.state import AgentState, Intent


def _build_system_prompt(state: AgentState) -> str:
    """Build a system prompt incorporating legal context and safety rules."""

    lang_instruction = (
        "Respond in Bangla (Bengali) script using simple language that "
        "ordinary citizens can understand. Avoid overly technical legal jargon."
        if state.language == "bn"
        else "Respond in English using simple language that ordinary "
        "citizens can understand. Avoid overly technical legal jargon."
    )

    base = (
        "You are Prohor, an AI legal literacy assistant for Bangladeshi "
        "citizens. You help users understand their legal rights, legal "
        "procedures, legal documents, complaint/GD filing, and legal aid "
        "services.\n\n"
        "IMPORTANT RULES:\n"
        "1. Always cite the specific law, section, or regulation when available.\n"
        "2. If you are unsure, say so — NEVER fabricate legal provisions, "
        "sections, laws, or citations.\n"
        "3. Do not provide personal legal advice. Provide general legal "
        "information and suggest consulting a qualified lawyer.\n"
        "4. Structure your response with:\n"
        "   - Understanding: Brief acknowledgment of the user's situation\n"
        "   - Legal Information: Relevant laws and provisions explained simply\n"
        "   - Next Steps: Actionable guidance\n"
        "   - Citations: Specific laws/sections referenced\n"
        "   - Limitations: What remains uncertain or requires professional advice\n"
        f"5. {lang_instruction}\n"
    )

    # ── Add context analysis results ────────────────────────────
    context_parts = []
    if state.legal_domain:
        context_parts.append(f"Legal domain: {state.legal_domain}")
    if state.legal_situation:
        context_parts.append(f"Situation: {state.legal_situation}")
    if state.identified_entities:
        context_parts.append(f"Entities: {', '.join(state.identified_entities)}")
    if context_parts:
        base += "\n\nCONTEXT ANALYSIS:\n" + "\n".join(context_parts)

    # ── Add retrieved evidence ──────────────────────────────────
    if state.evidence:
        evidence_lines = []
        for i, ev in enumerate(state.evidence):
            line = f"[{i+1}] {ev.law_or_regulation}"
            if ev.section_or_provision:
                line += f", § {ev.section_or_provision}"
            line += f"\n   {ev.retrieved_content}"
            if ev.issuing_authority:
                line += f"\n   Authority: {ev.issuing_authority}"
            evidence_lines.append(line)
        base += "\n\nRETRIEVED LEGAL EVIDENCE:\n" + "\n\n".join(evidence_lines)
        base += (
            "\n\nIMPORTANT: Only cite laws/sections that appear in the "
            "evidence above. Do not invent new citations."
        )
    else:
        base += (
            "\n\nNo specific legal evidence was retrieved. Use your "
            "general knowledge but clearly state the limitation and "
            "do not cite specific sections without verification."
        )

    # ── Add specialized workflow output ─────────────────────────
    if state.draft_text:
        base += "\n\nCOMPLAINT/GD DRAFT (from drafting workflow):\n"
        base += state.draft_text
        base += (
            "\n\nPresent this draft to the user. Remind them to fill in "
            "placeholders and review before use. Do not claim it has been "
            "submitted."
        )

    if state.document_type:
        base += f"\n\nDOCUMENT ANALYSIS RESULT:\n"
        base += f"Document type identified: {state.document_type}\n"
        if state.next_steps:
            base += "Key findings:\n"
            for step in state.next_steps:
                base += f"- {step}\n"

    if state.legal_aid_providers:
        base += "\n\nLEGAL AID PROVIDERS FOUND:\n"
        for p in state.legal_aid_providers:
            base += f"- {p.get('name', 'Unknown')} ({p.get('service_type', '')})\n"

    if state.next_steps and not state.draft_text and not state.document_type:
        base += "\n\nSUGGESTED NEXT STEPS:\n"
        for i, step in enumerate(state.next_steps):
            base += f"{i+1}. {step}\n"

    if state.limitations:
        base += f"\n\nLIMITATIONS:\n{state.limitations}"

    return base


def _build_clarification_response(state: AgentState) -> str:
    """Build a response that asks a clarification question."""
    lang_prefix = ""
    if state.language == "bn":
        lang_prefix = "আপনার পরিস্থিতি আরও ভালোভাবে বুঝতে হলে, "
    else:
        lang_prefix = "To better understand your situation, "

    question = state.clarification_question or ""
    return f"{lang_prefix}{question}"


def _build_complaint_draft_response(state: AgentState) -> str:
    """Build a response that presents a complaint/GD draft."""
    bn = state.language == "bn"
    parts = []

    if bn:
        parts.append("নিচে আপনার অভিযোগ/জিডি আবেদনের একটি খসড়া দেওয়া হলো:\n")
    else:
        parts.append("Below is a draft of your complaint/GD application:\n")

    parts.append(state.draft_text)

    if state.missing_info:
        if bn:
            parts.append("\n\nঅনুপস্থিত তথ্য (পূরণ করুন):")
        else:
            parts.append("\n\nMissing information (please fill in):")
        for info in state.missing_info:
            parts.append(f"  - {info}")

    if state.limitations:
        parts.append(f"\n\n{state.limitations}")

    return "\n".join(parts)


def _build_document_analysis_response(state: AgentState) -> str:
    """Build a response presenting document analysis results."""
    bn = state.language == "bn"
    parts = []

    if bn:
        parts.append("নিচে আপনার দলিলের বিশ্লেষণ দেওয়া হলো:\n")
    else:
        parts.append("Below is the analysis of your document:\n")

    if state.document_type:
        if bn:
            parts.append(f"দলিলের ধরন: {state.document_type}")
        else:
            parts.append(f"Document type: {state.document_type}")

    if state.next_steps:
        if bn:
            parts.append("\nগুরুত্বপূর্ণ বিষয়:")
        else:
            parts.append("\nKey findings:")
        for step in state.next_steps:
            parts.append(f"  - {step}")

    if state.limitations:
        parts.append(f"\n{state.limitations}")

    return "\n".join(parts)


def _build_legal_aid_response(state: AgentState) -> str:
    """Build a response presenting legal aid information."""
    bn = state.language == "bn"
    parts = []

    if bn:
        parts.append("নিচে আইনি সহায়তা সংক্রান্ত তথ্য দেওয়া হলো:\n")
    else:
        parts.append("Here is information about legal aid services:\n")

    # Add evidence-based information
    if state.evidence:
        for ev in state.evidence:
            parts.append(f"- {ev.retrieved_content}")
            if ev.section_or_provision:
                parts.append(f"  ({ev.format_citation()})")

    # Add providers if available
    if state.legal_aid_providers:
        if bn:
            parts.append("\nযাচাই করা প্রতিষ্ঠান:")
        else:
            parts.append("\nVerified providers:")
        for p in state.legal_aid_providers:
            parts.append(f"- {p.get('name', 'Unknown')}")

    if state.limitations:
        parts.append(f"\n{state.limitations}")

    return "\n".join(parts)


def _build_scenario_response(state: AgentState) -> str:
    """Build a response for legal scenario guidance."""
    bn = state.language == "bn"
    parts = []

    domain_label = state.legal_domain or "general legal"
    domain_display = domain_label.replace("-", " ").title()

    if bn:
        parts.append(f"আপনার {domain_display} পরিস্থিতির জন্য নিচের আইনি তথ্যটি দেওয়া হলো।")
    else:
        parts.append(f"Based on your {domain_display} situation, here is the relevant legal information.")

    # Add evidence
    if state.evidence:
        if bn:
            parts.append("\nপ্রাসঙ্গিক আইন:")
        else:
            parts.append("\nRelevant Legal Information:")
        for i, ev in enumerate(state.evidence):
            citation = ev.format_citation()
            parts.append(f"\n{i+1}. {ev.retrieved_content}")
            if ev.section_or_provision:
                parts.append(f"   ({citation})")

    # Add next steps
    if state.next_steps:
        if bn:
            parts.append("\n\nপরবর্তী পদক্ষেপ:")
        else:
            parts.append("\n\nNext Steps:")
        for i, step in enumerate(state.next_steps):
            parts.append(f"{i+1}. {step}")

    if state.limitations:
        parts.append(f"\n\n{state.limitations}")

    return "\n".join(parts)


def generate_response(state: AgentState) -> AgentState:
    """Call the LLM to generate the agent's response."""

    # ── Out of scope: return immediately ─────────────────────────
    if state.intent == "out_of_scope":
        state.generated_response = (
            "I'm Prohor, a legal literacy assistant for Bangladeshi citizens. "
            "I can help you with:\n"
            "- Understanding your legal rights\n"
            "- Legal procedures and guidance\n"
            "- Legal document explanation\n"
            "- Complaint and GD application drafting\n"
            "- Finding legal aid services\n\n"
            "Please ask a question related to Bangladeshi law."
        )
        state.reasoning_status = "complete"
        return state

    # ── Clarification needed: ask and return early ──────────────
    if state.needs_clarification and state.clarification_question:
        state.generated_response = _build_clarification_response(state)
        state.reasoning_status = "complete"
        return state

    # ── Complaint/GD draft: present the draft ────────────────────
    if state.draft_text:
        state.generated_response = _build_complaint_draft_response(state)
        state.reasoning_status = "complete"
        state.citations = [ev.format_citation() for ev in state.evidence]
        return state

    # ── Document analysis: present analysis results ──────────────
    if state.document_type:
        state.generated_response = _build_document_analysis_response(state)
        state.reasoning_status = "complete"
        state.citations = [ev.format_citation() for ev in state.evidence]
        return state

    # ── Legal aid: present legal aid info ────────────────────────
    if state.intent == "find_legal_help":
        state.generated_response = _build_legal_aid_response(state)
        state.reasoning_status = "complete"
        state.citations = [ev.format_citation() for ev in state.evidence]
        return state

    # ── Scenario guidance: present structured guidance ──────────
    if state.intent == "legal_scenario_guidance" and state.next_steps:
        state.generated_response = _build_scenario_response(state)
        state.reasoning_status = "complete"
        state.citations = [ev.format_citation() for ev in state.evidence]
        return state

    # ── Default: call the LLM with full context ──────────────────
    llm = get_llm()
    system_prompt = _build_system_prompt(state)

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system_prompt)]

    # Include conversation history for context (preserves memory)
    for msg in state.conversation_history:
        messages.append(msg)

    # Add current user query
    messages.append(ChatMessage(role="user", content=state.user_query))

    state.reasoning_status = "reasoning"

    try:
        response_text = llm.chat(messages)
        state.generated_response = response_text
        state.reasoning_status = "complete"

        # Generate citations from evidence only
        state.citations = [ev.format_citation() for ev in state.evidence]

    except Exception as exc:
        state.error = f"LLM call failed: {exc!s}"
        state.reasoning_status = "error"

    return state
