"""Structured search result payloads returned by the Searcher agent."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

try:  # pragma: no cover - optional dependency
    from agents import AgentOutputSchema as _BaseSchema
except ImportError:  # pragma: no cover - fallback when Agents SDK unavailable
    _BaseSchema = BaseModel  # type: ignore[assignment]


class SearchResultItem(_BaseSchema):
    """Single agent match produced by vector store search."""

    model_config = {"extra": "forbid"}

    agent_id: Optional[str] = Field(
        default=None,
        description="Internal identifier for the agent profile.",
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Human-friendly name or title for the agent.",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Short description synthesized from the agent profile.",
    )
    score: Optional[float] = Field(
        default=None,
        ge=0,
        description="Relevance score returned by vector search.",
    )
    availability: Optional[str] = Field(
        default=None,
        description="Availability facet mapped from the profile (full_time, etc.).",
    )
    base_rate: Optional[float] = Field(
        default=None,
        ge=0,
        description="Base hourly rate in USD when available.",
    )
    success_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Historical completion percentage when available.",
    )
    industry: Optional[str] = Field(
        default=None,
        description="Primary industry tag aligned with the query.",
    )
    agent_type: Optional[str] = Field(
        default=None,
        description="Primary modality (voice, text, image, multi_modal).",
    )
    raw_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Unprocessed metadata blob from the vector store result.",
    )


class SearchResults(_BaseSchema):
    """Aggregate results returned by the Searcher agent."""

    model_config = {"extra": "forbid"}

    query: str = Field(
        ...,
        description="Semantic search query issued to the vector store.",
    )
    applied_filters: dict[str, Any] = Field(
        default_factory=dict,
        description="Filters applied when executing the search request.",
    )
    matches: List[SearchResultItem] = Field(
        default_factory=list,
        description="Ordered list of matching agents from the vector store.",
    )

    def top_match(self) -> SearchResultItem | None:
        """Return the highest ranked match, if any."""
        return self.matches[0] if self.matches else None


__all__ = ["SearchResultItem", "SearchResults"]
