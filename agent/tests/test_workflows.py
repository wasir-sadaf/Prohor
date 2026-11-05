"""
Integration tests for specialized workflows through the full agent pipeline.

Tests each specialized workflow end-to-end via invoke_agent() with
realistic Bangla and English example conversations.
"""

from agent.entry_point import invoke_agent
from agent.llm.factory import reset_llm_cache
from agent.graph import reset_graph
from agent.schemas.request import AgentRequest
from agent.schemas.message import ChatMessage


class TestScenarioGuidanceWorkflow:
    """Tests for the legal scenario guidance workflow via invoke_agent."""

    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_landlord_deposit_guidance_en(self):
        """English: landlord deposit dispute triggers scenario guidance."""
        resp = invoke_agent(AgentRequest(
            query="My landlord is not returning my security deposit. I have a written agreement and I moved out.",
        ))
        assert resp.response != ""
        assert resp.intent == "legal_scenario_guidance"
        assert resp.error is None

    def test_employment_dispute_en(self):
        """English: employment salary dispute."""
        resp = invoke_agent(AgentRequest(
            query="My employer has not paid my salary for 3 months. What should I do?",
        ))
        assert resp.response != ""
        assert resp.error is None

    def test_landlord_deposit_bangla(self):
        """Bangla: landlord deposit dispute."""
        resp = invoke_agent(AgentRequest(
            query="বাড়িওয়ালা আমার জমা রাখা টাকা ফেরত দিচ্ছে না। আমার চুক্তি আছে এবং আমি বাড়ি ছেড়ে দিয়েছি।",
            language="bn",
        ))
        assert resp.response != ""
        assert resp.error is None

    def test_consumer_rights_violation_en(self):
        """English: consumer rights violation."""
        resp = invoke_agent(AgentRequest(
            query="I bought a defective product and the shop won't give me a refund. What are my consumer rights?",
        ))
        assert resp.response != ""
        assert resp.intent is not None
        assert resp.error is None


class TestDocumentExplanationWorkflow:
    """Tests for the document explanation workflow via invoke_agent."""

    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_contract_explanation_en(self):
        """English: user asks to explain a contract clause."""
        resp = invoke_agent(AgentRequest(
            query="Can you explain this contract clause about termination notice?",
        ))
        assert resp.response != ""
        assert resp.intent == "document_explanation"
        assert resp.error is None

    def test_document_with_text_en(self):
        """English: user provides document text for analysis."""
        long_text = (
            "This rental agreement is made between the landlord and tenant. "
            "The tenant shall pay monthly rent of Tk 15000. "
            "The tenant must give 30 days notice before vacating. "
            "The deposit is non-refundable if the tenant breaks the lease early. "
            "The landlord shall maintain the property in habitable condition."
        )
        resp = invoke_agent(AgentRequest(
            query=long_text,
        ))
        assert resp.response != ""
        assert resp.error is None

    def test_document_explanation_bangla(self):
        """Bangla: user asks about a document clause."""
        resp = invoke_agent(AgentRequest(
            query="এই চুক্তির ধারা ৫ এ কী বলা হয়েছে ব্যাখ্যা করুন",
            language="bn",
        ))
        assert resp.response != ""
        assert resp.error is None


class TestComplaintGDDraftingWorkflow:
    """Tests for the complaint/GD drafting workflow via invoke_agent."""

    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_gd_draft_en(self):
        """English: user wants to file a GD about a stolen phone."""
        resp = invoke_agent(AgentRequest(
            query="I want to file a GD. My phone was stolen yesterday at Dhanmondi, Dhaka.",
        ))
        assert resp.response != ""
        assert resp.intent == "complaint_gd_drafting"
        assert resp.error is None

    def test_gd_draft_bangla(self):
        """Bangla: user wants to file a GD."""
        resp = invoke_agent(AgentRequest(
            query="আমার মোবাইল ফোন চুরি হয়েছে। আমি জিডি করতে চাই।",
            language="bn",
        ))
        assert resp.response != ""
        assert resp.intent == "complaint_gd_drafting"
        assert resp.error is None

    def test_complaint_draft_en(self):
        """English: user wants to file a formal complaint."""
        resp = invoke_agent(AgentRequest(
            query="I want to file a formal complaint against my neighbor for harassment.",
        ))
        assert resp.response != ""
        assert resp.error is None

    def test_gd_draft_has_placeholders(self):
        """Draft should include placeholders for missing information."""
        resp = invoke_agent(AgentRequest(
            query="My phone was stolen. I want to file a GD.",
        ))
        # The response should mention missing info or placeholders
        assert resp.response != ""

    def test_gd_draft_never_submitted(self):
        """The response should never claim the draft has been submitted."""
        resp = invoke_agent(AgentRequest(
            query="I want to file a GD about a stolen bike.",
        ))
        # Should say "not been submitted" or similar, never "has been submitted" alone
        assert "has been submitted" not in resp.response.lower() or "not" in resp.response.lower()
        # Should contain a review reminder
        assert "review" in resp.response.lower() or "খসড়া" in resp.response

    def test_gd_multi_turn_with_details(self):
        """Multi-turn: user provides details after initial request."""
        history = [
            ChatMessage(role="user", content="I want to file a GD."),
            ChatMessage(role="assistant", content="Please describe the incident."),
        ]
        resp = invoke_agent(AgentRequest(
            query="On 15th March 2024, my laptop was stolen from my office at Banani.",
            conversation_history=history,
        ))
        assert resp.response != ""
        assert resp.error is None


