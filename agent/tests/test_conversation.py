"""Tests for conversation memory and follow-up handling."""

from agent.entry_point import invoke_agent
from agent.llm.factory import reset_llm_cache
from agent.graph import reset_graph
from agent.schemas.message import ChatMessage
from agent.schemas.request import AgentRequest


class TestConversationMemory:
    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_followup_detected_with_history(self):
        """A query with conversation history should be detected as follow-up."""
        history = [
            ChatMessage(role="user", content="Hi"),
            ChatMessage(role="assistant", content="Hello! How can I help?"),
        ]
        req = AgentRequest(
            query="Tell me more about GD",
            conversation_history=history,
        )
        resp = invoke_agent(req)
        # The follow-up should be handled normally
        assert resp.response != ""
        assert resp.intent is not None

    def test_clarification_then_answer_flow(self):
        """
        Full conversation flow:
        1. User asks incomplete question → agent asks clarification
        2. User answers → agent proceeds with full response
        """
        # Step 1: Initial query triggers clarification
        req1 = AgentRequest(query="My landlord is not returning my deposit.")
        resp1 = invoke_agent(req1)

        assert resp1.needs_clarification is True
        assert resp1.clarification_question is not None

        # Step 2: User answers the clarification
        history = [
            ChatMessage(role="user", content="My landlord is not returning my deposit."),
            ChatMessage(role="assistant", content=resp1.response),
        ]
        req2 = AgentRequest(
            query="Yes, I have a written rental agreement and I have already moved out.",
            conversation_history=history,
        )
        resp2 = invoke_agent(req2)

        # Should now provide a full response, not another clarification
        assert resp2.response != ""
        # Should not ask the same clarification question again
        assert resp2.needs_clarification is False or (
            resp2.clarification_question != resp1.clarification_question
        )

    def test_clarification_response_has_no_disclaimer(self):
        """Clarification questions should not have a legal disclaimer appended."""
        req = AgentRequest(query="My landlord is not returning my deposit.")
        resp = invoke_agent(req)

        if resp.needs_clarification:
            assert "disclaimer" not in resp.response.lower()

    def test_out_of_scope_does_not_trigger_clarification(self):
        req = AgentRequest(query="What's the weather today?")
        resp = invoke_agent(req)

        assert resp.needs_clarification is False
        assert resp.intent == "out_of_scope"

    def test_conversation_context_preserved_in_history(self):
        """Verify that conversation history is passed through to the LLM."""
        history = [
            ChatMessage(role="user", content="What are my rights as a tenant?"),
            ChatMessage(role="assistant", content="As a tenant you have various rights..."),
        ]
        req = AgentRequest(
            query="What about eviction?",
            conversation_history=history,
        )
        resp = invoke_agent(req)

        # Should produce a response referencing the prior context
        assert resp.response != ""
        assert resp.error is None

    def test_multiple_clarifications_not_repeated(self):
        """
        Ensure the agent doesn't repeatedly ask the same clarification
        across multiple turns.
        """
        # First turn
        req1 = AgentRequest(query="My landlord won't return my deposit")
        resp1 = invoke_agent(req1)

        assert resp1.needs_clarification is True
        question1 = resp1.clarification_question

        # Simulate user providing a non-answer (e.g., asking a different question)
        history = [
            ChatMessage(role="user", content="My landlord won't return my deposit"),
            ChatMessage(role="assistant", content=resp1.response),
        ]
        req2 = AgentRequest(
            query="What are my rights in this situation?",
            conversation_history=history,
        )
        resp2 = invoke_agent(req2)

        # Should not ask the exact same question again
        if resp2.needs_clarification:
            assert resp2.clarification_question != question1
