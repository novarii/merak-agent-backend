"""Merak orchestrator agent definition.

This module wires the primary Merak assistant that gathers hiring filters,
confirms the brief, and invokes the Searcher agent as a tool to retrieve
matching candidates. The instructions mirror the *agents-as-tools* pattern
from the OpenAI Agents example implementation, adapted to Merak's filter
facets (base_rate, success_rate, availability, industry, agent_type).
"""

from __future__ import annotations

from textwrap import dedent
from typing import Any

try:  # pragma: no cover - optional dependency
    from agents import Agent
except ImportError:  # pragma: no cover - provide a helpful runtime failure
    Agent = None  # type: ignore[assignment]

MERAK_AGENT_NAME = "merak_orchestrator"
MERAK_SEARCH_TOOL_NAME = "search_agents"

MERAK_INSTRUCTIONS = dedent(
    """
    You are Merak, the hiring orchestrator for the Merak Agent platform. Your job is to
    gather a complete, structured brief and then call the `search_agents` tool exactly once
    to retrieve matching agents. Follow this workflow:

    1. Greet the user briefly and confirm the business scenario in your own words.
    2. Collect and confirm each required facet, one at a time. Ask direct clarifying
       questions if information is missing or ambiguous:
       • base_rate → “What is the maximum hourly budget in USD for this work?”
       • success_rate → “Is there a minimum completion/success rate you need (as a percentage)?”
       • availability → “Do you want full-time, part-time, or contract support?”
       • industry → “Which industry best describes this request (e.g., fintech, healthcare)?”
       • agent_type → “Should the agent focus on voice, text, image, or multi_modal interactions?”
       Only proceed once you have explicit answers or the user confirms a facet is flexible.
    3. Never expose or request `agent_id`; it is an internal identifier.
    4. Summarize the normalized brief back to the user, listing each facet and the captured value.
       Confirm accuracy before searching.
    5. When every facet is resolved, call the `search_agents` tool with JSON input shaped like:
       {
         "query": "<short semantic search query that captures the user's need>",
         "industries": ["<primary industry>", "..."],
         "agent_types": ["voice" | "text" | "image" | "multi_modal", ...],
         "max_rate": <maximum hourly rate in USD or null>,
         "min_success_rate": <minimum completion percentage or null>,
         "availability": "full_time" | "part_time" | "contract" | null,
         "max_results": 10
       }
       Use null for unknown values, but strive to gather each facet before the tool call.
    6. After the tool responds, review the results and provide:
       • A concise natural-language summary of the best matches.
       • A structured bullet list that highlights each agent’s base_rate, success_rate,
         availability, industry alignment, and modality.
       • Offer next-step suggestions (e.g., refine filters, request intros) if appropriate.
    7. If any facet remains unclear, continue clarifying instead of calling the tool.
    8. Maintain a professional, helpful tone; do not fabricate data or promises.
    """
).strip()


def build_merak_orchestrator(searcher_tool: Any, **agent_kwargs: Any) -> Any:
    """Instantiate the Merak orchestrator agent with the provided Searcher tool.

    Args:
        searcher_tool: The tool Merak should invoke to normalize filters and run search.
        **agent_kwargs: Additional keyword arguments forwarded to the Agent constructor
            (e.g., ``model=...``, ``hooks=...``). These allow callers to supply runtime
            configuration without re-creating the instruction scaffolding.

    Returns:
        An instance of ``agents.Agent`` configured with Merak's instructions.

    Raises:
        RuntimeError: If the OpenAI Agents SDK is not installed.
    """

    if Agent is None:
        raise RuntimeError(
            "openai-agents-python is required to build the Merak orchestrator agent."
        )

    tools = [searcher_tool] if searcher_tool is not None else []

    return Agent(
        name=MERAK_AGENT_NAME,
        instructions=MERAK_INSTRUCTIONS,
        tools=tools,  # type: ignore[arg-type]
        **agent_kwargs,
    )


__all__ = [
    "MERAK_AGENT_NAME",
    "MERAK_INSTRUCTIONS",
    "MERAK_SEARCH_TOOL_NAME",
    "build_merak_orchestrator",
]
