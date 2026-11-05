"""Integration tests for the full agent pipeline via invoke_agent."""

from agent.entry_point import invoke_agent
from agent.llm.factory import reset_llm_cache
from agent.graph import reset_graph


class TestInvokeAgent:
    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_basic_query(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="What are my fundamental rights?")
        resp = invoke_agent(req)

        assert resp.response != ""
        assert resp.intent is not None
        assert resp.safety_status == "ok"

    def test_gd_query(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="How do I file a GD?")
        resp = invoke_agent(req)

        assert resp.response != ""
        assert resp.intent == "complaint_gd_drafting"
        # Mock RAG should find GD-related evidence
        assert len(resp.evidence) > 0

    def test_out_of_scope(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="What's the weather today?")
        resp = invoke_agent(req)

        assert "legal literacy assistant" in resp.response.lower()
        assert resp.intent == "out_of_scope"

    def test_citations_populated(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="Tell me about my constitutional rights")
        resp = invoke_agent(req)

        # Mock RAG returns Constitution-related results
        if resp.evidence:
            assert len(resp.citations) > 0
            assert any("Constitution" in c for c in resp.citations)

    def test_bangla_language(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="আমার অধিকার কী কী?", language="bn")
        resp = invoke_agent(req)

        assert resp.response != ""
        assert resp.intent is not None

    def test_with_conversation_history(self):
        from agent.schemas.request import AgentRequest
        from agent.schemas.message import ChatMessage

        history = [
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello! How can I help you with legal information?"),
        ]
        req = AgentRequest(
            query="Tell me about filing a complaint",
            conversation_history=history,
        )
        resp = invoke_agent(req)

        assert resp.response != ""

    def test_model_used_in_response(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="What is legal aid?")
        resp = invoke_agent(req)

        assert resp.model_used != "unknown"
        assert resp.model_used == "mock-llm-v1"

    def test_safety_disclaimer_appended(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="What are my legal rights?")
        resp = invoke_agent(req)

        assert "disclaimer" in resp.response.lower()

    def test_no_error_on_normal_query(self):
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="How to get legal aid in Bangladesh?")
        resp = invoke_agent(req)

        assert resp.error is None

    def test_clarification_for_landlord_deposit(self):
        """Test that the agent asks a clarification question for an incomplete landlord-tenant scenario."""
        from agent.schemas.request import AgentRequest

        req = AgentRequest(query="My landlord is not returning my deposit.")
        resp = invoke_agent(req)

        assert resp.needs_clarification is True
        assert resp.clarification_question is not None
        # Should ask about rental agreement or similar
        assert resp.response != ""

    def test_followup_after_clarification(self):
        """Test that a follow-up after clarification doesn't re-ask the same question."""
        from agent.schemas.request import AgentRequest
        from agent.schemas.message import ChatMessage

        history = [
            ChatMessage(role="user", content="My landlord is not returning my deposit."),
            ChatMessage(
                role="assistant",
                content="To better understand your situation, Do you have a written rental agreement?",
            ),
        ]
        req = AgentRequest(
            query="Yes, I have a written rental agreement and I have already moved out.",
            conversation_history=history,
        )
        resp = invoke_agent(req)

        # Should not ask the same question again
        assert resp.needs_clarification is False or resp.clarification_question != "Do you have a written rental agreement?"
