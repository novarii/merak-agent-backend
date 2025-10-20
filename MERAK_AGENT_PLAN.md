# Merak Hiring Agent Build Plan

## Reference Docs
- OpenAI Agents Python Quickstart — https://openai.github.io/openai-agents-python/quickstart
- Handoff primitives — https://openai.github.io/openai-agents-python/ref/handoffs
- Agent `Runner` orchestration — https://openai.github.io/openai-agents-python/quickstart#run-agent-orchestration
- Structured agent output — https://openai.github.io/openai-agents-python/ja/ref/agent_output
- FileSearchTool for vector stores — https://openai.github.io/openai-agents-python/ref/tool#filesearchtool
- Example blueprint — `example_implementation.xml` (mirror of ChatKit demo backend; use for patterns, not as source of truth)

## Target User Flow
1. User asks Merak for an agent (e.g. “BI dashboard automation”).
2. Merak gathers missing filters (max rate, availability, skills, location).
3. Merak confirms a normalized brief.
4. Filter Standardizer agent converts the brief into a typed schema covering search facets.
5. Vector search tool retrieves matching agent profiles and applies business ranking.
6. Merak summarizes the top matches and surfaces structured results to the user and UI.

## Filter Facets
- `base_rate` — hourly base rate in USD (use numeric comparisons for filtering with optional ceiling thresholds provided by the user).
- `success_rate` — historical completion ratio expressed as a percentage (support minimum thresholds).
- `availability` — discrete enum with values `full_time`, `part_time`, or `contract`.
- `industry` — primary industry tags such as `fintech`, `healthcare`, etc.; allow multi-select filtering.
- `agent_type` — modality enum describing core channel support: `voice`, `text`, `image`, or `multi_modal`.
- `agent_id` — internal identifier included in payloads for reference only; do not expose as a filter.
- Filters feed semantic vector search by composing OpenAI File Search `attribute_filter` payloads (use `eq`, `gte`, `lte` operators combined under an `and` wrapper when multiple facets are present).

## Phase 1 — Foundations (reference `app/chat.py`, `app/memory_store.py`)
- Add OpenAI Agents SDK integration in `app/integrations/openai_agents.py`; follow the helper pattern in the example (see `get_runner` / tracing setup in `example_implementation.xml`).
- Port the in-memory thread store approach from `app/memory_store.py` to a dedicated service (`app/services/thread_store.py`) so ChatKit state is isolated from agent orchestration logic.
- Create shared Pydantic schemas under `app/schemas/agent_filters.py` using the clarifying field names and `AgentOutputSchema` pattern shown in the example’s `Fact` models.
- Stand up a ChatKit server wrapper `app/integrations/chatkit_server.py` that mirrors the `ChatKitServer` subclass in the example (ensure `stream_agent_response` and `ThreadItemConverter` wiring are preserved).
- Expose FastAPI routes `app/api/chatkit.py` and `app/api/health.py`, following the `ChatKit` SSE route from the example (`ChatKitServer.process(...)`).

## Phase 2 — Orchestrator Agent (“Merak”) (reference `agents/__init__.py`, `Agent` usage)
- Define Merak in `agents/orchestrator.py` using the instruction scaffolding shown in the example’s (`example_implementation.xml`) `Agent` definitions; include explicit clarifying prompts per filter facet.
- Implement a clarifying loop tool: model after `_handle_client_theme` + tool pattern in `app/chat.py`, but emit structured “missing_fields” payloads Merak can use to decide the next question.
- Capture conversation state using the `RunContextWrapper` idiom from the example so Merak has access to thread metadata and can resume sessions cleanly.
- Prepare detailed `handoff_description` metadata that mirrors the example’s handoff payload style (document keys in `app/schemas/handoffs.py`).

## Phase 3 — Searcher Agent (openai.github.io/openai-agents-python/tools/ agent-as-tool with context 7)
- Build `agents/merak/searcher.py` that accepts the orchestrator’s confirmed brief and returns `AgentFilterPayload` JSON validated with `AgentOutputSchema`.
- Surface the Searcher through `as_tool(tool_name="search_agents", tool_description="Normalize filters and retrieve candidates")` so Merak stays in charge of the conversation while invoking retrieval.
- Ensure the tool wraps the vector search helper from Phase 4, returning both the normalized payload and top results Merak can summarize.

## Phase 4 — Vector Store Search (reference tool wiring in example)
- Implement `app/services/search.py` wrapping OpenAI’s File Search tool; base configuration options (top_k, filters) on how the example wires tools in `function_tool` decorators.
- Register a `file_search` tool with the Searcher agent; reuse the `function_tool` decorator style from the example to keep tool signatures consistent.
- Provide a `build_file_search_tool` helper that returns `search_agents(query: str, industry: str | None = None, agent_type: str | None = None, max_rate: int | None = None, min_success_rate: int | None = None, availability: str | None = None, max_results: int = 10)`; construct the `attribute_filter` dynamically:
  ```python
  filters = []
  if industry:
      filters.append({"type": "eq", "key": "industry", "value": industry})
  if agent_type:
      filters.append({"type": "eq", "key": "agent_type", "value": agent_type})
  if max_rate is not None:
      filters.append({"type": "lte", "key": "base_rate", "value": max_rate})
  if min_success_rate is not None:
      filters.append({"type": "gte", "key": "success_rate", "value": min_success_rate})
  if availability:
      filters.append({"type": "eq", "key": "availability", "value": availability})
  attribute_filter = filters[0] if len(filters) == 1 else {"type": "and", "filters": filters} if filters else None
  client.vector_stores.search(
      vector_store_id=settings.vector_store_id,
      query=query,
      attribute_filter=attribute_filter,
      ranking_options={"ranker": "auto", "score_threshold": 0.7},
      max_num_results=max_results,
  )
  ```
- Add DTOs in `app/schemas/search_results.py` and transformation helpers to convert raw File Search hits into Merak-friendly ranking data.

## Phase 5 — Response Assembly (reference rendering utilities in example)
- Extend Merak to aggregate search results, enrich with rate/availability notes, and provide both structured and natural-language responses.
- Use the widget rendering pattern from `app/sample_widget.py` as inspiration for optional UI snippets (e.g. quick summary cards).
- Update FastAPI route to stream Merak’s final summaries and structured payloads over SSE, mirroring the example’s event streaming pipeline.

## Phase 6 — Observability & Evaluation (reference tracing hooks in example)
- Enable session tracing with the Agents SDK; follow the example’s logging setup (`logging.basicConfig(...)`) and extend with OpenTelemetry once available.
- Add unit tests in `tests/agents/test_merak.py` that cover clarifying-question logic and schema validation, using the fixture style implied by the example’s in-memory store.
- Add integration tests in `tests/integration/test_search_flow.py` that exercise the orchestrator → standardizer → vector search loop with mocked tool responses.

## Phase 7 — Deployment Readiness
- Document required environment variables (OpenAI key, vector store IDs) in `.env.example`, validating via `app/core/settings.py` in the same fashion the example centralizes constants in `app/constants.py`.
- Provide CLI or asynchronous tasks for ingesting agent profiles into the vector store (capture scripts in `agents/ingest/` or `scripts/` as follow-ups).
- Author a runbook in `docs/architecture.md` detailing agent responsibilities, handoff lifecycles, failure handling, and how to replay threads from the in-memory store implementation.
