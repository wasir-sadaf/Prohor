# Prohor Agent — AI Legal Literacy Assistant

Python agentic AI component for Prohor (প্রহর), helping Bangladeshi citizens understand their legal rights, procedures, documents, and legal aid services.

## Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│ classify_intent  │  → 7 intent categories (Bangla + English)
└────────┬────────┘
         │
    [out_of_scope?] ──yes──► generate_response (redirect) ──► END
         │no
         ▼
┌─────────────────┐
│ analyze_context  │  → legal domain, entities, clarification
└────────┬────────┘
         │
   [needs_clarification?] ──yes──► generate_response (ask question) ──► END
         │no
         ▼
┌──────────────────┐
│ retrieve_evidence │  → RAG client (mock or backend)
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ run_specialized_work │  → scenario guidance / document / complaint / legal aid
└────────┬─────────────┘
         │
         ▼
┌─────────────────┐
│ generate_response │  → LLM call or structured workflow output
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ validate_safety   │  → citation verification, injection check, disclaimer
└────────┬────────┘
         │
         ▼
       END
```

### Specialized Workflows

| Intent | Workflow Tool | Purpose |
|--------|---------------|---------|
| `legal_scenario_guidance` | `search_legal_procedures()` | Step-by-step legal guidance for common situations |
| `document_explanation` | `explain_legal_document()` | Document analysis with clause extraction |
| `complaint_gd_drafting` | `generate_complaint_draft()` | GD/complaint draft generation with placeholders |
| `find_legal_help` | `find_legal_aid()` | Legal aid service discovery |
| `know_your_rights` | (passthrough) | Uses RAG evidence directly |
| `general_legal_question` | (passthrough) | Uses RAG evidence + LLM |

### Safety Mechanisms

- **Disclaimer**: Every response includes a "general information, not legal advice" disclaimer
- **Citation verification**: Only citations backed by retrieved evidence are kept
- **Prompt injection protection**: User input and documents are sanitized; system tags, injection patterns, and role markers are filtered
- **Harmful content blocking**: Responses containing harmful instructions are blocked
- **Legal advice detection**: Unauthorized legal advice language triggers a warning

## Environment Variables

```bash
# LLM Provider (mock, openai, google)
LLM_PROVIDER=mock

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# Google Gemini
GOOGLE_API_KEY=
GOOGLE_MODEL=gemini-1.5-flash

# Generation
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
LLM_TIMEOUT=30

# Backend RAG Integration (leave unset to use mock)
# PROHOR_BACKEND_URL=http://localhost:5000
# PROHOR_BACKEND_TOKEN=your_jwt_token
```

## Installation

```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Running Tests

```bash
cd agent
PYTHONPATH=. .venv/bin/python -m pytest tests/ -v
```

## Usage

### Python (for backend integration)

```python
from agent import invoke_agent, AgentRequest

# Basic query
response = invoke_agent(AgentRequest(
    query="How do I file a GD?",
))
print(response.response)
print(response.citations)
print(response.evidence)

# With conversation history and session ID
response = invoke_agent(AgentRequest(
    query="My landlord won't return my deposit",
    session_id="conversation-uuid-from-backend",
    conversation_history=[
        ChatMessage(role="user", content="Hi"),
        ChatMessage(role="assistant", content="How can I help?"),
    ],
    language="bn",
))

# With document text
response = invoke_agent(AgentRequest(
    query="Explain this contract clause",
    context={"document_text": "The tenant shall pay rent monthly..."},
))
```

### Backend Integration Contract

The Node.js backend calls `invoke_agent()` through a subprocess or HTTP bridge. The flow:

```
Frontend → POST /api/chat → Backend authenticates → Retrieves history
  → Calls invoke_agent(AgentRequest) → Gets AgentResponse
  → Saves user message → Saves assistant message
  → Saves message_sources (using citation_entries) → Returns to frontend
```

**Request → AgentRequest mapping:**

```javascript
const agentRequest = {
    query: userMessage,
    language: "en",              // or "bn"
    session_id: conversationId,  // from conversations.id
    conversation_history: messages.map(m => ({
        role: m.role,
        content: m.content,
    })),
    user_id: userId,
    context: documentText ? { document_text: documentText } : null,
};
```

**AgentResponse → Backend storage mapping:**

```javascript
// response.evidence contains LegalEvidence objects with:
//   source_id  → legal_sources.id (for message_sources)
//   chunk_id   → legal_chunks.id (for message_sources)
//   is_verified → legal_sources.is_verified

// response.citation_entries contains structured citations:
//   { citation_text, source_id, chunk_id, is_verified }

// Save message_sources for each citation_entry:
for (const entry of response.citation_entries) {
    if (entry.chunk_id) {
        await db.from("message_sources").insert({
            message_id: assistantMessageId,
            chunk_id: entry.chunk_id,
        });
    }
}
```

