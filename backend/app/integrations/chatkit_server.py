"""ChatKit server wiring for the Merak hiring agent backend.

The implementation mirrors the ChatKit demo backend but trims features to match
Merak's current needs:

- stores conversation state in ``ThreadStore`` so sessions persist in memory.
- wraps the Merak orchestrator agent and streams responses via ChatKit.
- uses an ``AgentContext`` / ``RunContextWrapper`` bridge so the orchestrator
  retains access to thread metadata, matching the example implementation.
"""

from __future__ import annotations

import inspect
from typing import Annotated, Any, AsyncIterator, Optional

from pydantic import ConfigDict, Field

from app.agents.orchestrator import (
    MERAK_SEARCH_TOOL_NAME,
    build_merak_orchestrator,
)
from app.agents.searcher import (
    SEARCHER_TOOL_DESCRIPTION,
    build_searcher_agent,
)
from app.core.settings import SettingsError, get_settings
from app.services.search import build_file_search_tool
from app.services.thread_store import ThreadStore

try:  # pragma: no cover - optional dependency
    from agents import Agent, Runner
except ImportError:  # pragma: no cover
    Agent = Runner = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from chatkit.agents import AgentContext, ThreadItemConverter, stream_agent_response
    from chatkit.server import ChatKitServer
    from chatkit.types import (
        Attachment,
        ClientToolCallItem,
        ThreadItem,
        ThreadMetadata,
        ThreadStreamEvent,
        UserMessageItem,
    )
except ImportError:  # pragma: no cover
    AgentContext = ThreadItemConverter = stream_agent_response = None  # type: ignore[assignment]
    ChatKitServer = None  # type: ignore[assignment]
    Attachment = ClientToolCallItem = ThreadItem = ThreadMetadata = None  # type: ignore[assignment]
    ThreadStreamEvent = UserMessageItem = None  # type: ignore[assignment]


def _is_tool_completion_item(item: Any) -> bool:
    """Return True when the ChatKit item represents a completed tool call."""
    if ClientToolCallItem is None:
        return False
    return isinstance(item, ClientToolCallItem)


if AgentContext is not None:

    class MerakAgentContext(AgentContext):
        """Context passed to the Merak orchestrator via RunContextWrapper."""

        model_config = ConfigDict(arbitrary_types_allowed=True)
        store: Annotated[ThreadStore, Field(exclude=True)]
        request_context: dict[str, Any]

else:  # pragma: no cover - define placeholder for type checking when ChatKit missing

    class MerakAgentContext:  # type: ignore[too-many-ancestors]
        pass


