"""Configuration loading and validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .config_types import RuntimeConfig


class ConfigLoadError(RuntimeError):
    """Raised when runtime configuration cannot be loaded safely."""


def _format_validation_error(exc: ValidationError) -> str:
    lines: list[str] = ["Configuration validation failed:"]
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        lines.append(f"- {location}: {error['msg']}")
    return "\n".join(lines)


def _read_yaml_config(config_path: Path) -> dict[str, Any]:
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigLoadError(f"Unable to read config file '{config_path}': {exc}") from exc

    try:
        payload = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML in config file '{config_path}': {exc}") from exc

    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ConfigLoadError(
            f"Config file '{config_path}' must contain a top-level mapping/object."
        )

    return payload


def load_config(config_path: str | Path) -> RuntimeConfig:
    """Load, parse, and validate runtime config from a YAML file path."""
    resolved_path = Path(config_path)
    if not resolved_path.exists():
        raise ConfigLoadError(f"Config file not found: '{resolved_path}'")
    if not resolved_path.is_file():
        raise ConfigLoadError(f"Config path is not a file: '{resolved_path}'")

    payload = _read_yaml_config(resolved_path)
    try:
        return RuntimeConfig.model_validate(payload)
    except ValidationError as exc:
        raise ConfigLoadError(_format_validation_error(exc)) from exc


def load_default_config() -> RuntimeConfig:
    """Load default config from `src/config.yaml`."""
    default_path = Path(__file__).resolve().parents[2] / "config.yaml"
    return load_config(default_path)
