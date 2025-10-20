"""ChatKit server wiring for the Merak hiring agent backend."""

from __future__ import annotations

import inspect
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Optional
from uuid import uuid4

from app.services.thread_store import ThreadStore
from merak_agents.merak.orchestrator import MerakAgentContext, create_merak_agent

try:  # pragma: no cover - optional dependency
    from agents import Runner
except ImportError:  # pragma: no cover - fallback when Agents SDK absent
    Runner = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from chatkit.agents import ThreadItemConverter, stream_agent_response
    from chatkit.server import ChatKitServer, ThreadItemDoneEvent
    from chatkit.types import (
        Attachment,
        ClientToolCallItem,
        HiddenContextItem,
        ThreadItem,
        ThreadMetadata,
        ThreadStreamEvent,
        UserMessageItem,
    )
except ImportError:  # pragma: no cover - fallback when ChatKit not installed
    ThreadItemConverter = stream_agent_response = None  # type: ignore[assignment]
    ThreadItemDoneEvent = None  # type: ignore[assignment]
    ChatKitServer = None  # type: ignore[assignment]
    Attachment = ClientToolCallItem = HiddenContextItem = ThreadItem = ThreadMetadata = None  # type: ignore[assignment]
    ThreadStreamEvent = UserMessageItem = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from agents import Agent
except ImportError:  # pragma: no cover
    Agent = None  # type: ignore[assignment]

if ChatKitServer is not None:

    class MerakChatKitServer(ChatKitServer):  # type: ignore[misc]
        """ChatKit server backed by the Merak orchestrator agent."""

        def __init__(self, store: ThreadStore | None = None) -> None:
            if ChatKitServer is None:
                raise RuntimeError(
                    "chatkit is not installed. Install `openai-chatkit` to enable chat streaming."
                )
            self.store = store or ThreadStore()
            super().__init__(self.store)
            self.assistant: Agent | None = None  # type: ignore[type-arg]
            self._thread_item_converter = self._init_thread_item_converter()

        # -- ChatKit hooks ------------------------------------------------
        async def respond(  # type: ignore[override]
            self,
            thread: ThreadMetadata,
            item: Optional[UserMessageItem],
            context: dict[str, Any],
        ) -> AsyncIterator[ThreadStreamEvent]:
            if Runner is None or stream_agent_response is None:
                raise RuntimeError(
                    "Merak orchestrator requires `openai-agents` and `openai-chatkit` to be installed."
                )

            agent = self._ensure_agent()
            if agent is None:
                raise RuntimeError("Merak orchestrator agent is not available.")

            agent_context = MerakAgentContext(  # type: ignore[call-arg]
                thread=thread,
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
                agent,
                agent_input,
                context=agent_context,
            )

            async for event in stream_agent_response(agent_context, result):
                yield event
            return

        async def to_message_content(self, _input: Attachment) -> Any:  # type: ignore[override]
            raise RuntimeError("File attachments are not supported by the Merak backend.")

        # -- Internal helpers --------------------------------------------
        def _ensure_agent(self) -> Agent | None:  # type: ignore[type-arg]
            if self.assistant is not None:
                return self.assistant
            try:
                self.assistant = create_merak_agent()
            except Exception as exc:  # pragma: no cover - defensive
                logging.getLogger(__name__).warning("Failed to create Merak agent: %s", exc)
                self.assistant = None
            return self.assistant

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
            if converter is not None:
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
                            next_param = params[1]
                            if next_param.kind in (
                                inspect.Parameter.POSITIONAL_ONLY,
                                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            ):
                                call_args.append(thread)
                            else:
                                call_kwargs[next_param.name] = thread

                    result = method(*call_args, **call_kwargs)
                    if inspect.isawaitable(result):
                        return await result
                    return result

            if isinstance(item, UserMessageItem):
                return _user_message_text(item)

            return None

        async def _add_hidden_item(
            self,
            thread: ThreadMetadata,
            context: dict[str, Any],
            content: str,
        ) -> None:
            if ThreadItemDoneEvent is None:
                return
            await self.store.add_thread_item(
                thread.id,
                HiddenContextItem(
                    id=_gen_id("msg"),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=content,
                ),
                context,
            )

else:  # pragma: no cover - fallback class for missing dependency

    class MerakChatKitServer:  # type: ignore[no-redef]
        def __init__(self, store: ThreadStore | None = None) -> None:
            raise RuntimeError(
                "chatkit is not installed. Install `openai-chatkit` to enable chat streaming."
            )


def _user_message_text(item: Any) -> str:
    parts: list[str] = []
    for part in getattr(item, "content", []):
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _is_tool_completion_item(item: Any) -> bool:
    return ClientToolCallItem is not None and isinstance(item, ClientToolCallItem)


_SERVER_SINGLETON: MerakChatKitServer | None = None


def create_chatkit_server(store: ThreadStore | None = None) -> MerakChatKitServer | None:
    """Instantiate the ChatKit server when dependencies are present."""
    if ChatKitServer is None:
        return None
    return MerakChatKitServer(store=store)


def get_chatkit_server() -> MerakChatKitServer | None:
    """Return a lazily-instantiated ChatKit server singleton."""
    global _SERVER_SINGLETON
    if _SERVER_SINGLETON is None:
        _SERVER_SINGLETON = create_chatkit_server()
    return _SERVER_SINGLETON


__all__ = ["MerakChatKitServer", "create_chatkit_server", "get_chatkit_server"]
