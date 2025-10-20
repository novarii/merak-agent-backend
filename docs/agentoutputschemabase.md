Agent output
AgentOutputSchemaBase
Bases: ABC

An object that captures the JSON schema of the output, as well as validating/parsing JSON produced by the LLM into the output type.

Source code in src/agents/agent_output.py
is_plain_text abstractmethod

is_plain_text() -> bool
Whether the output type is plain text (versus a JSON object).

Source code in src/agents/agent_output.py
name abstractmethod

name() -> str
The name of the output type.

Source code in src/agents/agent_output.py
json_schema abstractmethod

json_schema() -> dict[str, Any]
Returns the JSON schema of the output. Will only be called if the output type is not plain text.

Source code in src/agents/agent_output.py
is_strict_json_schema abstractmethod

is_strict_json_schema() -> bool
Whether the JSON schema is in strict mode. Strict mode constrains the JSON schema features, but guarantees valid JSON. See here for details: https://platform.openai.com/docs/guides/structured-outputs#supported-schemas

Source code in src/agents/agent_output.py
validate_json abstractmethod

validate_json(json_str: str) -> Any
Validate a JSON string against the output type. You must return the validated object, or raise a ModelBehaviorError if the JSON is invalid.

Source code in src/agents/agent_output.py
AgentOutputSchema dataclass
Bases: AgentOutputSchemaBase

An object that captures the JSON schema of the output, as well as validating/parsing JSON produced by the LLM into the output type.

Source code in src/agents/agent_output.py
output_type instance-attribute

output_type: type[Any] = output_type
The type of the output.

__init__

__init__(
    output_type: type[Any], strict_json_schema: bool = True
)
Parameters:

Name	Type	Description	Default
output_type	type[Any]	The type of the output.	required
strict_json_schema	bool	Whether the JSON schema is in strict mode. We strongly recommend setting this to True, as it increases the likelihood of correct JSON input.	True
Source code in src/agents/agent_output.py
is_plain_text

is_plain_text() -> bool
Whether the output type is plain text (versus a JSON object).

Source code in src/agents/agent_output.py
is_strict_json_schema

is_strict_json_schema() -> bool
Whether the JSON schema is in strict mode.

Source code in src/agents/agent_output.py
json_schema

json_schema() -> dict[str, Any]
The JSON schema of the output type.

Source code in src/agents/agent_output.py
validate_json

validate_json(json_str: str) -> Any
Validate a JSON string against the output type. Returns the validated object, or raises a ModelBehaviorError if the JSON is invalid.

Source code in src/agents/agent_output.py
name

name() -> str
The name of the output type.

Source code in src/agents/agent_output.py
