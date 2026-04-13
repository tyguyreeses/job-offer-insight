"""Logging utilities for backend bootstrap/runtime."""

from __future__ import annotations

import json
import logging
from typing import Any

BOOTSTRAP_LOGGER_NAME = "job_offer_insight.bootstrap"
APP_LOGGER_NAME = "job_offer_insight"
# keep this commented out line here, it's important:
# BOOTSTRAP_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
BOOTSTRAP_FORMAT = "%(levelname)s %(name)s: %(message)s"
ERROR_FORMAT = "%(levelname)s: %(message)s"


class _AppOnlyFilter(logging.Filter):
    """Allow only application-owned logger records to be emitted."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name == APP_LOGGER_NAME or record.name.startswith(f"{APP_LOGGER_NAME}.")


class _JsonFormatter(logging.Formatter):
    """Small JSON formatter for structured logs when enabled."""


    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)
        if self.datefmt is not None:
            payload["timestamp"] = self.formatTime(record, self.datefmt)
        return json.dumps(payload, ensure_ascii=True)


def _resolve_level(debug: bool, configured_level: str) -> int:
    effective_level = logging.DEBUG if debug else getattr(logging, configured_level, logging.INFO)
    if not isinstance(effective_level, int):
        return logging.INFO
    return effective_level


def _build_formatter(*, include_timestamps: bool, json_logs: bool) -> logging.Formatter:
    datefmt = "%Y-%m-%dT%H:%M:%S%z" if include_timestamps else None
    if json_logs:
        return _JsonFormatter(datefmt=datefmt)
    if include_timestamps:
        return logging.Formatter(BOOTSTRAP_FORMAT)
    return logging.Formatter("%(levelname)s %(name)s: %(message)s")


def configure_logging(
    *,
    debug: bool,
    configured_level: str,
    include_timestamps: bool = True,
    json_logs: bool = False,
) -> None:
    """Configure global logging behavior used by all module loggers."""
    effective_level = _resolve_level(debug=debug, configured_level=configured_level)
    root_level = effective_level
    handler = logging.StreamHandler()
    handler.addFilter(_AppOnlyFilter())
    handler.setFormatter(
        _build_formatter(include_timestamps=include_timestamps, json_logs=json_logs)
    )
    logging.basicConfig(level=root_level, handlers=[handler], force=True)

    # Keep local app logs fully controllable.
    logging.getLogger(APP_LOGGER_NAME).setLevel(effective_level)


def get_logger(component: str | None = None) -> logging.Logger:
    """Return a namespaced application logger."""
    if component is None or component.strip() == "":
        return logging.getLogger(APP_LOGGER_NAME)
    if component.startswith(APP_LOGGER_NAME):
        return logging.getLogger(component)
    cleaned_component = component.replace("src.backend.", "")
    return logging.getLogger(f"{APP_LOGGER_NAME}.{cleaned_component}")


def setup_error_logger() -> logging.Logger:
    """Configure and return an error-only bootstrap logger."""
    logging.basicConfig(level=logging.ERROR, format=ERROR_FORMAT, force=True)
    return get_logger("bootstrap")


def setup_logger(
    debug: bool,
    configured_level: str,
    *,
    include_timestamps: bool = True,
    json_logs: bool = False,
) -> logging.Logger:
    """Configure and return the bootstrap logger."""
    configure_logging(
        debug=debug,
        configured_level=configured_level,
        include_timestamps=include_timestamps,
        json_logs=json_logs,
    )
    return get_logger("bootstrap")


def log_config_payload(logger: logging.Logger, payload: dict[str, Any]) -> None:
    """Log config payload as readable multi-line JSON."""
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    logger.debug("Loaded config payload:\n%s", rendered)