## Real RAG Integration

The agent supports two RAG modes:

1. **Mock RAG** (default): Returns canned legal data for local development. No backend required.

2. **Backend RAG**: Connects to the Prohor Node.js backend legal search API.
   - Set `PROHOR_BACKEND_URL` to the backend URL (e.g., `http://localhost:5000`)
   - Set `PROHOR_BACKEND_TOKEN` to a valid JWT for authenticated endpoints
   - Calls `GET /api/legal/search?q=...` to retrieve legal chunks
   - Calls `GET /api/legal/sources/:id` to fetch source metadata
   - Maps responses to `LegalEvidence` with `source_id` and `chunk_id`

**Note**: The backend `/api/legal/search` endpoint requires authentication (`authMiddleware`). The backend team must provide a service token or the endpoint must be adjusted to allow internal service-to-service calls.

## Directory Structure

```
agent/
├── __init__.py              # Public API
├── entry_point.py           # invoke_agent() — backend entry point
├── graph.py                 # LangGraph orchestration
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   └── settings.py           # LLM configuration from env vars
│
├── llm/
│   ├── base.py               # LLMClient protocol
│   ├── factory.py            # Provider selection
│   ├── mock.py               # Mock LLM for development
│   ├── openai_client.py      # OpenAI backend
│   └── google_client.py      # Google Gemini backend
│
├── schemas/
│   ├── state.py              # AgentState (flows through graph)
│   ├── request.py            # AgentRequest (backend → agent)
│   ├── response.py           # AgentResponse (agent → backend)
│   ├── evidence.py           # LegalEvidence (with source_id, chunk_id)
│   └── message.py            # ChatMessage
│
├── nodes/
│   ├── intent_classifier.py  # 7 intent categories
│   ├── context_analyzer.py   # Domain detection, clarification
│   ├── rag_retriever.py      # RAG retrieval (mock or backend)
│   ├── workflow_router.py    # Dispatch to specialized tools
│   ├── response_generator.py # LLM call + structured output
│   └── safety_validator.py   # Citation verification, injection protection
│
├── tools/
│   ├── scenario_tool.py      # Legal scenario guidance
│   ├── document_tool.py      # Document explanation
│   ├── complaint_tool.py     # Complaint/GD drafting
│   └── legal_aid_tool.py     # Legal aid discovery
│
├── rag/
│   ├── interface.py          # RAGClient protocol, RAGQuery, RAGResult
│   ├── mock.py               # Mock RAG client
│   └── backend_client.py    # Real backend RAG adapter
│
└── tests/
    ├── conftest.py
    ├── test_agent.py         # Integration tests
    ├── test_context.py       # Context analysis tests
    ├── test_conversation.py  # Conversation memory tests
    ├── test_intent.py        # Intent classification tests
    ├── test_phase4.py        # Safety, citation, injection, error tests
    ├── test_rag.py            # RAG interface tests
    ├── test_safety.py        # Safety validator tests
    ├── test_schemas.py       # Schema tests
    ├── test_sample_conversations.py # Sample conversations
    ├── test_tools.py         # Specialized tool tests
    └── test_workflows.py     # Workflow integration tests
```

## Remaining Requirements for Backend Team

1. **Node.js → Python bridge**: The backend team needs to implement the communication layer that calls `invoke_agent()`. Options: subprocess spawn with JSON stdin/stdout, or a thin Python HTTP wrapper.

2. **Service token for RAG**: The `/api/legal/search` endpoint requires authentication. Either:
   - Create a service-level JWT that bypasses user-specific RLS
   - Add an internal API key header for service-to-service calls
   - Create a separate unauthenticated internal search endpoint

3. **message_sources saving**: After saving the assistant message, iterate over `response.citation_entries` and insert rows into `message_sources` with the `message_id` and `chunk_id` from each entry.

4. **Legal search enhancement**: The current `/api/legal/search` uses `ilike` (case-insensitive LIKE) which is basic text matching. For better retrieval quality, consider adding full-text search (PostgreSQL `tsvector`) or vector similarity search in the future.

5. **legal_chunks metadata**: The `metadata` column in `legal_chunks` may contain structured data (section numbers, article references). The backend RAG adapter currently doesn't parse this — the backend team could enhance the search endpoint to return parsed metadata alongside the content.
