"""Tests for the specialized legal workflow tools."""

from agent.rag.mock import MockRAGClient
from agent.tools.scenario_tool import (
    search_legal_procedures,
    ScenarioGuidanceInput,
    ScenarioGuidanceResult,
)
from agent.tools.document_tool import (
    explain_legal_document,
    DocumentAnalysisInput,
    DocumentAnalysisResult,
    DocumentClause,
)
from agent.tools.complaint_tool import (
    generate_complaint_draft,
    ComplaintDraftInput,
    ComplaintDraftResult,
)
from agent.tools.legal_aid_tool import (
    find_legal_aid,
    LegalAidInput,
    LegalAidResult,
    MockLegalAidProvider,
)


class TestScenarioGuidanceTool:
    def setup_method(self):
        self.rag_client = MockRAGClient()

    def test_landlord_tenant_guidance(self):
        input_data = ScenarioGuidanceInput(
            user_query="My landlord is not returning my deposit",
            legal_domain="landlord-tenant",
            identified_entities=["landlord", "security deposit"],
            language="en",
        )
        result = search_legal_procedures(input_data, self.rag_client)
        assert isinstance(result, ScenarioGuidanceResult)
        assert result.legal_domain == "landlord-tenant"
        assert len(result.next_steps) > 0
        assert "Keep copies" in result.next_steps[0] or "rental agreement" in result.next_steps[0].lower()

    def test_employment_guidance(self):
        input_data = ScenarioGuidanceInput(
            user_query="I was terminated without notice",
            legal_domain="employment law",
            identified_entities=["employer", "termination"],
            language="en",
        )
        result = search_legal_procedures(input_data, self.rag_client)
        assert result.legal_domain == "employment law"
        assert len(result.next_steps) > 0
        assert any("employment" in step.lower() or "labour" in step.lower() for step in result.next_steps)

    def test_bangla_guidance(self):
        input_data = ScenarioGuidanceInput(
            user_query="বাড়িওয়ালা আমার টাকা ফেরত দিচ্ছে না",
            legal_domain="landlord-tenant",
            language="bn",
        )
        result = search_legal_procedures(input_data, self.rag_client)
        assert result.legal_domain == "landlord-tenant"
        assert "বাংলা" in result.guidance_text or "আপনার" in result.guidance_text
        assert len(result.next_steps) > 0

    def test_evidence_retrieved(self):
        input_data = ScenarioGuidanceInput(
            user_query="What are my rights as a consumer?",
            legal_domain="consumer protection",
            language="en",
        )
        result = search_legal_procedures(input_data, self.rag_client)
        # Mock RAG should return at least one result
        assert len(result.evidence) > 0

    def test_limitations_included(self):
        input_data = ScenarioGuidanceInput(
            user_query="My employer fired me",
            legal_domain="employment law",
            language="en",
        )
        result = search_legal_procedures(input_data, self.rag_client)
        assert result.limitations is not None
        assert "consult" in result.limitations.lower() or "lawyer" in result.limitations.lower()

    def test_consumer_protection_next_steps(self):
        input_data = ScenarioGuidanceInput(
            user_query="I bought a defective product",
            legal_domain="consumer protection",
            language="en",
        )
        result = search_legal_procedures(input_data, self.rag_client)
        assert any("receipt" in step.lower() or "complaint" in step.lower() for step in result.next_steps)


