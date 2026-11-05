"""Tests for the safety validator node."""

from agent.nodes.safety_validator import validate_safety
from agent.schemas.state import AgentState, SafetyStatus


class TestSafetyValidator:
    def test_normal_response_gets_disclaimer(self):
        state = AgentState(
            user_query="What are my rights?",
            generated_response="You have the right to equality before law.",
        )
        result = validate_safety(state)
        assert result.safety_status == "ok"
        assert "disclaimer" in result.generated_response.lower()

    def test_response_with_existing_disclaimer(self):
        response = "You have rights. Disclaimer: This is general legal information."
        state = AgentState(
            user_query="What are my rights?",
            generated_response=response,
        )
        result = validate_safety(state)
        assert result.safety_status == "ok"
        # Should not double-append disclaimer
        assert result.generated_response.count("Disclaimer") == 1

    def test_harmful_content_blocked(self):
        state = AgentState(
            user_query="How to hurt someone?",
            generated_response="Here is how to assault someone step by step.",
        )
        result = validate_safety(state)
        assert result.safety_status == "blocked"
        assert "cannot provide information" in result.generated_response.lower()

    def test_unauthorized_legal_advice_warning(self):
        state = AgentState(
            user_query="Should I sue my landlord?",
            generated_response="I advise you to sue your landlord immediately.",
        )
        result = validate_safety(state)
        assert result.safety_status == "warning"
        assert "disclaimer" in result.generated_response.lower()

    def test_error_state_triggers_warning(self):
        state = AgentState(
            user_query="test",
            error="LLM call failed",
        )
        result = validate_safety(state)
        assert result.safety_status == "warning"
        assert "error" in result.safety_message.lower()