class MerakChatKitServer(ChatKitServer):  # type: ignore[misc]
    """Thin wrapper around ChatKit's server to plug in Merak specific behavior."""

    def __init__(
        self,
        assistant: Agent | None = None,
        store: ThreadStore | None = None,
    ) -> None:
        if ChatKitServer is None:
            raise RuntimeError(
                "chatkit is not installed. Install `openai-chatkit` to enable chat streaming."
            )
        self.store = store or ThreadStore()
        super().__init__(self.store)
        self.assistant: Agent | None = assistant
        self._thread_item_converter = self._init_thread_item_converter()

    async def respond(  # type: ignore[override]
        self,
        thread: ThreadMetadata,
        item: Optional[UserMessageItem],
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        if Runner is None or AgentContext is None or stream_agent_response is None:
            raise RuntimeError(
                "openai-agents-python and openai-chatkit are required to stream responses."
            )
        if self.assistant is None:
            raise RuntimeError("Merak orchestrator agent has not been configured on the server.")

        agent_context = MerakAgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None or _is_tool_completion_item(target_item):
            return

        agent_input = await self._to_agent_input(thread, target_item)
        if agent_input is None:
            return

        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event
        return

    async def to_message_content(self, _input: Attachment) -> Any:  # type: ignore[override]
        raise RuntimeError("File attachments are not supported by the Merak backend.")

    def _init_thread_item_converter(self) -> Any | None:
        converter_cls = ThreadItemConverter
        if converter_cls is None or not callable(converter_cls):
            return None

        attempts: tuple[dict[str, Any], ...] = (
            {"to_message_content": self.to_message_content},
            {"message_content_converter": self.to_message_content},
            {},
        )

        for kwargs in attempts:
            try:
                return converter_cls(**kwargs)
            except TypeError:
                continue
        return None

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        try:
            items = await self.store.load_thread_items(thread.id, None, 1, "desc", context)
        except Exception:  # pragma: no cover - defensive
            return None

        return items.data[0] if getattr(items, "data", None) else None

    async def _to_agent_input(
        self,
        thread: ThreadMetadata,
        item: ThreadItem,
    ) -> Any | None:
        if _is_tool_completion_item(item):
            return None

        converter = getattr(self, "_thread_item_converter", None)
        if converter is None:
            return item

        for attr in (
            "to_input_item",
            "convert",
            "convert_item",
            "convert_thread_item",
        ):
            method = getattr(converter, attr, None)
            if method is None:
                continue

            call_args: list[Any] = [item]
            call_kwargs: dict[str, Any] = {}

            try:
                signature = inspect.signature(method)
            except (TypeError, ValueError):
                signature = None

            if signature is not None:
                params = [
                    parameter
                    for parameter in signature.parameters.values()
                    if parameter.kind
                    not in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                    )
                ]
                if len(params) >= 2:
                    call_args.append(thread)
                if len(params) >= 3:
                    call_kwargs["store"] = self.store

            try:
                return await method(*call_args, **call_kwargs)  # type: ignore[misc]
            except TypeError:
                continue
        return item


_ASSISTANT_SINGLETON: Agent | None = None
_SERVER_SINGLETON: MerakChatKitServer | None = None


def _build_default_assistant() -> Agent | None:
    """Construct Merak's orchestrator agent with the Searcher tool attached."""
    if Agent is None:
        return None

    settings = get_settings()
    if not settings.openai_vector_store_id:
        raise SettingsError(
            "OPENAI_VECTOR_STORE_ID must be set to enable Merak's semantic search."
        )

    file_search_tool = build_file_search_tool(
        vector_store_id=settings.openai_vector_store_id,
        max_results=10,
    )

    searcher_agent = build_searcher_agent(
        file_search_tool,
        model=settings.openai_agent_model,
    )

    searcher_tool = searcher_agent.as_tool(  # type: ignore[assignment]
        tool_name=MERAK_SEARCH_TOOL_NAME,
        tool_description=SEARCHER_TOOL_DESCRIPTION,
    )

    return build_merak_orchestrator(
        searcher_tool,
        model=settings.openai_agent_model,
    )


def get_merak_assistant() -> Agent | None:
    """Return a cached instance of the Merak orchestrator agent."""
    global _ASSISTANT_SINGLETON
    if _ASSISTANT_SINGLETON is None:
        _ASSISTANT_SINGLETON = _build_default_assistant()
    return _ASSISTANT_SINGLETON


def create_chatkit_server(
    assistant: Agent | None = None,
    store: ThreadStore | None = None,
) -> MerakChatKitServer | None:
    """Instantiate the ChatKit server when dependencies are present."""
    if ChatKitServer is None:
        return None
    if assistant is None:
        assistant = get_merak_assistant()
    return MerakChatKitServer(assistant=assistant, store=store)


def get_chatkit_server() -> MerakChatKitServer | None:
    """Return a lazily-instantiated ChatKit server singleton."""
    global _SERVER_SINGLETON
    if _SERVER_SINGLETON is None:
        _SERVER_SINGLETON = create_chatkit_server()
    return _SERVER_SINGLETON


__all__ = [
    "MerakAgentContext",
    "MerakChatKitServer",
    "create_chatkit_server",
    "get_chatkit_server",
    "get_merak_assistant",
]
