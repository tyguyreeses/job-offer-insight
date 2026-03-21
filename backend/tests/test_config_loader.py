from __future__ import annotations

from pathlib import Path

import pytest

from configs.config_loader import load_app_config, resolve_config_path


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    monkeypatch.delenv("APP_CONFIG_PATH", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)


def test_load_app_config_uses_yaml_database_url(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
database:
  url: sqlite:///./custom.db
  echo: false
server:
  cors:
    allow_origins: [http://localhost:5173]
    allow_credentials: true
    allow_methods: ["*"]
    allow_headers: ["*"]
""".strip(),
        encoding="utf-8",
    )

    config = load_app_config(config_path)
    assert config.database.url == "sqlite:///./custom.db"


def test_load_app_config_prefers_database_url_env(monkeypatch, tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
database:
  url: sqlite:///./from-yaml.db
  echo: false
server:
  cors:
    allow_origins: [http://localhost:5173]
    allow_credentials: true
    allow_methods: ["*"]
    allow_headers: ["*"]
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("DATABASE_URL", "sqlite:///./from-env.db")
    config = load_app_config(config_path)
    assert config.database.url == "sqlite:///./from-env.db"


def test_resolve_config_path_prefers_app_config_path_env(monkeypatch, tmp_path: Path):
    custom_path = tmp_path / "app-config.yaml"
    monkeypatch.setenv("APP_CONFIG_PATH", str(custom_path))
    assert resolve_config_path() == custom_path


def test_load_app_config_fails_for_missing_file(tmp_path: Path):
    missing_path = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        load_app_config(missing_path)


def test_load_app_config_fails_for_invalid_schema(tmp_path: Path):
    config_path = tmp_path / "bad-config.yaml"
    config_path.write_text("database: {}", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid config schema"):
        load_app_config(config_path)
