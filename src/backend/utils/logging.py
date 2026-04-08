"""Logging utilities for backend bootstrap/runtime."""

from __future__ import annotations

import json
import logging
from typing import Any

BOOTSTRAP_LOGGER_NAME = "job_offer_insight.bootstrap"
BOOTSTRAP_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
ERROR_FORMAT = "%(levelname)s: %(message)s"


def setup_error_logger() -> logging.Logger:
    """Configure and return an error-only bootstrap logger."""
    logging.basicConfig(level=logging.ERROR, format=ERROR_FORMAT)
    return logging.getLogger(BOOTSTRAP_LOGGER_NAME)


def setup_logger(debug: bool, configured_level: str) -> logging.Logger:
    """Configure and return the bootstrap logger."""
    effective_level = logging.DEBUG if debug else getattr(logging, configured_level, logging.INFO)
    logging.basicConfig(
        level=effective_level,
        format=BOOTSTRAP_FORMAT,
    )
    return logging.getLogger(BOOTSTRAP_LOGGER_NAME)


def log_config_payload(logger: logging.Logger, payload: dict[str, Any]) -> None:
    """Log config payload as readable multi-line JSON."""
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    logger.debug("Loaded config payload:\n%s", rendered)
