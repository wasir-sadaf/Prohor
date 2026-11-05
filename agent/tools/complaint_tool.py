"""
Complaint & GD Drafting tool.

Generates formal complaint or General Diary (GD) application drafts
in Bangla or English. The tool:
- Understands the incident described by the user
- Identifies missing factual information
- Organizes information chronologically
- Generates a formal draft with placeholders for missing info
- Allows revision requests

IMPORTANT:
- Never invent incident details or fabricate evidence
- Clearly distinguish user-provided facts from placeholders
- Never claim an application has been submitted
- Remind users to review the draft before using it
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field


class ComplaintDraftInput(BaseModel):
    """Input for the complaint/GD drafting workflow."""

    user_query: str = Field(description="User's description of the incident")
    legal_situation: Optional[str] = Field(default=None)
    identified_entities: list[str] = Field(default_factory=list)
    language: str = Field(default="en")
    conversation_history: list[dict] = Field(
        default_factory=list,
        description="Prior conversation for additional context",
    )
    draft_type: Optional[str] = Field(
        default=None,
        description="'gd', 'complaint', or 'fir'. If None, auto-detected.",
    )


class ComplaintDraftResult(BaseModel):
    """Structured output from the complaint/GD drafting workflow."""

    draft_text: str = Field(description="The generated formal draft")
    draft_type: str = Field(description="Type of draft: 'gd', 'complaint', or 'fir'")
    missing_info: list[str] = Field(
        default_factory=list,
        description="Factual information that is missing and marked as placeholders",
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether critical information is missing",
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question to ask if clarification is needed",
    )
    review_reminder: str = Field(
        description="Reminder for the user to review before using",
    )


# ── Factual info detection patterns ──────────────────────────────
_FACT_PATTERNS: list[tuple[str, list[str]]] = [
    ("date", [r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", r"\b(today|yesterday|এই কাল)\b"]),
    ("time", [r"\b(\d{1,2}:\d{2})\b", r"\b(morning|afternoon|evening|night|সকাল|বিকেল|রাত)\b"]),
    ("location", [r"\b(at|near|in|on|কাছে|পাশে|মধ্যে)\b\s+([A-Z][a-z]+)"]),
    ("person_name", [r"\b(Mr\.|Mrs\.|Ms\.|MD|মোঃ)\s+([A-Z][a-z]+)"]),
]

# ── Required fields for a GD/complaint ───────────────────────────
_REQUIRED_FIELDS = {
    "gd": ["complainant_name", "incident_date", "incident_description", "police_station"],
    "complaint": ["complainant_name", "respondent_name", "incident_date", "incident_description"],
    "fir": ["complainant_name", "incident_date", "incident_location", "incident_description", "police_station"],
}

# ── Placeholders ───────────────────────────────────────────────
_PLACEHOLDER_PREFIX = "[PLACEHOLDER: "
_PLACEHOLDER_SUFFIX = "]"

def _ph(field_name: str, lang: str = "en") -> str:
    """Generate a placeholder string."""
    if lang == "bn":
        field_bn = {
            "complainant_name": "অভিযোগকারীর নাম",
            "respondent_name": "প্রতিবাদীর নাম",
            "incident_date": "ঘটনার তারিখ",
            "incident_location": "ঘটনার স্থান",
            "incident_description": "ঘটনার বিবরণ",
            "police_station": "থানার নাম",
            "complainant_address": "অভিযোগকারীর ঠিকানা",
            "complainant_phone": "অভিযোগকারীর ফোন নম্বর",
            "witnesses": "সাক্ষীদের নাম",
        }
        label = field_bn.get(field_name, field_name)
    else:
        label = field_name.replace("_", " ").title()
    return f"{_PLACEHOLDER_PREFIX}{label}{_PLACEHOLDER_SUFFIX}"


def _detect_draft_type(query: str) -> str:
    """Auto-detect the draft type from the user's query."""
    lower = query.lower()
    if any(kw in lower for kw in ["fir", "first information report"]):
        return "fir"
    if any(kw in lower for kw in ["gd", "general diary", "জিডি"]):
        return "gd"
    if any(kw in lower for kw in ["complaint", "অভিযোগ", "অভিযোগপত্র"]):
        return "complaint"
    return "gd"  # Default to GD


