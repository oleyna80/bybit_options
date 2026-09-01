"""Logging configuration for the application."""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    """Configure root logging from LOG_LEVEL env var."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
