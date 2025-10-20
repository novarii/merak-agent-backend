"""Pydantic models describing the normalized filters used for agent retrieval."""

from __future__ import annotations

from enum import Enum
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field

try:  # pragma: no cover - optional dependency
    from agents import AgentOutputSchema as _BaseSchema
except ImportError:  # pragma: no cover - fallback when Agents SDK unavailable
    _BaseSchema = BaseModel  # type: ignore[assignment]


class AvailabilityOption(str, Enum):
    """Engagement model requested by the user."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"


class AgentTypeOption(str, Enum):
    """Supported communication modality for an agent profile."""

    VOICE = "voice"
    TEXT = "text"
    IMAGE = "image"
    MULTI_MODAL = "multi_modal"


class BaseRateFilter(_BaseSchema):
    """Maximum hourly base rate constraint (assumes USD)."""

    model_config = ConfigDict(extra="forbid")

    max_rate: int | None = Field(
        default=None,
        ge=0,
        description="Inclusive upper bound for the acceptable hourly base rate in USD.",
    )

    def resolved(self) -> bool:
        """Return True when at least one rate constraint has been provided."""
        return self.max_rate is not None


class SuccessRateFilter(_BaseSchema):
    """Historical completion ratio thresholds."""

    model_config = ConfigDict(extra="forbid")

    min_success_rate: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum historical completion percentage required (0-100).",
    )

    def resolved(self) -> bool:
        """Return True when a minimum success rate threshold is present."""
        return self.min_success_rate is not None


class AgentFilterPayload(_BaseSchema):
    """Normalized filter payload Merak hands to the semantic search layer."""

    model_config = ConfigDict(extra="forbid")

    summary: str | None = Field(
        default=None,
        description="Normalized summary of the user's request.",
    )
    search_query: str | None = Field(
        default=None,
        description="Explicit semantic search query; falls back to the summary when absent.",
    )
    base_rate: BaseRateFilter = Field(default_factory=BaseRateFilter)
    success_rate: SuccessRateFilter = Field(default_factory=SuccessRateFilter)
    availability: AvailabilityOption | None = Field(
        default=None,
        description="Preferred working model (full-time, part-time, or contract).",
    )
    industries: List[str] = Field(
        default_factory=list,
        description="Normalized industry tags (e.g., 'fintech', 'healthcare').",
    )
    agent_types: List[AgentTypeOption] = Field(
        default_factory=list,
        description="Communication modalities the agent must support.",
    )
    agent_id: str | None = Field(
        default=None,
        description="Internal identifier carried for context; not used for filtering.",
    )

    def resolved_query(self) -> str | None:
        """Return the semantic search query seeded by Merak."""
        return self.search_query or self.summary

    def missing_fields(self) -> list[str]:
        """Return filter facets that still require clarification."""
        missing: list[str] = []

        if not self.resolved_query():
            missing.append("search_query")
        if not self.base_rate.resolved():
            missing.append("base_rate")
        if not self.success_rate.resolved():
            missing.append("success_rate")
        if self.availability is None:
            missing.append("availability")
        if not self.industries:
            missing.append("industry")
        if not self.agent_types:
            missing.append("agent_type")
        return missing

    def is_complete(self) -> bool:
        """Return True once all required filter facets have been filled."""
        return not self.missing_fields()

    def build_attribute_filter(self) -> dict[str, Any] | None:
        """Construct an OpenAI File Search attribute_filter payload."""
        filters: list[dict[str, Any]] = []

        if self.industries:
            industry_filters = [
                {"type": "eq", "key": "industry", "value": industry}
                for industry in self.industries
            ]
            filters.append(
                industry_filters[0]
                if len(industry_filters) == 1
                else {"type": "or", "filters": industry_filters}
            )

        if self.agent_types:
            agent_type_filters = [
                {"type": "eq", "key": "agent_type", "value": agent_type.value}
                for agent_type in self.agent_types
            ]
            filters.append(
                agent_type_filters[0]
                if len(agent_type_filters) == 1
                else {"type": "or", "filters": agent_type_filters}
            )

        if self.base_rate.max_rate is not None:
            filters.append(
                {"type": "lte", "key": "base_rate", "value": self.base_rate.max_rate}
            )

        if self.success_rate.min_success_rate is not None:
            filters.append(
                {"type": "gte", "key": "success_rate", "value": self.success_rate.min_success_rate}
            )

        if self.availability is not None:
            filters.append(
                {"type": "eq", "key": "availability", "value": self.availability.value}
            )

        if not filters:
            return None

        return filters[0] if len(filters) == 1 else {"type": "and", "filters": filters}


__all__ = [
    "AgentFilterPayload",
    "AgentTypeOption",
    "AvailabilityOption",
    "BaseRateFilter",
    "SuccessRateFilter",
]
