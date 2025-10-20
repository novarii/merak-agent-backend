"""Utilities for building vector search tools used by the Searcher agent."""

from __future__ import annotations

from typing import Any

from app.core.settings import SettingsError, get_settings, try_get_settings

try:  # pragma: no cover - optional dependency
    from agents import FileSearchTool
except ImportError:  # pragma: no cover - fallback when Agents SDK unavailable
    FileSearchTool = None  # type: ignore[assignment]


def build_file_search_tool(
    *,
    vector_store_id: str | None = None,
    max_results: int = 10,
) -> Any:
    """Return an OpenAI-hosted FileSearchTool configured for the Merak vector store.

    Args:
        vector_store_id: Explicit vector store identifier. When omitted the value will be
            sourced from ``Settings.openai_vector_store_id``.
        max_results: Upper bound on the number of results the tool should return.

    Raises:
        RuntimeError: When the Agents SDK (and thus FileSearchTool) is unavailable.
        SettingsError: When no vector store identifier can be resolved.
    """

    if FileSearchTool is None:
        raise RuntimeError(
            "OpenAI Agents SDK is required to construct the FileSearchTool. Install "
            "`openai-agents` to enable semantic search."
        )

    store_id = vector_store_id
    if store_id is None:
        settings = try_get_settings()
        if settings is None or not settings.openai_vector_store_id:
            raise SettingsError(
                "OPENAI_VECTOR_STORE_ID must be configured to enable semantic search."
            )
        store_id = settings.openai_vector_store_id

    return FileSearchTool(  # type: ignore[call-arg]
        vector_store_ids=[store_id],
        max_num_results=max_results,
    )


__all__ = ["build_file_search_tool"]
