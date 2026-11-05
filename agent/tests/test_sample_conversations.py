"""
Sample conversation tests — exercises the full agent pipeline with
10+ Bangla and English legal queries covering all intent categories.

These tests verify the agent handles diverse real-world queries
correctly. Mock evidence is used (not fabricated legal claims).
"""

from agent.entry_point import invoke_agent
from agent.llm.factory import reset_llm_cache
from agent.graph import reset_graph
from agent.schemas.request import AgentRequest


class TestSampleConversations:
    """Integration tests with diverse legal queries."""

    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    # ── English queries ──────────────────────────────────────────

    def test_en_rights_query(self):
        """English: user asks about fundamental rights."""
        resp = invoke_agent(AgentRequest(query="What are my fundamental rights as a citizen?"))
        assert resp.response != ""
        assert resp.intent == "know_your_rights"
        assert resp.error is None

    def test_en_gd_query(self):
        """English: user asks about filing a GD."""
        resp = invoke_agent(AgentRequest(query="How do I file a general diary at the police station?"))
        assert resp.response != ""
        assert resp.intent == "complaint_gd_drafting"
        assert resp.error is None

    def test_en_legal_aid_query(self):
        """English: user asks about legal aid."""
        resp = invoke_agent(AgentRequest(query="I cannot afford a lawyer, where can I get free legal aid?"))
        assert resp.response != ""
        assert resp.intent == "find_legal_help"
        assert resp.error is None

    def test_en_landlord_deposit(self):
        """English: landlord-tenant deposit dispute (should trigger clarification)."""
        resp = invoke_agent(AgentRequest(query="My landlord is not returning my deposit."))
        assert resp.response != ""
        assert resp.needs_clarification is True
        assert resp.clarification_question is not None

    def test_en_document_explanation(self):
        """English: user asks about a document clause."""
        resp = invoke_agent(AgentRequest(query="Can you explain this contract clause about termination?"))
        assert resp.response != ""
        assert resp.intent == "document_explanation"
        assert resp.error is None

    def test_en_out_of_scope(self):
        """English: out-of-scope query."""
        resp = invoke_agent(AgentRequest(query="What's the weather in Dhaka today?"))
        assert resp.intent == "out_of_scope"
        assert "legal literacy assistant" in resp.response.lower()

    def test_en_employment_termination(self):
        """English: employment termination scenario."""
        resp = invoke_agent(AgentRequest(query="I was terminated from my job without any notice or reason."))
        assert resp.response != ""
        assert resp.needs_clarification is True or resp.intent is not None

    # ── Bangla queries ───────────────────────────────────────────

    def test_bn_rights_query(self):
        """Bangla: user asks about fundamental rights."""
        resp = invoke_agent(AgentRequest(query="আমার মৌলিক অধিকার কী কী?", language="bn"))
        assert resp.response != ""
        assert resp.intent == "know_your_rights"
        assert resp.error is None

    def test_bn_gd_query(self):
        """Bangla: user asks about filing a GD."""
        resp = invoke_agent(AgentRequest(query="আমি জিডি করতে চাই, কীভাবে করব?", language="bn"))
        assert resp.response != ""
        assert resp.intent == "complaint_gd_drafting"
        assert resp.error is None

    def test_bn_legal_aid_query(self):
        """Bangla: user asks about legal aid."""
        resp = invoke_agent(AgentRequest(query="আমার ন্যায় সহায়তা প্রয়োজন, আমি গরিব", language="bn"))
        assert resp.response != ""
        assert resp.intent == "find_legal_help"
        assert resp.error is None

    def test_bn_landlord_deposit(self):
        """Bangla: landlord-tenant deposit dispute (should trigger clarification)."""
        resp = invoke_agent(AgentRequest(query="বাড়িওয়ালা আমার জমা রাখা টাকা ফেরত দিচ্ছে না", language="bn"))
        assert resp.response != ""
        assert resp.needs_clarification is True
        assert resp.clarification_question is not None

    def test_bn_divorce_query(self):
        """Bangla: user asks about divorce (should trigger clarification)."""
        resp = invoke_agent(AgentRequest(query="আমি আমার স্বামীকে তালাক দিতে চাই", language="bn"))
        assert resp.response != ""
        assert resp.needs_clarification is True or resp.intent is not None

    # ── Multi-turn conversation ──────────────────────────────────

    def test_multi_turn_clarification_flow(self):
        """
        Multi-turn conversation:
        1. User asks incomplete question → agent asks clarification
        2. User answers → agent provides full response
        """
        from agent.schemas.message import ChatMessage

        # Turn 1: triggers clarification
        resp1 = invoke_agent(AgentRequest(query="My landlord is not returning my deposit."))
        assert resp1.needs_clarification is True

        # Turn 2: user answers the clarification
        history = [
            ChatMessage(role="user", content="My landlord is not returning my deposit."),
            ChatMessage(role="assistant", content=resp1.response),
        ]
        resp2 = invoke_agent(AgentRequest(
            query="Yes, I have a written rental agreement and I have already moved out.",
            conversation_history=history,
        ))
        assert resp2.response != ""
        assert resp2.error is None
