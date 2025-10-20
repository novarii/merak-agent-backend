# Merak Hiring Agent Build Plan

## Reference Docs
- OpenAI Agents Python Quickstart — https://openai.github.io/openai-agents-python/quickstart
- Handoff primitives — https://openai.github.io/openai-agents-python/ref/handoffs
- Agent `Runner` orchestration — https://openai.github.io/openai-agents-python/quickstart#run-agent-orchestration
- Structured agent output — https://openai.github.io/openai-agents-python/ja/ref/agent_output
- FileSearchTool for vector stores — https://openai.github.io/openai-agents-python/ref/tool#filesearchtool

## Target User Flow
1. User asks Merak for an agent (e.g. “BI dashboard automation”).
2. Merak gathers missing filters (max rate, availability, skills, location).
3. Merak confirms a normalized brief.
4. Filter Standardizer agent converts the brief into a typed schema covering search facets.
5. Vector search tool retrieves matching agent profiles.
6. Merak summarizes the top matches and surfaces structured results to the user.

## Phase 1 — Foundations
- Add OpenAI Agents SDK as an integration (`app/integrations/openai_agents.py`) and expose helpers for creating `Agent`, `Runner`, and tracing configs (Quickstart ref).
- Create shared Pydantic schemas in `app/schemas/agent_filters.py` reflecting the clarifying questions (use `AgentOutputSchema` patterns for JSON validation).
- Stand up a ChatKit server wrapper (`app/integrations/chatkit_server.py`) extending `ChatKitServer` and wiring `Runner.run_streamed` via `stream_agent_response` to the orchestrator (ChatKit server ref).
- Expose a FastAPI route (e.g. `app/api/chatkit.py`) mirroring the ChatKit example that calls `server.process(...)` and streams SSE responses when the UI hits `/chatkit` (ChatKit FastAPI ref).

## Phase 2 — Orchestrator Agent (“Merak”)
- Define Merak in `agents/merak/orchestrator.py` using `Agent` class with instructions about interviewing users, asking clarifiers when filter fields are missing, and confirming final criteria (Quickstart ref).
- Implement clarifying-question loop via guardrailed tool or output schema so Merak knows which fields remain unknown.
- Prepare handoff metadata (`handoff_description`) so downstream agents understand Merak’s context (Handoff ref).

## Phase 3 — Filter Standardizer Agent
- Build a specialized agent in `agents/merak/filter_standardizer.py` that accepts Merak’s confirmed summary and emits `AgentFilterPayload` JSON (AgentOutputSchema ref for strict validation).
- Register a `Handoff` from Merak to the standardizer using `Handoff` dataclass with `on_invoke_handoff` callback; surface the handoff through the ChatKit stream so the UI sees progress events (Handoff ref, ChatKit stream ref).
- Ensure Merak waits for the structured response before continuing the conversation; leverage `Runner` orchestration to manage this round trip and persist `previous_response_id` in thread metadata for resumability (Runner orchestrator ref, ChatKit metadata ref).

## Phase 4 — Vector Store Search
- Implement `app/services/search.py` that wraps OpenAI File Search tool with project vector store IDs (FileSearchTool ref).
- Register a `file_search` tool with the Filter Standardizer or a dedicated Retrieval agent; configure ranking/filter parameters from standardized payload.
- Add transform logic to shape `file_search` results into domain-specific DTOs (`app/schemas/search_results.py`).

## Phase 5 — Response Assembly
- Extend Merak to interpret search results and craft user-facing summaries, including rate/availability/fit notes.
- Provide structured output (e.g. list of agents with match scores) alongside natural-language recommendations.
- Update FastAPI endpoint to stream Merak’s responses or return the final handoff output and summary.

## Phase 6 — Observability & Evaluation
- Enable session tracing with Agents SDK to visualize handoffs and tool calls (Quickstart tracing guidance).
- Add unit tests in `tests/agents/test_merak.py` covering question-asking logic and schema validation.
- Add integration tests for end-to-end search flow using mocked vector responses (`tests/integration/test_search_flow.py`).

## Phase 7 — Deployment Readiness
- Document required environment variables (OpenAI key, vector store IDs) in `.env.example` and validate via `app/core/settings.py`.
- Provide CLI or background tasks for ingesting agent profiles into the vector store (outside scope but noted).
- Create runbook in `docs/architecture.md` covering agent responsibilities, handoffs, and failure handling paths.
