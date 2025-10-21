"""Backward compatible re-export for legacy search helpers."""

from __future__ import annotations

from app.services.file_search import build_file_search_tool, build_merak_search_function

__all__ = ["build_file_search_tool", "build_merak_search_function"]