class TestDocumentExplanationTool:
    def setup_method(self):
        self.rag_client = MockRAGClient()

    def test_rental_agreement_identified(self):
        text = "This rental agreement is between landlord and tenant. The tenant shall pay rent monthly."
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert result.document_type == "rental agreement"
        assert len(result.clauses) > 0

    def test_obligation_extraction(self):
        text = (
            "The tenant shall pay rent on the 1st of each month. "
            "The landlord must maintain the property in good condition. "
            "Section 3. The tenant is responsible for utility bills."
        )
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert len(result.obligations) > 0
        assert any("shall pay" in ob or "must maintain" in ob for ob in result.obligations)

    def test_deadline_extraction(self):
        text = (
            "The tenant must give 30 days notice within the notice period. "
            "The deposit shall be returned within 7 days of vacating."
        )
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert len(result.deadlines) > 0
        assert any("days" in dl.lower() or "within" in dl.lower() for dl in result.deadlines)

    def test_warning_extraction(self):
        text = (
            "The deposit is non-refundable under any circumstances. "
            "The landlord may terminate at sole discretion without notice."
        )
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert len(result.warnings) > 0

    def test_summary_built(self):
        text = "This is a rental agreement. The tenant shall pay rent."
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert "rental agreement" in result.summary.lower()

    def test_limitations_included(self):
        text = "Simple contract text."
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert result.limitations is not None
        assert "not" in result.limitations.lower() and "legal advice" in result.limitations.lower()

    def test_bangla_document(self):
        text = "এই চুক্তির অধীনে ভাড়াটিয়া প্রতি মাসে ভাড়া প্রদান করতে বাধ্য।"
        input_data = DocumentAnalysisInput(document_text=text, language="bn")
        result = explain_legal_document(input_data, self.rag_client)
        assert result.limitations is not None

    def test_with_user_question(self):
        text = "This employment contract states the employee shall work 40 hours per week."
        input_data = DocumentAnalysisInput(
            document_text=text,
            user_question="What are my working hours?",
            language="en",
        )
        result = explain_legal_document(input_data, self.rag_client)
        assert "Your question" in result.summary or "your question" in result.summary.lower()

    def test_empty_document(self):
        input_data = DocumentAnalysisInput(document_text="", language="en")
        result = explain_legal_document(input_data, self.rag_client)
        assert result.document_type is None
        assert result.clauses == []

    def test_clause_categories(self):
        text = (
            "The tenant shall pay rent monthly (obligation). "
            "Rent must be paid within 5 days of due date (deadline). "
            "Deposit is non-refundable (warning)."
        )
        input_data = DocumentAnalysisInput(document_text=text, language="en")
        result = explain_legal_document(input_data, self.rag_client)
        categories = {c.category for c in result.clauses}
        # Should have at least one of each category
        assert "obligation" in categories or "deadline" in categories


class TestComplaintDraftingTool:
    def test_gd_draft_english(self):
        input_data = ComplaintDraftInput(
            user_query="On 15th January 2024, my phone was stolen at Dhanmondi. I want to file a GD.",
            language="en",
        )
        result = generate_complaint_draft(input_data)
        assert result.draft_type == "gd"
        assert "General Diary" in result.draft_text
        assert "PLACEHOLDER" in result.draft_text  # Missing fields are placeholders
        assert "review" in result.review_reminder.lower()

    def test_gd_draft_bangla(self):
        input_data = ComplaintDraftInput(
            user_query="১৫ জানুয়ারি ২০২৪ তারিখে আমার ফোন চুরি হয়েছে। আমি জিডি করতে চাই।",
            language="bn",
        )
        result = generate_complaint_draft(input_data)
        assert result.draft_type == "gd"
        assert "জিডি" in result.draft_text
        assert result.review_reminder != ""

    def test_complaint_draft(self):
        input_data = ComplaintDraftInput(
            user_query="My neighbor Mr. Rahman is harassing me. I want to file a formal complaint.",
            language="en",
            draft_type="complaint",
        )
        result = generate_complaint_draft(input_data)
        assert result.draft_type == "complaint"
        assert "Complaint" in result.draft_text or "complaint" in result.draft_text.lower()

    def test_missing_info_identified(self):
        input_data = ComplaintDraftInput(
            user_query="My phone was stolen",
            language="en",
        )
        result = generate_complaint_draft(input_data)
        assert len(result.missing_info) > 0
        assert "PLACEHOLDER" in " ".join(result.missing_info)

    def test_never_claims_submitted(self):
        input_data = ComplaintDraftInput(
            user_query="I was robbed yesterday",
            language="en",
        )
        result = generate_complaint_draft(input_data)
        assert "submitted" not in result.draft_text.lower()
        assert "not" in result.review_reminder.lower()

    def test_fir_draft(self):
        input_data = ComplaintDraftInput(
            user_query="I want to file an FIR about a theft at my shop",
            language="en",
        )
        result = generate_complaint_draft(input_data)
        assert result.draft_type == "fir"

    def test_date_extracted(self):
        input_data = ComplaintDraftInput(
            user_query="On 15/01/2024 my bike was stolen",
            language="en",
        )
        result = generate_complaint_draft(input_data)
        # Date should appear in the draft (either as fact or placeholder)
        assert "15/01/2024" in result.draft_text or "incident_date" in result.draft_text.lower()

    def test_facts_from_history(self):
        input_data = ComplaintDraftInput(
            user_query="I want to file a GD about the incident",
            language="en",
            conversation_history=[
                {"role": "user", "content": "My phone was stolen on 20th December at Gulshan"},
                {"role": "assistant", "content": "I can help you draft a GD application."},
            ],
        )
        result = generate_complaint_draft(input_data)
        # Should extract date from conversation history
        assert "20th December" in result.draft_text or "Gulshan" in result.draft_text

    def test_review_reminder_bangla(self):
        input_data = ComplaintDraftInput(
            user_query="আমার মোবাইল চুরি হয়েছে, জিডি করতে চাই",
            language="bn",
        )
        result = generate_complaint_draft(input_data)
        assert "খসড়া" in result.review_reminder or "যাচাই" in result.review_reminder


