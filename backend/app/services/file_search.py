"""Helpers for configuring the hosted FileSearch tool used by Merak."""

from __future__ import annotations

import json
from typing import Any, Iterable, List

from pydantic import BaseModel, Field

from app.core.settings import Settings, SettingsError, try_get_settings
from app.schemas.agent_filters import (
    AgentFilterPayload,
    AgentTypeOption,
    AvailabilityOption,
    BaseRateFilter,
    SuccessRateFilter,
)

try:  # pragma: no cover - optional dependency
    from agents import FileSearchTool, FunctionTool
    from agents.tool import ToolOutputText
except ImportError:  # pragma: no cover - fallback when Agents SDK unavailable
    FileSearchTool = FunctionTool = ToolOutputText = None  # type: ignore[assignment]

DEFAULT_MAX_RESULTS = 10
DEFAULT_RANKING_OPTIONS: dict[str, Any] = {"ranker": "auto", "score_threshold": 0.7}


class _MerakSearchArgs(BaseModel):
    """Schema for Merak's high-level search intent."""

    query: str = Field(..., description="Semantic search query describing the ideal agent.")
    industries: List[str] | None = Field(
        default=None,
        description="Industries to prioritize (e.g., fintech, healthcare).",
    )
    agent_types: List[str] | None = Field(
        default=None,
        description="Preferred communication modalities (voice, text, image, multi_modal).",
    )
    max_rate: int | None = Field(
        default=None,
        ge=0,
        description="Maximum hourly rate in USD.",
    )
    min_success_rate: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum completion percentage required.",
    )
    availability: str | None = Field(
        default=None,
        description="Desired availability (full_time, part_time, contract).",
    )
    max_results: int = Field(
        default=DEFAULT_MAX_RESULTS,
        ge=1,
        le=50,
        description="Upper bound on returned matches.",
    )


def _resolve_vector_store_id(
    settings: Settings | None,
    *,
    override: str | None = None,
) -> str:
    """Return the vector store identifier, raising if no value can be resolved."""
    if override:
        return override

    candidate = (settings or try_get_settings())
    if candidate and candidate.openai_vector_store_id:
        return candidate.openai_vector_store_id

    raise SettingsError(
        "OPENAI_VECTOR_STORE_ID must be configured to enable semantic search. "
        "Provide it via Settings or pass `vector_store_id` explicitly."
    )


def _normalize_choice(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _coerce_agent_types(values: Iterable[str] | None) -> list[AgentTypeOption]:
    if not values:
        return []
    normalized: list[AgentTypeOption] = []
    seen: set[AgentTypeOption] = set()
    for value in values:
        candidate = _normalize_choice(str(value))
        for option in AgentTypeOption:
            if candidate in (option.value, option.name.lower()):
                if option not in seen:
                    seen.add(option)
                    normalized.append(option)
                break
    return normalized


def _coerce_availability(value: str | None) -> AvailabilityOption | None:
    if value is None:
        return None
    candidate = _normalize_choice(value)
    for option in AvailabilityOption:
        if candidate in (option.value, option.name.lower()):
            return option
    return None


def _stringify_for_json(value: Any) -> Any:
    """Best-effort conversion that keeps JSON serialization stable."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _stringify_for_json(sub_value) for key, sub_value in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_stringify_for_json(item) for item in value]
    return repr(value)


def build_file_search_tool(
    *,
    settings: Settings | None = None,
    vector_store_id: str | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    ranking_options: dict[str, Any] | None = None,
    include_search_results: bool = True,
) -> Any:
    """Instantiate the Agents SDK ``FileSearchTool`` for the Merak vector store."""
    if FileSearchTool is None:
        raise RuntimeError(
            "OpenAI Agents SDK is required to construct the FileSearchTool. Install "
            "`openai-agents` to enable semantic search."
        )

    store_id = _resolve_vector_store_id(settings, override=vector_store_id)

    tool_kwargs: dict[str, Any] = {
        "vector_store_ids": [store_id],
        "include_search_results": include_search_results,
    }

    if max_results is not None:
        tool_kwargs["max_num_results"] = max_results

    if ranking_options is not None:
        tool_kwargs["ranking_options"] = ranking_options
    else:
        tool_kwargs["ranking_options"] = DEFAULT_RANKING_OPTIONS

    return FileSearchTool(**tool_kwargs)  # type: ignore[call-arg]


def build_merak_search_function(
    file_search_tool: Any,
    *,
    tool_name: str = "search_agents",
    tool_description: str | None = None,
) -> Any:
    """Wrap the hosted FileSearch tool behind a structured function tool for Merak."""
    if FunctionTool is None:
        raise RuntimeError(
            "openai-agents-python is required to build Merak search tools. Install "
            "`openai-agents` to enable semantic search."
        )

    async def _invoke(ctx: Any, args: str) -> Any:
        parsed = _MerakSearchArgs.model_validate_json(args)
        industries = [item.strip() for item in parsed.industries or [] if item and item.strip()]
        agent_types = _coerce_agent_types(parsed.agent_types)
        availability = _coerce_availability(parsed.availability)

        payload = AgentFilterPayload(
            summary=parsed.query,
            search_query=parsed.query,
            industries=industries,
            agent_types=agent_types,
            availability=availability,
            base_rate=BaseRateFilter(max_rate=parsed.max_rate),
            success_rate=SuccessRateFilter(min_success_rate=parsed.min_success_rate),
        )

        attribute_filter = payload.build_attribute_filter()

        tool_input = {
            "query": payload.resolved_query() or parsed.query,
            "attribute_filter": attribute_filter,
            "max_num_results": parsed.max_results,
        }

        if not hasattr(ctx, "call_tool"):
            raise RuntimeError(
                "RunContextWrapper does not expose `call_tool`; unable to invoke FileSearchTool."
            )

        raw_result = await ctx.call_tool(file_search_tool, json.dumps(tool_input))

        metadata = {
            "query": tool_input["query"],
            "applied_filters": {
                "industries": industries,
                "agent_types": [option.value for option in agent_types],
                "max_rate": parsed.max_rate,
                "min_success_rate": parsed.min_success_rate,
                "availability": availability.value if availability else None,
            },
            "attribute_filter": attribute_filter,
            "raw_result": _stringify_for_json(raw_result),
        }

        summary_text = (
            f"Searched for '{metadata['query']}' "
            f"with filters {metadata['applied_filters']}."
        )
        metadata_json = json.dumps(metadata, default=_stringify_for_json)

        text_output = f"{summary_text}\nmetadata={metadata_json}"
        if ToolOutputText is not None:
            return ToolOutputText(text=text_output)  # type: ignore[call-arg]
        return text_output

    description = tool_description or "Search Merak agent profiles using the configured vector store."

    return FunctionTool(
        name=tool_name,
        description=description,
        params_json_schema=_MerakSearchArgs.model_json_schema(),
        on_invoke_tool=_invoke,
    )


__all__ = [
    "DEFAULT_MAX_RESULTS",
    "DEFAULT_RANKING_OPTIONS",
    "build_file_search_tool",
    "build_merak_search_function",
]
