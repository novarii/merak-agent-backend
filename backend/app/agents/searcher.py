"""Searcher agent responsible for running semantic vector queries."""

from __future__ import annotations

from textwrap import dedent
from typing import Any, Iterable, List, Optional

from app.schemas.agent_filters import (
    AgentFilterPayload,
    AgentTypeOption,
    AvailabilityOption,
    BaseRateFilter,
    SuccessRateFilter,
)
from app.schemas.search_results import SearchResults

try:  # pragma: no cover - optional dependency
    from agents import Agent, AgentOutputSchema, function_tool
except ImportError:  # pragma: no cover - provide runtime failure when SDK missing
    Agent = AgentOutputSchema = function_tool = None  # type: ignore[assignment]

SEARCHER_AGENT_NAME = "merak_searcher"
SEARCH_FILTER_TOOL_NAME = "prepare_search_parameters"
SEARCHER_TOOL_DESCRIPTION = "Normalize filters and retrieve ranked agent matches."

SEARCHER_INSTRUCTIONS = dedent(
    """
    You are the Searcher. The orchestrator sends you a single JSON object containing:
      {
        "query": "<semantic search query>",
        "industries": ["fintech", ...],
        "agent_types": ["voice", "text", "image", "multi_modal"],
        "max_rate": <max hourly USD rate or null>,
        "min_success_rate": <minimum success percentage or null>,
        "availability": "full_time" | "part_time" | "contract" | null,
        "max_results": <integer, default 10>
      }

    Follow this workflow:
    1. Parse the JSON payload exactly. If required fields are missing, ask the caller
       to resend the input with all fields.
    2. Call the `prepare_search_parameters` tool with the parsed values. This returns
       sanitized filters, including the attribute_filter JSON required by the vector store.
    3. Call the `file_search` tool once using the returned payload:
         {
           "query": <query>,
           "attribute_filter": <attribute_filter or null>,
           "max_num_results": <max_results>
         }
    4. Inspect the tool output and project it into the SearchResults schema. For every
       hit, populate the fields:
         - agent_id (if present in metadata)
         - display_name or title
         - summary (short description)
         - score (numeric relevance score)
         - availability, base_rate, success_rate, industry, agent_type when available
         - raw_metadata (entire metadata dict from the search result)
    5. Emit strictly valid JSON conforming to the SearchResults schema. Do not add
       extraneous keys. Always copy the `applied_filters` dictionary returned by the
       prepare_search_parameters tool so the orchestrator can display it.

    Never converse with the user; simply return the structured JSON response.
    """
).strip()


def _normalize_choice(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _coerce_availability(value: Optional[str]) -> AvailabilityOption | None:
    if value is None:
        return None
    normalized = _normalize_choice(value)
    for option in AvailabilityOption:
        if option.value == normalized or option.name.lower() == normalized:
            return option
    return None


def _coerce_agent_types(values: Optional[Iterable[str]]) -> List[AgentTypeOption]:
    if not values:
        return []
    seen: set[AgentTypeOption] = set()
    result: list[AgentTypeOption] = []
    for value in values:
        normalized = _normalize_choice(str(value))
        for option in AgentTypeOption:
            if option.value == normalized or option.name.lower() == normalized:
                if option not in seen:
                    seen.add(option)
                    result.append(option)
                break
    return result


if function_tool is not None:

    @function_tool(
        name_override=SEARCH_FILTER_TOOL_NAME,
        description_override=(
            "Normalize Merak search filters and build attribute_filter payloads for vector search."
        ),
    )
    def prepare_search_parameters(
        query: str,
        industries: Optional[List[str]] = None,
        agent_types: Optional[List[str]] = None,
        max_rate: Optional[int] = None,
        min_success_rate: Optional[int] = None,
        availability: Optional[str] = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        industries_list = [item.strip() for item in industries or [] if item and item.strip()]
        agent_type_options = _coerce_agent_types(agent_types)
        availability_option = _coerce_availability(availability)

        payload = AgentFilterPayload(
            summary=query,
            search_query=query,
            industries=industries_list,
            agent_types=agent_type_options,
            availability=availability_option,
            base_rate=BaseRateFilter(max_rate=max_rate),
            success_rate=SuccessRateFilter(min_success_rate=min_success_rate),
        )

        attribute_filter = payload.build_attribute_filter()

        return {
            "query": query,
            "attribute_filter": attribute_filter,
            "applied_filters": {
                "industries": industries_list,
                "agent_types": [option.value for option in agent_type_options],
                "max_rate": max_rate,
                "min_success_rate": min_success_rate,
                "availability": availability_option.value if availability_option else None,
            },
            "max_num_results": max_results,
        }

else:  # pragma: no cover - executed only when Agents SDK missing

    def prepare_search_parameters(*_: Any, **__: Any) -> dict[str, Any]:
        raise RuntimeError(
            "openai-agents-python is required to normalize search parameters. "
            "Install `openai-agents` to enable the Searcher agent."
        )


def build_searcher_agent(file_search_tool: Any, **agent_kwargs: Any) -> Any:
    """Instantiate the Searcher agent with the required tools."""
    if Agent is None or AgentOutputSchema is None or function_tool is None:
        raise RuntimeError(
            "openai-agents-python is required to build the Searcher agent. Install "
            "`openai-agents` to enable semantic search."
        )

    tools = [prepare_search_parameters, file_search_tool]  # type: ignore[list-item]

    return Agent(  # type: ignore[call-arg]
        name=SEARCHER_AGENT_NAME,
        instructions=SEARCHER_INSTRUCTIONS,
        output_schema=AgentOutputSchema(output_type=SearchResults),
        tools=tools,
        **agent_kwargs,
    )


__all__ = [
    "SEARCHER_AGENT_NAME",
    "SEARCH_FILTER_TOOL_NAME",
    "SEARCHER_TOOL_DESCRIPTION",
    "build_searcher_agent",
    "prepare_search_parameters",
]
