"""Tests for the intent classifier node."""

from agent.nodes.intent_classifier import classify_intent
from agent.schemas.state import AgentState, Intent


class TestClassifyIntent:
    def test_know_your_rights(self):
        state = AgentState(user_query="What are my fundamental rights?")
        result = classify_intent(state)
        assert result.intent == "know_your_rights"
        assert "rag_retrieve" in result.selected_tools

    def test_complaint_gd_drafting(self):
        state = AgentState(user_query="How do I file a GD?")
        result = classify_intent(state)
        assert result.intent == "complaint_gd_drafting"
        assert "format_template" in result.selected_tools

    def test_legal_scenario_guidance(self):
        state = AgentState(user_query="What is the procedure for filing a case?")
        result = classify_intent(state)
        assert result.intent == "legal_scenario_guidance"
        assert "context_analysis" in result.selected_tools

    def test_document_explanation(self):
        state = AgentState(user_query="Explain this contract clause to me")
        result = classify_intent(state)
        assert result.intent == "document_explanation"

    def test_find_legal_help(self):
        state = AgentState(user_query="I need legal aid help")
        result = classify_intent(state)
        assert result.intent == "find_legal_help"

    def test_out_of_scope(self):
        state = AgentState(user_query="What's the weather today?")
        result = classify_intent(state)
        assert result.intent == "out_of_scope"
        assert result.selected_tools == []

    def test_general_legal_question_fallback(self):
        state = AgentState(user_query="Tell me about bail")
        result = classify_intent(state)
        assert result.intent == "general_legal_question"

    def test_bangla_keywords_rights(self):
        state = AgentState(user_query="আমার অধিকার কী কী?")
        result = classify_intent(state)
        assert result.intent == "know_your_rights"

    def test_bangla_keywords_gd(self):
        state = AgentState(user_query="আমি জিডি করতে চাই")
        result = classify_intent(state)
        assert result.intent == "complaint_gd_drafting"

    def test_bangla_keywords_legal_aid(self):
        state = AgentState(user_query="আমার ন্যায় সহায়তা দরকার")
        result = classify_intent(state)
        assert result.intent == "find_legal_help"

    def test_bangla_keywords_landlord(self):
        state = AgentState(user_query="বাড়িওয়ালা আমার জমা রাখা টাকা ফেরত দিচ্ছে না")
        result = classify_intent(state)
        assert result.intent == "legal_scenario_guidance"

    def test_awaiting_clarification_preserves_intent(self):
        """When awaiting clarification, the intent should be preserved."""
        state = AgentState(
            user_query="Yes I have a written agreement",
            intent="legal_scenario_guidance",
            awaiting_clarification=True,
        )
        result = classify_intent(state)
        # Should keep the previous intent, not reclassify
        assert result.intent == "legal_scenario_guidance"
