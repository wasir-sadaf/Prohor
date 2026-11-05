"""
Reasoner node — the core LLM call.

Constructs a system prompt with legal context, includes retrieved
evidence, calls the LLM, and stores the generated response.
"""

from __future__ import annotations

from agent.llm.factory import get_llm
from agent.schemas.message import ChatMessage
from agent.schemas.state import AgentState


def _build_system_prompt(state: AgentState) -> str:
    """Build a system prompt incorporating legal context and safety rules."""

    lang_instruction = (
        "Respond in Bangla (Bengali) script." if state.language == "bn"
        else "Respond in English."
    )

    base = (
        "You are Prohor, an AI legal literacy assistant for Bangladeshi "
        "citizens. You help users understand their legal rights, legal "
        "procedures, legal documents, complaint/GD filing, and legal aid "
        "services.\n\n"
        "IMPORTANT RULES:\n"
        "1. Always cite the specific law, section, or regulation.\n"
        "2. If you are unsure, say so — never fabricate legal information.\n"
        "3. Do not provide personal legal advice. Provide general legal "
        "information and suggest consulting a qualified lawyer.\n"
        "4. Keep responses clear, accessible, and actionable.\n"
        f"5. {lang_instruction}\n"
    )

    if state.evidence:
        evidence_text = "\n\n".join(
            f"[{i+1}] {ev.law_or_regulation}"
            f"{f', § {ev.section_or_provision}' if ev.section_or_provision else ''}\n"
            f"   {ev.retrieved_content}"
            for i, ev in enumerate(state.evidence)
        )
        base += f"\n\nRETRIEVED LEGAL EVIDENCE:\n{evidence_text}"
    else:
        base += "\n\nNo specific legal evidence was retrieved. Use your "
        base += "general knowledge but clearly state the limitation."

    return base


def generate_response(state: AgentState) -> AgentState:
    """Call the LLM to generate the agent's response."""

    if state.intent == "out_of_scope":
        state.generated_response = (
            "I'm Prohor, a legal literacy assistant. I can help you with "
            "Bangladeshi legal rights, procedures, documents, GD/complaint "
            "filing, and legal aid services. Please ask a legal question."
        )
        state.reasoning_status = "complete"
        return state

    llm = get_llm()

    system_prompt = _build_system_prompt(state)

    messages: list[ChatMessage] = [ChatMessage(role="system", content=system_prompt)]

    # Include conversation history for context
    for msg in state.conversation_history:
        messages.append(msg)

    # Add current user query
    messages.append(ChatMessage(role="user", content=state.user_query))

    state.reasoning_status = "reasoning"

    try:
        response_text = llm.chat(messages)
        state.generated_response = response_text
        state.reasoning_status = "complete"

        # Generate citations from evidence
        state.citations = [ev.format_citation() for ev in state.evidence]

    except Exception as exc:
        state.error = f"LLM call failed: {exc!s}"
        state.reasoning_status = "error"

    return state