def _extract_facts(query: str) -> dict:
    """Extract factual information from the user's query."""
    facts = {}
    lower = query.lower()

    # Date detection
    for pattern in _FACT_PATTERNS[0][1]:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            facts["incident_date"] = match.group(0)
            break

    # Time detection
    for pattern in _FACT_PATTERNS[1][1]:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            facts["incident_time"] = match.group(0)
            break

    # Location detection
    for pattern in _FACT_PATTERNS[2][1]:
        match = re.search(pattern, query)
        if match:
            facts["incident_location"] = match.group(0)
            break

    # Person name detection
    for pattern in _FACT_PATTERNS[3][1]:
        match = re.search(pattern, query)
        if match:
            facts["respondent_name"] = match.group(0)
            break

    # Description is the query itself (trimmed)
    facts["incident_description"] = query.strip()

    return facts


def _find_missing_fields(
    draft_type: str,
    facts: dict,
) -> list[str]:
    """Identify required fields that are missing from the facts."""
    required = _REQUIRED_FIELDS.get(draft_type, _REQUIRED_FIELDS["gd"])
    missing = []
    for field_name in required:
        if field_name not in facts:
            missing.append(field_name)
    return missing


def _build_gd_draft(
    facts: dict,
    missing_fields: list[str],
    lang: str,
) -> str:
    """Build a GD application draft."""
    if lang == "bn":
        lines = [
            "অভিযোগকারীর নাম: " + facts.get("complainant_name", _ph("complainant_name", "bn")),
            "অভিযোগকারীর ঠিকানা: " + _ph("complainant_address", "bn"),
            "অভিযোগকারীর ফোন নম্বর: " + _ph("complainant_phone", "bn"),
            "",
            "বিষয়: জিডি এন্ট্রি দাখিল।",
            "",
            "জনাব/জনাবা,",
            "",
            "এতদ্বারা অবগত করছি যে নিম্নলিখিত ঘটনাটি ঘটেছে:",
            "",
            "ঘটনার তারিখ: " + facts.get("incident_date", _ph("incident_date", "bn")),
            "ঘটনার সময়: " + facts.get("incident_time", _ph("incident_time", "bn")),
            "ঘটনার স্থান: " + facts.get("incident_location", _ph("incident_location", "bn")),
            "",
            "ঘটনার বিবরণ:",
            facts.get("incident_description", _ph("incident_description", "bn")),
            "",
            "উপর্যুক্ত ঘটনার জিডি এন্ট্রি দাখিলের জন্য অনুরোধ করছি।",
            "",
            "অনুগ্রহপূর্বক একটি জিডি রসিদ প্রদান করুন।",
            "",
            "বিনীয় নিবেদক,",
            facts.get("complainant_name", _ph("complainant_name", "bn")),
            "",
            "সেবায় এতদ্বারা অনুগ্রহ করে তারিখ: " + _ph("date", "bn"),
        ]
    else:
        lines = [
            "Complainant Name: " + facts.get("complainant_name", _ph("complainant_name")),
            "Complainant Address: " + _ph("complainant_address"),
            "Complainant Phone: " + _ph("complainant_phone"),
            "",
            "Subject: Application for General Diary (GD) Entry.",
            "",
            "To the Officer-in-Charge,",
            _ph("police_station") + " Police Station",
            "",
            "I hereby inform you that the following incident has occurred:",
            "",
            "Date of Incident: " + facts.get("incident_date", _ph("incident_date")),
            "Time of Incident: " + facts.get("incident_time", _ph("incident_time")),
            "Location of Incident: " + facts.get("incident_location", _ph("incident_location")),
            "",
            "Description of Incident:",
            facts.get("incident_description", _ph("incident_description")),
            "",
            "I request you to kindly register this as a General Diary entry.",
            "",
            "Please provide a GD receipt for my reference.",
            "",
            "Sincerely,",
            facts.get("complainant_name", _ph("complainant_name")),
            "",
            "Date: " + _ph("date"),
        ]
    return "\n".join(lines)