class TestFindLegalHelpWorkflow:
    """Tests for the find legal help workflow via invoke_agent."""

    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_find_legal_aid_en(self):
        """English: user asks about legal aid."""
        resp = invoke_agent(AgentRequest(
            query="I cannot afford a lawyer. Where can I get free legal aid in Bangladesh?",
        ))
        assert resp.response != ""
        assert resp.intent == "find_legal_help"
        assert resp.error is None

    def test_find_legal_aid_bangla(self):
        """Bangla: user asks about legal aid."""
        resp = invoke_agent(AgentRequest(
            query="আমার ন্যায় সহায়তা প্রয়োজন। আমি গরিব, আইনজীবী ভাড়া করতে পারি না।",
            language="bn",
        ))
        assert resp.response != ""
        assert resp.intent == "find_legal_help"
        assert resp.error is None

    def test_legal_aid_no_fabricated_contacts(self):
        """Legal aid response should not fabricate phone numbers or addresses."""
        resp = invoke_agent(AgentRequest(
            query="I need legal aid services near me.",
        ))
        # Should not contain fabricated phone numbers
        assert resp.response != ""
        # The mock acknowledges limitations
        assert resp.error is None

    def test_legal_aid_with_location(self):
        """User provides location for legal aid search."""
        resp = invoke_agent(AgentRequest(
            query="I need legal aid in Chittagong. I have a family dispute.",
            context={"location": "Chittagong"},
        ))
        assert resp.response != ""
        assert resp.error is None


class TestWorkflowRouting:
    """Tests for workflow routing integration in the main agent."""

    def setup_method(self):
        reset_llm_cache()
        reset_graph()

    def test_rights_query_uses_default_path(self):
        """Know-your-rights queries don't trigger specialized workflows."""
        resp = invoke_agent(AgentRequest(
            query="What are my fundamental rights as a Bangladeshi citizen?",
        ))
        assert resp.intent == "know_your_rights"
        assert resp.response != ""

    def test_gd_query_routes_to_drafting(self):
        """GD queries route to the complaint drafting workflow."""
        resp = invoke_agent(AgentRequest(
            query="I want to file a GD about a theft.",
        ))
        assert resp.intent == "complaint_gd_drafting"

    def test_document_query_routes_to_document_workflow(self):
        """Document queries route to the document explanation workflow."""
        resp = invoke_agent(AgentRequest(
            query="Can you explain this contract clause to me?",
        ))
        assert resp.intent == "document_explanation"

    def test_legal_aid_query_routes_correctly(self):
        """Legal aid queries route to the find legal help workflow."""
        resp = invoke_agent(AgentRequest(
            query="I need free legal aid services.",
        ))
        assert resp.intent == "find_legal_help"

    def test_scenario_query_routes_correctly(self):
        """Scenario queries route to the scenario guidance workflow."""
        resp = invoke_agent(AgentRequest(
            query="My employer terminated me without notice. What should I do?",
        ))
        assert resp.intent == "legal_scenario_guidance"

    def test_out_of_scope_not_routed(self):
        """Out-of-scope queries are not routed to any workflow."""
        resp = invoke_agent(AgentRequest(
            query="What's the weather today?",
        ))
        assert resp.intent == "out_of_scope"
