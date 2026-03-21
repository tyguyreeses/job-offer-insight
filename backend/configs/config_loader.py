from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from .config_types import AppConfig

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.yaml")


def resolve_config_path() -> Path:
    configured_path = os.getenv("APP_CONFIG_PATH")
    return Path(configured_path) if configured_path else DEFAULT_CONFIG_PATH


def load_app_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or resolve_config_path()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at: {path}")

    try:
        raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML config at {path}: {exc}") from exc

    if raw_data is None:
        raw_data = {}

    try:
        config = AppConfig.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(f"Invalid config schema at {path}: {exc}") from exc

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        config = config.model_copy(
            update={
                "database": config.database.model_copy(update={"url": database_url}),
            }
        )

    return config