def _build_complaint_draft(
    facts: dict,
    missing_fields: list[str],
    lang: str,
) -> str:
    """Build a formal complaint draft."""
    if lang == "bn":
        lines = [
            "অভিযোগকারীর নাম: " + facts.get("complainant_name", _ph("complainant_name", "bn")),
            "প্রতিবাদীর নাম: " + facts.get("respondent_name", _ph("respondent_name", "bn")),
            "অভিযোগকারীর ঠিকানা: " + _ph("complainant_address", "bn"),
            "প্রতিবাদীর ঠিকানা: " + _ph("respondent_address", "bn"),
            "",
            "বিষয়: আনুষ্ঠানিক অভিযোগ দাখিল।",
            "",
            "জনাব/জনাবা,",
            "",
            "এতদ্বারা আনুষ্ঠানিকভাবে অভিযোগ করছি যে নিম্নলিখিত ঘটনাটি ঘটেছে:",
            "",
            "ঘটনার তারিখ: " + facts.get("incident_date", _ph("incident_date", "bn")),
            "ঘটনার স্থান: " + facts.get("incident_location", _ph("incident_location", "bn")),
            "",
            "অভিযোগের বিবরণ:",
            facts.get("incident_description", _ph("incident_description", "bn")),
            "",
            "সাক্ষীগণ: " + _ph("witnesses", "bn"),
            "",
            "উপর্যুক্ত অভিযোগের তদন্ত এবং বিচারের জন্য অনুরোধ করছি।",
            "",
            "বিনীয় নিবেদক,",
            facts.get("complainant_name", _ph("complainant_name", "bn")),
        ]
    else:
        lines = [
            "Complainant Name: " + facts.get("complainant_name", _ph("complainant_name")),
            "Respondent Name: " + facts.get("respondent_name", _ph("respondent_name")),
            "Complainant Address: " + _ph("complainant_address"),
            "Respondent Address: " + _ph("respondent_address"),
            "",
            "Subject: Formal Complaint.",
            "",
            "To the Relevant Authority,",
            "",
            "I hereby formally complain that the following incident has occurred:",
            "",
            "Date of Incident: " + facts.get("incident_date", _ph("incident_date")),
            "Location of Incident: " + facts.get("incident_location", _ph("incident_location")),
            "",
            "Description of Complaint:",
            facts.get("incident_description", _ph("incident_description")),
            "",
            "Witnesses: " + _ph("witnesses"),
            "",
            "I request a formal investigation and appropriate legal action.",
            "",
            "Sincerely,",
            facts.get("complainant_name", _ph("complainant_name")),
        ]
    return "\n".join(lines)


def generate_complaint_draft(
    input_data: ComplaintDraftInput,
) -> ComplaintDraftResult:
    """
    Generate a complaint or GD application draft.

    Parameters
    ----------
    input_data : ComplaintDraftInput
        User's incident description and context.

    Returns
    -------
    ComplaintDraftResult
        The draft, missing info, and review reminder.
    """
    # ── Determine draft type ─────────────────────────────────────
    draft_type = input_data.draft_type or _detect_draft_type(input_data.user_query)

    # ── Extract factual info from the query ──────────────────────
    facts = _extract_facts(input_data.user_query)

    # ── Check conversation history for additional facts ──────────
    for msg in input_data.conversation_history:
        content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
        extra_facts = _extract_facts(content)
        # Merge — don't overwrite existing facts
        for key, value in extra_facts.items():
            if key not in facts:
                facts[key] = value

    # ── Find missing fields ──────────────────────────────────────
    missing_fields = _find_missing_fields(draft_type, facts)

    # ── Build draft ──────────────────────────────────────────────
    if draft_type == "complaint":
        draft_text = _build_complaint_draft(facts, missing_fields, input_data.language)
    else:
        draft_text = _build_gd_draft(facts, missing_fields, input_data.language)

    # ── Determine if critical info is missing ────────────────────
    critical_fields = ["incident_description"]
    needs_clarification = any(f in missing_fields for f in critical_fields)
    clarification_question = None
    if needs_clarification:
        if input_data.language == "bn":
            clarification_question = "অনুগ্রহ করে ঘটনাটি বিস্তারিতভাবে বর্ণনা করুন।"
        else:
            clarification_question = "Please describe the incident in detail."

    # ── Build missing info list (human-readable) ─────────────────
    missing_info_str = [_ph(f, input_data.language) for f in missing_fields]

    # ── Build review reminder ────────────────────────────────────
    if input_data.language == "bn":
        review_reminder = (
            "গুরুত্বপূর্ণ: এটি একটি খসড়া। এটি ব্যবহারের আগে যাচাই করুন। "
            "PLACEHOLDER হিসেবে চিহ্নিত তথ্য পূরণ করুন। "
            "এই খসড়া জমা দেওয়া হয়নি এবং এটি একটি আইনি দলিল নয়।"
        )
    else:
        review_reminder = (
            "IMPORTANT: This is a draft. Please review it before use. "
            "Fill in all information marked as PLACEHOLDER. "
            "This draft has not been submitted and is not a legal document."
        )

    return ComplaintDraftResult(
        draft_text=draft_text,
        draft_type=draft_type,
        missing_info=missing_info_str,
        needs_clarification=needs_clarification,
        clarification_question=clarification_question,
        review_reminder=review_reminder,
    )
