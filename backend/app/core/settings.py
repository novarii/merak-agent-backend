"""Environment-backed configuration for the Merak backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Final

DEFAULT_AGENT_MODEL: Final[str] = "gpt-4o-mini"


class SettingsError(RuntimeError):
    """Raised when mandatory configuration is missing or malformed."""


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


@dataclass(frozen=True)
class Settings:
    """Centralized configuration for integrations and application defaults."""

    openai_api_key: str
    openai_agent_model: str = DEFAULT_AGENT_MODEL
    openai_organization: str | None = None
    openai_project: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        """Construct settings from environment variables, raising on missing values."""
        api_key = _optional_env("OPENAI_API_KEY")
        if not api_key:
            raise SettingsError("OPENAI_API_KEY must be set to interact with OpenAI Agents.")

        return cls(
            openai_api_key=api_key,
            openai_agent_model=_optional_env("OPENAI_AGENT_MODEL") or DEFAULT_AGENT_MODEL,
            openai_organization=_optional_env("OPENAI_ORG"),
            openai_project=_optional_env("OPENAI_PROJECT"),
        )


@lru_cache(maxsize=1)
def _load_settings() -> Settings:
    return Settings.from_env()


def get_settings() -> Settings:
    """Return cached settings, raising SettingsError when configuration is missing."""
    return _load_settings()


def try_get_settings() -> Settings | None:
    """Return settings when available, otherwise None without raising."""
    try:
        return _load_settings()
    except SettingsError:
        return None


__all__ = [
    "DEFAULT_AGENT_MODEL",
    "Settings",
    "SettingsError",
    "get_settings",
    "try_get_settings",
]
