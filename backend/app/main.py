"""ASGI entrypoint for the Merak hiring agent backend."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.chatkit import router as chatkit_router
from app.api.health import router as health_router

app = FastAPI(title="Merak Agent API")

app.include_router(health_router)
app.include_router(chatkit_router)

__all__ = ["app"]
