"""ChatKit server wiring for the Merak hiring agent backend."""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional

from app.services.thread_store import ThreadStore

try:  # pragma: no cover - optional dependency
    from chatkit.server import ChatKitServer
    from chatkit.types import Attachment, ThreadMetadata, ThreadStreamEvent, UserMessageItem
except ImportError:  # pragma: no cover - fallback when ChatKit not installed
    ChatKitServer = None  # type: ignore[assignment]
    Attachment = ThreadMetadata = ThreadStreamEvent = UserMessageItem = None  # type: ignore[assignment]


class MerakChatKitServer(ChatKitServer):  # type: ignore[misc]
    """Thin wrapper around ChatKit's server to plug in Merak specific behavior."""

    def __init__(self, store: ThreadStore | None = None) -> None:
        if ChatKitServer is None:
            raise RuntimeError(
                "chatkit is not installed. Install `openai-chatkit` to enable chat streaming."
            )
        self.store = store or ThreadStore()
        super().__init__(self.store)

    async def respond(  # type: ignore[override]
        self,
        thread: ThreadMetadata,
        item: Optional[UserMessageItem],
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        raise NotImplementedError("Merak orchestrator agent has not been wired yet.")

    async def to_message_content(self, _input: Attachment) -> Any:  # type: ignore[override]
        raise RuntimeError("File attachments are not supported by the Merak backend.")


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
