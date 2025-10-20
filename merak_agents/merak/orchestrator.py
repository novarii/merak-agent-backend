"""Merak orchestrator agent definition and supporting tools."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence

from app.integrations.openai_agents import create_agent
from app.schemas.agent_filters import AgentFilterPayload

try:  # pragma: no cover - optional dependency
    from agents import Agent, AgentContext, RunContextWrapper, function_tool
except ImportError:  # pragma: no cover - fallback shims keep module importable
    Agent = AgentContext = RunContextWrapper = None  # type: ignore[assignment]

    def function_tool(*args: Any, **kwargs: Any):  # type: ignore[override]
        if args and callable(args[0]) and not kwargs:
            return args[0]

        def decorator(func: Any) -> Any:
            return func

        return decorator

try:  # pragma: no cover - optional dependency
    from chatkit.types import ThreadMetadata
except ImportError:  # pragma: no cover
    ThreadMetadata = Any  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from pydantic import ConfigDict, Field
except ImportError:  # pragma: no cover
    ConfigDict = Field = None  # type: ignore[assignment]

MERAK_AGENT_NAME = "Merak Orchestrator"

MERAK_AGENT_INSTRUCTIONS = textwrap.dedent(
    """\
    You are Merak, a hiring assistant that interviews users to collect a complete,
    structured brief for sourcing AI agents. Follow this flow:
    1. Greet the user and quickly summarize their request so you understand the project.
    2. Ask targeted clarifying questions until every required filter is filled:
       - project_brief
       - role_title
       - required_skills
       - rate (hourly or monthly max)
       - availability (start date and weekly hours)
       - location preferences (remote, countries, on-site cities)
    3. After each user answer call the `capture_filter_update` tool with the fields you learned.
    4. Use `report_missing_filters` whenever you need to know which filters still lack detail.
    5. When all filters are satisfied, call `finalize_brief` to produce the summarized payload,
       then present a concise confirmation to the user. After confirmation, hand off to the
       Filter Standardizer agent.

    General guidance:
    - Ask one focused question at a time when possible.
    - Reflect the user’s answers back before moving on.
    - Only call `finalize_brief` when `report_missing_filters` returns an empty list.
    - Decline requests unrelated to agent hiring politely.
    """
)


def _merge_filter_payload(
    existing: AgentFilterPayload,
    updates: Mapping[str, Any],
) -> AgentFilterPayload:
    """Return a new payload with nested updates applied."""
    current = existing.model_dump()
    for key, value in updates.items():
        if key not in current:
            current[key] = value
            continue
        current_value = current[key]
        if isinstance(current_value, MutableMapping) and isinstance(value, Mapping):
            # Deep merge dict-like nested structures (rate, availability, location)
            current_value.update(value)  # type: ignore[call-arg]
            current[key] = current_value
        else:
            current[key] = value
    return AgentFilterPayload.model_validate(current)


def _normalize_skills(skills: Sequence[str]) -> List[str]:
    normalized: List[str] = []
    for raw in skills:
        value = raw.strip()
        if not value:
            continue
        if value not in normalized:
            normalized.append(value)
    return normalized


if AgentContext is not None and Field is not None:  # pragma: no branch - runtime guard

    class MerakAgentContext(AgentContext):
        """Agent context shared between tools and orchestrator runtime."""

        model_config = ConfigDict(arbitrary_types_allowed=True)

        thread: ThreadMetadata  # type: ignore[assignment]
        request_context: dict[str, Any]
        filters: AgentFilterPayload = Field(default_factory=AgentFilterPayload)
        handoff_ready: bool = False
        clarifications: list[str] = Field(default_factory=list)

else:  # pragma: no cover - fallback when Agents SDK absent

    @dataclass
    class MerakAgentContext:  # type: ignore[no-redef]
        thread: Any
        request_context: dict[str, Any]
        filters: AgentFilterPayload = field(default_factory=AgentFilterPayload)
        handoff_ready: bool = False
        clarifications: list[str] = field(default_factory=list)


@function_tool(
    description_override="Update Merak's understanding of the hiring brief with newly provided details."
)
async def capture_filter_update(ctx: Any, filters: Dict[str, Any]) -> Dict[str, Any]:
    """Merge clarified fields into the shared `AgentFilterPayload`."""
    payload = ctx.context.filters  # type: ignore[attr-defined]

    mutable_filters = dict(filters)
    if "required_skills" in mutable_filters and isinstance(mutable_filters["required_skills"], Sequence):
        mutable_filters["required_skills"] = _normalize_skills(
            mutable_filters["required_skills"]  # type: ignore[arg-type]
        )
    if "nice_to_have_skills" in mutable_filters and isinstance(
        mutable_filters["nice_to_have_skills"], Sequence
    ):
        mutable_filters["nice_to_have_skills"] = _normalize_skills(
            mutable_filters["nice_to_have_skills"]  # type: ignore[arg-type]
        )

    updated = _merge_filter_payload(payload, mutable_filters)
    ctx.context.filters = updated  # type: ignore[attr-defined]
    return {"filters": updated.model_dump()}


@function_tool(
    description_override="Return the list of remaining filters Merak still needs to clarify."
)
async def report_missing_filters(ctx: Any) -> Dict[str, Any]:
    """Expose remaining filter gaps so the agent knows what to ask next."""
    pending = ctx.context.filters.missing_fields()  # type: ignore[attr-defined]
    return {"missing_fields": pending}


@function_tool(
    description_override="Mark the hiring brief as complete and ready for handoff once all filters are filled."
)
async def finalize_brief(ctx: Any) -> Dict[str, Any]:
    """Confirm that all filters are filled and surface the structured payload."""
    pending = ctx.context.filters.missing_fields()  # type: ignore[attr-defined]
    if pending:
        raise ValueError(
            "Cannot finalize the brief yet. Still missing: " + ", ".join(sorted(pending))
        )
    ctx.context.handoff_ready = True  # type: ignore[attr-defined]
    return {"filters": ctx.context.filters.model_dump()}  # type: ignore[attr-defined]


TOOLKIT = [
    capture_filter_update,
    report_missing_filters,
    finalize_brief,
]


def create_merak_agent() -> Any:
    """Build the Merak orchestrator agent with the configured toolchain."""
    if Agent is None:
        raise RuntimeError("OpenAI Agents SDK is required to create the Merak orchestrator.")
    return create_agent(
        name=MERAK_AGENT_NAME,
        instructions=MERAK_AGENT_INSTRUCTIONS,
        tools=TOOLKIT,
    )


__all__ = [
    "MERAK_AGENT_INSTRUCTIONS",
    "MERAK_AGENT_NAME",
    "MerakAgentContext",
    "capture_filter_update",
    "create_merak_agent",
    "finalize_brief",
    "report_missing_filters",
    "TOOLKIT",
]
