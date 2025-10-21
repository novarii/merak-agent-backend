"""Helpers for configuring the hosted FileSearch tool used by Merak."""

from __future__ import annotations

from typing import Any

from app.core.settings import Settings, SettingsError, try_get_settings

try:  # pragma: no cover - optional dependency
    from agents import FileSearchTool
except ImportError:  # pragma: no cover - fallback when Agents SDK unavailable
    FileSearchTool = None  # type: ignore[assignment]

DEFAULT_MAX_RESULTS = 10
DEFAULT_RANKING_OPTIONS: dict[str, Any] = {"ranker": "auto", "score_threshold": 0.7}


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


__all__ = [
    "DEFAULT_MAX_RESULTS",
    "DEFAULT_RANKING_OPTIONS",
    "build_file_search_tool",
]