class TestFindLegalAidTool:
    def setup_method(self):
        self.rag_client = MockRAGClient()

    def test_returns_evidence(self):
        input_data = LegalAidInput(
            legal_issue="I need legal aid for a family dispute",
            language="en",
        )
        result = find_legal_aid(input_data, self.rag_client)
        assert len(result.evidence) > 0
        assert any("Legal Aid" in ev.law_or_regulation or "legal aid" in ev.law_or_regulation.lower() for ev in result.evidence)

    def test_guidance_text_generated(self):
        input_data = LegalAidInput(
            legal_issue="I cannot afford a lawyer",
            language="en",
        )
        result = find_legal_aid(input_data, self.rag_client)
        assert result.guidance_text != ""
        assert "legal aid" in result.guidance_text.lower()

    def test_bangla_guidance(self):
        input_data = LegalAidInput(
            legal_issue="আমার আইনি সহায়তা প্রয়োজন",
            language="bn",
        )
        result = find_legal_aid(input_data, self.rag_client)
        assert result.guidance_text != ""
        assert "আইনি সহায়তা" in result.guidance_text

    def test_no_fabricated_providers(self):
        """Mock provider should not fabricate contact info."""
        input_data = LegalAidInput(
            legal_issue="I need free legal help",
            language="en",
        )
        result = find_legal_aid(input_data, self.rag_client)
        # Mock provider returns empty list — no fabricated names/numbers
        assert len(result.providers) == 0

    def test_limitations_when_no_providers(self):
        input_data = LegalAidInput(
            legal_issue="I need a lawyer",
            language="en",
        )
        result = find_legal_aid(input_data, self.rag_client)
        assert result.limitations is not None
        assert "verified" in result.limitations.lower() or "not" in result.limitations.lower()

    def test_with_location(self):
        input_data = LegalAidInput(
            legal_issue="I need legal aid",
            location="Dhaka",
            language="en",
        )
        result = find_legal_aid(input_data, self.rag_client)
        assert result.guidance_text != ""

    def test_citations_populated(self):
        input_data = LegalAidInput(
            legal_issue="free legal aid",
            language="en",
        )
        result = find_legal_aid(input_data, self.rag_client)
        if result.evidence:
            assert len(result.citations) > 0

    def test_mock_provider_is_available(self):
        provider = MockLegalAidProvider()
        assert provider.is_available is True

    def test_mock_provider_returns_empty(self):
        provider = MockLegalAidProvider()
        results = provider.search_providers("family law", "Dhaka", "en")
        assert results == []
