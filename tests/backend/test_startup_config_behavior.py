from __future__ import annotations

from pathlib import Path

import pytest

from src.backend.main import build_app_from_config_path
from src.backend.utils.config_loader import ConfigLoadError

VALID_CONFIG = """\
app:
  name: "job-offer-insight"
  env: "dev"
  host: "127.0.0.1"
  port: 8000
  request_timeout_seconds: 30

logging:
  level: "INFO"
  json_logs: false
  include_timestamps: true

database:
  provider: "sqlite"
  path: "data/job_offer_insight.db"
  enable_wal: true
  timeout_seconds: 5

openai:
  api_key_env_var: "OPENAI_API_KEY"
  model: "gpt-5.2"
  transcription_model: "gpt-4o-mini-transcribe"
  timeout_seconds: 45
  max_retries: 2

workflow:
  enable_audio_intake: true
  enable_text_intake: true
  enable_missing_info_followups: true
  enable_non_monetary_summary: true
  allow_placeholder_comparisons: true

agents:
  text_parser:
    type: structured-output
    enabled: true
    model: "gpt-5.2"
    max_output_tokens: 1200
    prompt: "Return only a JSON object."
"""


def _write_config(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")


def test_app_builds_with_valid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "valid_config.yaml"
    _write_config(config_path, VALID_CONFIG)

    app = build_app_from_config_path(config_path=config_path, debug=False)

    assert app.title == "job-offer-insight"


def test_app_build_fails_with_invalid_config(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid_config.yaml"
    invalid_config = VALID_CONFIG.replace("openai:\n", "")
    _write_config(config_path, invalid_config)

    with pytest.raises(ConfigLoadError):
        build_app_from_config_path(config_path=config_path, debug=False)


def test_app_build_fails_when_agents_section_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "missing_agents_config.yaml"
    invalid_config = VALID_CONFIG.replace("\nagents:\n  text_parser:\n    type: structured-output\n    enabled: true\n    model: \"gpt-5.2\"\n    max_output_tokens: 1200\n    prompt: \"Return only a JSON object.\"\n", "")
    _write_config(config_path, invalid_config)

    with pytest.raises(ConfigLoadError):
        build_app_from_config_path(config_path=config_path, debug=False)


def test_app_build_fails_when_agent_type_is_invalid(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid_agent_type_config.yaml"
    invalid_config = VALID_CONFIG.replace("type: structured-output", "type: invalid")
    _write_config(config_path, invalid_config)

    with pytest.raises(ConfigLoadError):
        build_app_from_config_path(config_path=config_path, debug=False)
