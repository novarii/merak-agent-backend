"""Backward compatible re-export for the legacy search helper."""

from __future__ import annotations

from app.services.file_search import build_file_search_tool

__all__ = ["build_file_search_tool"]
