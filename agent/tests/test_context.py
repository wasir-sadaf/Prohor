"""Tests for the context analysis node."""

from agent.nodes.context_analyzer import analyze_context
from agent.schemas.state import AgentState, Intent


class TestContextAnalyzer:
    def test_landlord_tenant_domain(self):
        state = AgentState(
            user_query="My landlord is not returning my deposit",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.legal_domain == "landlord-tenant"
        assert "landlord" in result.identified_entities
        assert "security deposit" in result.identified_entities

    def test_family_law_domain(self):
        state = AgentState(
            user_query="I want to divorce my husband",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.legal_domain == "family law"
        assert "divorce" in result.identified_entities

    def test_criminal_procedure_domain(self):
        state = AgentState(
            user_query="I want to file a complaint at the police station",
            intent="complaint_gd_drafting",
        )
        result = analyze_context(state)
        assert result.legal_domain == "criminal procedure"
        assert "police" in result.identified_entities

    def test_property_law_domain(self):
        state = AgentState(
            user_query="I have a property dispute about my land",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.legal_domain == "property law"
        assert "property" in result.identified_entities

    def test_employment_law_domain(self):
        state = AgentState(
            user_query="My employer terminated me without notice",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.legal_domain == "employment law"
        assert "employer" in result.identified_entities
        assert "termination" in result.identified_entities

    def test_general_legal_domain(self):
        state = AgentState(
            user_query="Tell me about bail",
            intent="general_legal_question",
        )
        result = analyze_context(state)
        assert result.legal_domain == "general legal"

    def test_out_of_scope_skips_analysis(self):
        state = AgentState(
            user_query="What's the weather?",
            intent="out_of_scope",
        )
        result = analyze_context(state)
        assert result.legal_domain is None
        assert result.identified_entities == []

    def test_landlord_clarification_triggered(self):
        """Clarification should be triggered for incomplete landlord-tenant scenarios."""
        state = AgentState(
            user_query="My landlord is not returning my deposit",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.needs_clarification is True
        assert result.clarification_question is not None
        assert result.awaiting_clarification is True

    def test_no_clarification_for_know_your_rights(self):
        """Know-your-rights queries don't need clarification."""
        state = AgentState(
            user_query="What are my fundamental rights?",
            intent="know_your_rights",
        )
        result = analyze_context(state)
        assert result.needs_clarification is False

    def test_no_clarification_for_find_legal_help(self):
        """Find-legal-help queries don't need clarification."""
        state = AgentState(
            user_query="I need free legal help",
            intent="find_legal_help",
        )
        result = analyze_context(state)
        assert result.needs_clarification is False

    def test_clarification_history_prevents_repeat(self):
        """Should not ask a question that was already asked."""
        state = AgentState(
            user_query="My landlord is not returning my deposit",
            intent="legal_scenario_guidance",
            clarification_history=["Do you have a written rental agreement?"],
        )
        result = analyze_context(state)
        # Should not ask the same question again
        if result.needs_clarification:
            assert result.clarification_question != "Do you have a written rental agreement?"

    def test_divorce_clarification_triggered(self):
        """Clarification for divorce queries."""
        state = AgentState(
            user_query="I want to divorce my husband",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.needs_clarification is True
        assert result.clarification_question is not None

    def test_legal_situation_summary(self):
        state = AgentState(
            user_query="My landlord is not returning my deposit",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.legal_situation is not None
        assert "landlord" in result.legal_situation

    def test_bangla_landlord_query(self):
        state = AgentState(
            user_query="বাড়িওয়ালা আমার জমা রাখা টাকা ফেরত দিচ্ছে না",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.legal_domain == "landlord-tenant"
        assert result.needs_clarification is True

    def test_awaiting_clarification_clears_flag(self):
        """When awaiting_clarification is True, the node clears it after processing."""
        state = AgentState(
            user_query="Yes I have a written agreement",
            intent="legal_scenario_guidance",
            awaiting_clarification=True,
        )
        result = analyze_context(state)
        # The flag should be cleared after processing
        assert result.awaiting_clarification is False

    def test_employment_termination_clarification(self):
        state = AgentState(
            user_query="I was terminated from my job without any reason",
            intent="legal_scenario_guidance",
        )
        result = analyze_context(state)
        assert result.needs_clarification is True
        assert result.clarification_question is not None
