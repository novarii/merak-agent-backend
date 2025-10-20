"""Helper utilities for working with the OpenAI Agents Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Iterable, Sequence

from app.core.settings import SettingsError, get_settings, try_get_settings

try:  # pragma: no cover - optional dependency
    from agents import Agent, Runner
except ImportError:  # pragma: no cover - fallback when SDK absent
    Agent = Runner = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - fallback when SDK absent
    AsyncOpenAI = None  # type: ignore[assignment]


def _ensure_agents_available() -> None:
    if Agent is None or Runner is None:
        raise RuntimeError(
            "OpenAI Agents SDK is not installed. Install `openai-agents` to enable this integration."
        )


def _ensure_openai_available() -> None:
    if AsyncOpenAI is None:
        raise RuntimeError(
            "OpenAI Python client is not installed. Install `openai` to create API clients."
        )


@lru_cache(maxsize=1)
def get_async_openai_client() -> Any:
    """Return a cached AsyncOpenAI client configured from environment variables."""
    _ensure_openai_available()
    settings = get_settings()
    return AsyncOpenAI(  # type: ignore[call-arg]
        api_key=settings.openai_api_key,
        organization=settings.openai_organization,
        project=settings.openai_project,
    )


def create_agent(
    *,
    name: str,
    instructions: str,
    tools: Sequence[Any] | None = None,
    model: str | None = None,
) -> Any:
    """Construct an Agents SDK `Agent` with defaults sourced from settings."""
    _ensure_agents_available()
    settings = try_get_settings()
    agent_model = model or (settings.openai_agent_model if settings else None)
    if not agent_model:
        raise SettingsError(
            "OPENAI_AGENT_MODEL must be provided via environment or argument `model`."
        )
    return Agent(  # type: ignore[call-arg]
        name=name,
        instructions=instructions,
        model=agent_model,
        tools=list(tools or ()),
    )


@dataclass(frozen=True)
class RunnerOptions:
    """Options governing runner construction."""

    enable_tracing: bool = False
    tags: Iterable[str] | None = None


def create_runner(agent: Any, *, options: RunnerOptions | None = None, **kwargs: Any) -> Any:
    """Instantiate a `Runner` bound to the provided agent."""
    _ensure_agents_available()
    client = get_async_openai_client()
    runner_kwargs: dict[str, Any] = {"client": client, "agent": agent}
    runner_kwargs.update(kwargs)

    if options and options.enable_tracing:
        runner_kwargs.setdefault("enable_tracing", True)
        if options.tags:
            runner_kwargs.setdefault("tracing_tags", tuple(options.tags))

    return Runner(**runner_kwargs)  # type: ignore[call-arg]


__all__ = [
    "RunnerOptions",
    "create_agent",
    "create_runner",
    "get_async_openai_client",
]
