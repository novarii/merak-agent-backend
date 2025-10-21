"""Interactive REPL for chatting with the Merak agent via run_demo_loop."""

from __future__ import annotations

import asyncio

from app.agents.orchestrator import (
    MERAK_SEARCH_TOOL_DESCRIPTION,
    MERAK_SEARCH_TOOL_NAME,
    build_merak_orchestrator,
)
from app.core.settings import SettingsError, get_settings
from app.services.file_search import build_file_search_tool, build_merak_search_function

try:  # pragma: no cover - optional dependency
    from agents import run_demo_loop
except ImportError:  # pragma: no cover - surface a helpful runtime error
    run_demo_loop = None  # type: ignore[assignment]


def build_merak_agent() -> any:
    """Construct the Merak agent configured for interactive demos."""
    settings = get_settings()
    file_search_tool = build_file_search_tool(settings=settings)
    search_tool = build_merak_search_function(
        file_search_tool,
        tool_name=MERAK_SEARCH_TOOL_NAME,
        tool_description=MERAK_SEARCH_TOOL_DESCRIPTION,
    )
    return build_merak_orchestrator(search_tool, model=settings.openai_agent_model)


async def main() -> None:
    """Start an interactive REPL session with Merak."""
    if run_demo_loop is None:
        raise RuntimeError(
            "openai-agents-python must be installed to run the demo loop. "
            "Install `openai-agents` and try again."
        )

    agent = build_merak_agent()
    print("Starting Merak demo loop. Type 'quit' or 'exit' (or Ctrl-D) to leave.")
    await run_demo_loop(agent)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SettingsError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc
