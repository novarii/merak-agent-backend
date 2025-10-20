"""Pydantic models describing the normalized hiring brief Merak collects."""

from __future__ import annotations

from datetime import date
from typing import Final, List, Sequence

from pydantic import BaseModel, ConfigDict, Field

try:  # pragma: no cover - optional dependency
    from agents import AgentOutputSchema as _BaseSchema
except ImportError:  # pragma: no cover - fallback when Agents SDK unavailable
    _BaseSchema = BaseModel  # type: ignore[assignment]

DEFAULT_CURRENCY: Final[str] = "USD"


class RateConstraints(_BaseSchema):
    """Desired compensation boundaries for candidate search."""

    model_config = ConfigDict(extra="forbid")

    currency: str = Field(
        default=DEFAULT_CURRENCY,
        min_length=3,
        max_length=3,
        description="ISO-4217 currency code for monetary filters.",
    )
    max_hourly_rate: float | None = Field(
        default=None,
        ge=0,
        description="Upper hourly rate threshold in the configured currency.",
    )
    max_monthly_rate: float | None = Field(
        default=None,
        ge=0,
        description="Upper monthly rate threshold in the configured currency.",
    )

    def resolved(self) -> bool:
        """Return True when at least one rate constraint has been provided."""
        return self.max_hourly_rate is not None or self.max_monthly_rate is not None


class AvailabilityWindow(_BaseSchema):
    """Window describing when the user needs the agent to start and workload."""

    model_config = ConfigDict(extra="forbid")

    start_date: date | None = Field(
        default=None,
        description="Earliest acceptable start date for the engagement.",
    )
    hours_per_week: int | None = Field(
        default=None,
        ge=1,
        le=168,
        description="Expected weekly hours commitment.",
    )
    timezone: str | None = Field(
        default=None,
        description="Preferred timezone or offset for synchronous collaboration.",
    )

    def resolved(self) -> bool:
        """Return True once both start date and hours are known."""
        return self.start_date is not None and self.hours_per_week is not None


class LocationPreference(_BaseSchema):
    """Geographic filters for candidate matching."""

    model_config = ConfigDict(extra="forbid")

    remote_ok: bool | None = Field(
        default=None,
        description="Whether fully remote candidates are acceptable.",
    )
    preferred_countries: List[str] = Field(
        default_factory=list,
        description="Country codes representing preferred working locations.",
    )
    onsite_cities: List[str] = Field(
        default_factory=list,
        description="Specific metro areas required for on-site or hybrid roles.",
    )

    def resolved(self) -> bool:
        """Return True when remote policy is known and any on-site locales are captured."""
        if self.remote_ok is None:
            return False
        if self.remote_ok:
            return True
        return bool(self.onsite_cities or self.preferred_countries)


class AgentFilterPayload(_BaseSchema):
    """Normalized hiring brief Merak uses to drive downstream retrieval."""

    model_config = ConfigDict(extra="forbid")

    project_brief: str | None = Field(
        default=None,
        description="Short description of the business need supplied by the user.",
    )
    role_title: str | None = Field(
        default=None,
        description="Canonical title describing the desired agent (e.g., 'Data Analyst').",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills that must be present for a candidate to qualify.",
    )
    nice_to_have_skills: List[str] = Field(
        default_factory=list,
        description="Supplemental skills that should boost ranking but are not mandatory.",
    )
    rate: RateConstraints = Field(default_factory=RateConstraints)
    availability: AvailabilityWindow = Field(default_factory=AvailabilityWindow)
    location: LocationPreference = Field(default_factory=LocationPreference)

    def missing_fields(self) -> list[str]:
        """Return human-readable names for filters that still need clarification."""
        missing: list[str] = []

        if not self.project_brief:
            missing.append("project_brief")
        if not self.role_title:
            missing.append("role_title")
        if not self.required_skills:
            missing.append("required_skills")
        if not self.rate.resolved():
            missing.append("rate")
        if not self.availability.resolved():
            missing.append("availability")
        if not self.location.resolved():
            missing.append("location")
        return missing

    def is_complete(self) -> bool:
        """Return True when no additional clarifications are required."""
        return not self.missing_fields()

    def extend_skills(self, skills: Sequence[str], *, required: bool = True) -> None:
        """Merge additional skills into either required or nice-to-have lists."""
        target = self.required_skills if required else self.nice_to_have_skills
        for skill in skills:
            normalized = skill.strip()
            if not normalized:
                continue
            if normalized not in target:
                target.append(normalized)


__all__ = [
    "AgentFilterPayload",
    "AvailabilityWindow",
    "LocationPreference",
    "RateConstraints",
]
