"""FastAPI router exposing the ChatKit SSE endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.integrations.chatkit_server import MerakChatKitServer, get_chatkit_server
from app.core.settings import SettingsError

try:  # pragma: no cover - optional dependency
    from chatkit.server import StreamingResult
except ImportError:  # pragma: no cover - fallback when ChatKit not installed
    StreamingResult = None  # type: ignore[assignment]

router = APIRouter(tags=["chatkit"])


def _require_chatkit_server() -> MerakChatKitServer:
    try:
        server = get_chatkit_server()
    except SettingsError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ChatKit integration is disabled. Install the ChatKit SDK to enable streaming.",
        )
    return server


@router.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    server: MerakChatKitServer = Depends(_require_chatkit_server),
) -> Response:
    payload = await request.body()

    try:
        result = await server.process(payload, {"request": request})
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected failure while processing ChatKit payload.",
        ) from exc

    if StreamingResult is not None and isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    if isinstance(result, (bytes, bytearray)):
        return Response(content=bytes(result), media_type="application/octet-stream")
    return JSONResponse(result)
