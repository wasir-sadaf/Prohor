"""
Specialized legal workflow tools for Prohor.

Each tool is a function with a typed input/output schema that can be
called by the workflow router. The tools produce structured outputs
that are merged into AgentState.
"""

from agent.tools.document_tool import explain_legal_document, DocumentAnalysisInput, DocumentAnalysisResult
from agent.tools.complaint_tool import generate_complaint_draft, ComplaintDraftInput, ComplaintDraftResult
from agent.tools.scenario_tool import search_legal_procedures, ScenarioGuidanceInput, ScenarioGuidanceResult
from agent.tools.legal_aid_tool import find_legal_aid, LegalAidInput, LegalAidResult

__all__ = [
    "explain_legal_document",
    "DocumentAnalysisInput",
    "DocumentAnalysisResult",
    "generate_complaint_draft",
    "ComplaintDraftInput",
    "ComplaintDraftResult",
    "search_legal_procedures",
    "ScenarioGuidanceInput",
    "ScenarioGuidanceResult",
    "find_legal_aid",
    "LegalAidInput",
    "LegalAidResult",
]
