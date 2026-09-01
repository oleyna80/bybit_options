"""Application settings (placeholder)."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Centralized settings holder."""

    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def load_settings() -> Settings:
    """Load settings from environment."""
    return Settings()
