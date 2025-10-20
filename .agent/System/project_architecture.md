# Merak Agent System Architecture

## Product Overview
Merak connects hiring managers with AI agents that can execute domain-specific tasks. A FastAPI backend orchestrates OpenAI Agent workflows, gathers user intent, standardises filters, and runs semantic retrieval against an OpenAI vector store. The platform streams results through ChatKit so clients can interact with Merak in real time.

## Repository Layout
- `backend/` — FastAPI service and agent orchestration code.
  - `app/main.py` exposes the ASGI app.
  - `app/api/` contains REST/SSE routes (`chatkit.py`, `health.py`).
  - `app/agents/` defines Merak (orchestrator) and the Searcher specialist.
  - `app/integrations/` wires ChatKit and the OpenAI Agents SDK.
  - `app/schemas/` stores shared Pydantic models (filters, search results).
  - `app/services/` holds supporting services (search tool builder, thread store).
  - `app/core/settings.py` centralises environment-backed configuration.
- `docs/` — reference snippets lifted from the OpenAI documentation.
- `MERAK_AGENT_PLAN.md` — phased implementation blueprint for upcoming features.
- `frontend/` — placeholder for the future UI (currently empty scaffold).

## Technology Stack
- **Backend framework:** FastAPI (Python 3.11+).
- **Agent runtime:** OpenAI Agents Python SDK.
- **Streaming UI:** OpenAI ChatKit (via `openai-chatkit`).
- **Semantic retrieval:** OpenAI vector store + hosted FileSearch tool.
- **Serialization:** Pydantic v2 (used both standalone and through `AgentOutputSchema`).
- **Thread persistence:** In-memory `ThreadStore` (development only).

## Core Components
### Environment Settings (`app/core/settings.py`)
Required variables:
| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Authenticates both the Agents SDK and vector store access. |
| `OPENAI_AGENT_MODEL` (optional) | Overrides default model (`gpt-4o-mini`). |
| `OPENAI_VECTOR_STORE_ID` | Vector store searched by the Searcher agent. |
| `OPENAI_ORG`, `OPENAI_PROJECT` (optional) | OpenAI tenancy scoping. |

`try_get_settings()` allows partial access without crashing, but `get_settings()` must succeed before the server can build agents or run inference.

### Agents
#### Orchestrator (`app/agents/orchestrator.py`)
- Primary conversational agent (`merak_orchestrator`).
- Collects required filters: `base_rate`, `success_rate`, `availability`, `industry`, `agent_type`.
- Once every facet is resolved, it invokes the Searcher tool (`search_agents`) exactly once.
- Expects the Searcher to return structured matches so it can summarise results for the user.

#### Searcher (`app/agents/searcher.py`)
- Specialist agent exposed as a tool via `as_tool`.
- Validates input payload, calls `prepare_search_parameters` function tool to convert raw inputs to an `AgentFilterPayload`, then executes the hosted `FileSearchTool`.
- Emits `SearchResults` (Pydantic schema) with applied filters, ranked matches, and raw metadata for downstream use.
- Ensures only USD `max_rate` and optional success rate thresholds are forwarded; `AgentFilterPayload.build_attribute_filter()` composes the OpenAI File Search JSON filter.

### Schemas
- `AgentFilterPayload` — internal normalised representation of facets. Handles enum coercion and filter construction.
- `SearchResults` / `SearchResultItem` — Searcher output contract surfaced to the orchestrator and UI.

### Integrations
- **OpenAI Agents SDK (`app/integrations/openai_agents.py`)**: helper utilities for creating Agents and Runners, reusing a cached `AsyncOpenAI` client.
- **ChatKit server (`app/integrations/chatkit_server.py`)**: extends `ChatKitServer`, wraps responses via `Runner.run_streamed`, and injects a `MerakAgentContext` (`AgentContext` derivative) so agents retain thread metadata. On instantiation it:
  1. Builds the hosted File Search tool (`app/services/search.py`).
  2. Constructs the Searcher agent and exposes it as `search_agents`.
  3. Builds the Merak orchestrator with the Searcher tool attached.
- **ThreadStore (`app/services/thread_store.py`)**: minimal in-memory store mirroring ChatKit demo semantics (no attachments). Suitable only for development/testing.

### Request Flow
1. **ChatKit client** posts to `/chatkit` with the SSE handshake.
2. **MerakChatKitServer** converts the incoming message to agent input and streams `ThreadStreamEvent` instances back to the client.
3. **Merak orchestrator** converses with the user, gathering all filter facets.
4. When ready, Merak invokes the `search_agents` tool with the finalised brief.
5. **Searcher agent** validates parameters, composes the vector store `attribute_filter`, invokes `FileSearchTool`, and returns structured `SearchResults`.
6. Merak resumes control, summarises the top matches, and streams them through ChatKit to the UI.

### Data & Persistence
- There is **no relational database**. All long-term data lives in the OpenAI vector store referenced by `OPENAI_VECTOR_STORE_ID`.
- Chat threads are stored in-memory only; restarting the backend clears conversation history.

## External Dependencies
- OpenAI API (Agents, File Search, vector stores).
- Optional tracing hooks can be enabled through the Agents SDK (`RunnerOptions.enable_tracing`).
- Developers must provision vector store indices and ingest agent profiles separately (see `MERAK_AGENT_PLAN.md` Phase 7 follow-ups).

## Operational Considerations
- **Error handling:** Missing SDKs raise runtime errors early (Agent creation, Searcher tool building, ChatKit instantiation).
- **Environment validation:** `/chatkit` responds with HTTP 503 if configuration or dependencies are missing.
- **Scaling:** Replace `ThreadStore` with a persistent store (e.g., Postgres or Redis) before production.
- **Security:** File attachments are intentionally disabled.

## Related Docs
- `.agent/README.md` — index of engineering documentation.
- `.agent/SOP/manual_testing.md` — step-by-step guide for running and manually testing Merak locally.
- `MERAK_AGENT_PLAN.md` — strategic implementation roadmap referenced by this architecture.
