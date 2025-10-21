# Merak Single-Agent FileSearch Migration

## Background
- Current flow splits orchestration between Merak and a dedicated search agent, which increases tool-handoff complexity and diverges from the latest product direction.
- We want Merak to remain the sole LLM-driven agent, invoking a typed FileSearch tool implemented as a `@dataclass` when user intent implies profile lookups.
- The OpenAI Agents SDK (see `example_implementation.xml`) already demonstrates single-agent orchestration with tool delegates, making the simplification feasible without regressing core capabilities.

## Goals
- Remove the Searcher agent and have Merak own clarification, brief normalization, and candidate retrieval.
- Introduce a reusable `FileSearchTool` dataclass that translates Merak’s requests into OpenAI File Search payloads with attribute filters.
- Refactor services, schemas, and FastAPI endpoints so the new tool surfaces candidate results and structured payloads identical (or better) to today’s responses.
- Maintain observability, tests, and documentation parity throughout the migration.

## Non-Goals
- Changing the underlying vector store provider or ingestion pipeline.
- Overhauling ChatKit session management or SSE streaming contracts beyond necessary wiring updates.
- Introducing conversational skills unrelated to hiring (e.g., task management, calendaring).

## Target User Flow
1. User engages Merak with a hiring request (profile search, refinement, follow-up questions).
2. Merak clarifies missing facets (rate, availability, skills) until the brief is complete.
3. Merak calls the `FileSearchTool` with the normalized query and filters.
4. File Search returns ranked candidates; Merak summarizes results and pushes structured data to the UI.
5. Subsequent user questions reuse context; Merak may call the tool again as filters change.

## Acceptance Criteria
- Merak is the only agent defined in `agents/`; its prompt encapsulates clarification, filtering, and retrieval guidance.
- A dataclass-backed FileSearch tool lives under `app/services/file_search.py` (or equivalent), exposes typed parameters, and translates calls into OpenAI File Search requests with attribute filters.
- FastAPI endpoints continue streaming ChatKit responses without additional agent-level hops; manual smoke checks confirm tool calls and response formatting.
- Updated documents (`.agent/System/**`, `.agent/SOP/**`, `.env.example`) reflect the new architecture and configuration touchpoints.

## Implementation Plan

### Phase 1 — Tool Foundations
- Add `app/services/file_search.py` with a `build_file_search_tool(settings: Settings) -> FileSearchTool` helper that instantiates the SDK’s `FileSearchTool` dataclass (`agents.tool.FileSearchTool`) by passing the configured `vector_store_ids`, `max_num_results`, and `ranking_options`.
- Wrap the SDK tool with a `function_tool` helper (`build_merak_search_function(...)`) that accepts structured arguments (`query`, optional filters) and, inside `on_invoke_tool`, constructs the `Filters` payload the dataclass expects; return `ToolOutputText` containing both a concise summary and serialized metadata for the LLM.
- Keep schemas minimal: reuse existing filter/result typing where available and defer heavy DTO layers until the workflow stabilizes.
- Update `app/integrations/__init__.py` (or module registry) to expose the builder so agents can fetch the configured tool without duplicating code.

### Phase 2 — Merak Agent Refactor
- Consolidate orchestration logic into `agents/merak.py`, updating prompts to explain when and how to invoke the new search tool (`Tool` union entry) with clear parameter guidance the LLM can follow.
- Remove the Searcher agent and related files (e.g., `agents/merak/searcher.py`, associated tool registration) while keeping reusable prompt fragments or schemas if still relevant.
- Adjust agent initialization (`app/services/agent_factory.py` or equivalent) to instantiate Merak with the `FileSearchTool` instance and any auxiliary tools (theme switching, fact saving); ensure enablement guards (`is_enabled`) match contexts where search is valid.

### Phase 3 — API & Service Updates
- Ensure FastAPI bootstrap (`app/main.py`, `app/api/chatkit.py`) references the new Merak setup and no longer loads the Searcher agent.
- Update service orchestration (`app/services/runner.py`, `app/integrations/openai_agents.py`, etc.) so tool catalog injection includes the FileSearch dataclass and removes unused search plumbing.
- Refresh dependency-injected caches or memory stores to reflect single-agent assumptions (e.g., thread metadata references only Merak).

### Phase 4 — Documentation & Rollout
- Update `.agent/System/project_architecture.md` with the simplified single-agent diagram and tool wiring notes.
- Refresh SOP snippets that referenced the retired search agent; point contributors at the new `function_tool` helper for future tweaks.
- Document any environment variable changes in `.env.example`; capture a short manual validation checklist (ChatKit happy path, tool invocation, result rendering) for staging sign-off.

## Dependencies & Risks
- Requires parity with existing vector store indices—ensure queries and filters match current metadata or coordinate schema updates with the ingestion pipeline.
- Prompt changes must be validated to prevent over-triggering tool calls; consider sandbox runs to tune instructions before production rollout.
- Any caching or memoization layers tied to the Searcher agent should be audited to avoid stale data or exceptions once the module is removed.
