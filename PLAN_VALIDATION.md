Workflow Assessment

  - Docs in docs/tools.md and docs/agents_as_tools_example.py confirm our workflow should use the “agents-as-tools” pattern: the orchestrator
    keeps the conversation while invoking specialists (agent.as_tool(...)).
  - After updating the plan, Merak must list the Searcher in its tools array so it invokes searcher_agent.as_tool("search_agents", ...). No
    return a structured summary + raw results. That lines up with AgentOutputSchema expectations described in docs/agentoutputschemabase.md.

  Searcher → File Search Bridge

  - Implement app/services/search.py with build_file_search_tool() returning a @function_tool that accepts query, industry, agent_type,
    max_rate, min_success_rate, availability, max_results.
  - Inside the Searcher agent (likely agents/merak/searcher.py):

    search_agents_tool = build_file_search_tool(client, settings.vector_store_id)

    searcher_agent = Agent(
        name="searcher",
        instructions="Normalize filters into AgentFilterPayload and call search_agents...",
        output_type=AgentFilterPayload,
        tools=[search_agents_tool],
    )
  - When the agent finishes, call payload.build_attribute_filter() and pass the pieces to search_agents. The tool handles the final OpenAI
    vector_stores.search call so parameter mapping stays centralized.

  Orchestrator Invocation

  - Define Merak with the Searcher tool:

    merak_agent = Agent(
        name="merak",
        instructions="Collect filters, then call search_agents when ready...",
        tools=[searcher_agent.as_tool(
            tool_name="search_agents",
            tool_description="Normalize filters and retrieve candidate matches",
        )],
    )
  - Merak prompts LLM to gather base_rate, success_rate, availability, industry, agent_type; once complete it invokes search_agents with the
    structured brief. The Searcher runs, calls the function tool, and returns results; Merak then summarizes for the user.

Search. The change is on the Searcher’s output: its AgentOutputSchema should be something like SearchResults (Phase 4 already calls for app/
schemas/search_results.py). Inside the Searcher agent you:

- Accept Merak’s brief, build an AgentFilterPayload to call payload.build_attribute_filter() and pass the pieces into search_agents.
- Capture the vector-store response and map it into your SearchResults model (matches, scores, supporting metadata).
- Return only that SearchResults payload to Merak.

Merak stays the conversational owner, gets back a clean result set to summarize for the user, while AgentFilterPayload remains purely an
internal helper to keep filter construction consistent with the plan.