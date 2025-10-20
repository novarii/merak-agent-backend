# Manual Testing SOP (Merak Backend)

## Purpose
Document the steps required to run the FastAPI backend, verify configuration, and simulate a ChatKit conversation so engineers can validate end-to-end behaviour without a UI.

## Prerequisites
- Python 3.11+ with virtualenv activated.
- Packages installed via `pip install -r requirements.txt` (make sure `openai`, `openai-agents`, `openai-chatkit`, and `httpx[sse]` are present).
- Access to an OpenAI vector store containing agent profiles.

## Environment Configuration
Create a dotenv file in `backend/` (e.g., `.env.local`) with:
```
OPENAI_API_KEY=sk-***
OPENAI_VECTOR_STORE_ID=vs_***
# Optional overrides
OPENAI_AGENT_MODEL=gpt-4o-mini
OPENAI_ORG=...
OPENAI_PROJECT=...
```

Load the variables before running the server:
```
set -a; source backend/.env.local; set +a
```

## Run the Backend
From `backend/`:
```
uvicorn app.main:app --reload
```

Verify the health endpoint:
```
curl http://127.0.0.1:8000/health
```

## Exercise the Chat Flow
Option A — **ChatKit CLI**
```
chatkit chat --api-base http://127.0.0.1:8000 --assistant merak-local
```
Respond to Merak’s clarifying questions until it triggers `search_agents`. Inspect streamed results for correctness.

Option B — **Python script (`backend/app/try_merak.py`)**
```
python backend/app/try_merak.py
```
The script issues a `ThreadsCreateReq` with a sample brief and prints streamed `ThreadStreamEvent` payloads.

## Validation Checklist
- Merak gathers all five filter facets before searching.
- Searcher tool call returns structured `SearchResults` (check for `matches`, `applied_filters`).
- Final assistant summary reflects the retrieved agents.
- No HTTP 503 errors (indicates environment misconfiguration).

## Related Docs
- `.agent/System/project_architecture.md` — architectural context for the workflow under test.
- `.agent/README.md` — documentation index.
