FunctionToolResult dataclass
tool instance-attribute

tool: FunctionTool
The tool that was run.

output instance-attribute

output: Any
The output of the tool.

run_item instance-attribute

run_item: RunItem
The run item that was produced as a result of the tool call.

FunctionTool dataclass
A tool that wraps a function. In most cases, you should use the function_tool helpers to create a FunctionTool, as they let you easily wrap a Python function.

Source code in src/agents/tool.py
name instance-attribute

name: str
The name of the tool, as shown to the LLM. Generally the name of the function.

description instance-attribute

description: str
A description of the tool, as shown to the LLM.

params_json_schema instance-attribute

params_json_schema: dict[str, Any]
The JSON schema for the tool's parameters.

on_invoke_tool instance-attribute

on_invoke_tool: Callable[
    [ToolContext[Any], str], Awaitable[Any]
]
A function that invokes the tool with the given context and parameters. The params passed are: 1. The tool run context. 2. The arguments from the LLM, as a JSON string.

You must return a one of the structured tool output types (e.g. ToolOutputText, ToolOutputImage, ToolOutputFileContent) or a string representation of the tool output, or a list of them, or something we can call str() on. In case of errors, you can either raise an Exception (which will cause the run to fail) or return a string error message (which will be sent back to the LLM).

strict_json_schema class-attribute instance-attribute

strict_json_schema: bool = True
Whether the JSON schema is in strict mode. We strongly recommend setting this to True, as it increases the likelihood of correct JSON input.

is_enabled class-attribute instance-attribute

is_enabled: (
    bool
    | Callable[
        [RunContextWrapper[Any], AgentBase],
        MaybeAwaitable[bool],
    ]
) = True
Whether the tool is enabled. Either a bool or a Callable that takes the run context and agent and returns whether the tool is enabled. You can use this to dynamically enable/disable a tool based on your context/state.

tool_input_guardrails class-attribute instance-attribute

tool_input_guardrails: (
    list[ToolInputGuardrail[Any]] | None
) = None
Optional list of input guardrails to run before invoking this tool.

tool_output_guardrails class-attribute instance-attribute

tool_output_guardrails: (
    list[ToolOutputGuardrail[Any]] | None
) = None
Optional list of output guardrails to run after invoking this tool.

FileSearchTool dataclass
A hosted tool that lets the LLM search through a vector store. Currently only supported with OpenAI models, using the Responses API.

Source code in src/agents/tool.py
vector_store_ids instance-attribute

vector_store_ids: list[str]
The IDs of the vector stores to search.

max_num_results class-attribute instance-attribute

max_num_results: int | None = None
The maximum number of results to return.

include_search_results class-attribute instance-attribute

include_search_results: bool = False
Whether to include the search results in the output produced by the LLM.

