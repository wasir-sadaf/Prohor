"""Tests for the agent's typed schemas."""

from agent.schemas.evidence import LegalEvidence
from agent.schemas.message import ChatMessage
from agent.schemas.request import AgentRequest
from agent.schemas.response import AgentResponse
from agent.schemas.state import AgentState, Intent, Language, SafetyStatus


class TestAgentState:
    def test_default_state(self):
        state = AgentState(user_query="Test query")
        assert state.user_query == "Test query"
        assert state.intent is None
        assert state.language == "en"
        assert state.evidence == []
        assert state.safety_status == "ok"
        assert state.reasoning_status == "pending"
        assert state.legal_domain is None
        assert state.identified_entities == []
        assert state.missing_info == []
        assert state.clarification_history == []
        assert state.awaiting_clarification is False
        assert state.is_followup is False

    def test_state_with_all_fields(self):
        state = AgentState(
            user_query="How do I file a GD?",
            language=Language.BANGLA,
            intent=Intent.COMPLAINT_GD_DRAFTING,
            reasoning_status="complete",
            generated_response="Here is how...",
            safety_status=SafetyStatus.OK,
        )
        assert state.user_query == "How do I file a GD?"
        assert state.language == "bn"
        assert state.intent == "complaint_gd_drafting"
        assert state.reasoning_status == "complete"
        assert state.safety_status == "ok"

    def test_state_accepts_enum_values_as_strings(self):
        state = AgentState(user_query="hi")
        state.intent = Intent.KNOW_YOUR_RIGHTS
        assert state.intent == "know_your_rights"

    def test_state_new_fields(self):
        state = AgentState(
            user_query="My landlord won't return my deposit",
            legal_domain="landlord-tenant",
            legal_situation="User is seeking guidance on a landlord tenant matter involving landlord.",
            identified_entities=["landlord", "security deposit"],
            missing_info=["Do you have a written rental agreement?"],
            clarification_history=["Do you have a written rental agreement?"],
            session_id="session-123",
            is_followup=True,
        )
        assert state.legal_domain == "landlord-tenant"
        assert state.identified_entities == ["landlord", "security deposit"]
        assert len(state.missing_info) == 1
        assert state.clarification_history[0] == "Do you have a written rental agreement?"
        assert state.session_id == "session-123"
        assert state.is_followup is True


class TestAgentRequest:
    def test_minimal_request(self):
        req = AgentRequest(query="What are my rights?")
        assert req.query == "What are my rights?"
        assert req.language == "en"
        assert req.conversation_history == []
        assert req.user_id is None

    def test_request_with_history(self):
        history = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there"),
        ]
        req = AgentRequest(
            query="Tell me about GD",
            language="bn",
            conversation_history=history,
            user_id="user-123",
        )
        assert req.language == "bn"
        assert len(req.conversation_history) == 2
        assert req.user_id == "user-123"


class TestAgentResponse:
    def test_default_response(self):
        resp = AgentResponse(response="Test answer")
        assert resp.response == "Test answer"
        assert resp.citations == []
        assert resp.evidence == []
        assert resp.safety_status == "ok"
        assert resp.error is None

    def test_response_with_evidence(self):
        evidence = LegalEvidence(
            source_title="Constitution",
            law_or_regulation="Constitution of Bangladesh",
            section_or_provision="Article 27",
            retrieved_content="All citizens are equal before law.",
        )
        resp = AgentResponse(
            response="You have the right to equality.",
            citations=[evidence.format_citation()],
            evidence=[evidence],
        )
        assert len(resp.evidence) == 1
        assert "Constitution of Bangladesh" in resp.citations[0]


class TestLegalEvidence:
    def test_format_citation_full(self):
        ev = LegalEvidence(
            source_title="Penal Code",
            law_or_regulation="Penal Code, 1860",
            section_or_provision="Section 302",
            retrieved_content="Punishment for murder.",
            source_url="https://example.com/penal-code",
            issuing_authority="Parliament",
            effective_date="1860-01-01",
        )
        citation = ev.format_citation()
        assert "Penal Code, 1860" in citation
        assert "§ Section 302" in citation
        assert "Parliament" in citation
        assert "https://example.com/penal-code" in citation

    def test_format_citation_minimal(self):
        ev = LegalEvidence(
            source_title="Some Law",
            law_or_regulation="Some Act",
            retrieved_content="Some content.",
        )
        citation = ev.format_citation()
        assert citation == "Some Act"
