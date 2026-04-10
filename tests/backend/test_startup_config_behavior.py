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
  accepted_audio_extensions: [".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"]
  timeout_seconds: 45
  max_retries: 2

workflow:
  enable_audio_intake: true
  enable_text_intake: true
  enable_missing_info_followups: true
  enable_non_monetary_summary: true
  allow_placeholder_comparisons: true

agents:
  entry_creation:
    type: non-structured
    enabled: true
    model: "gpt-5.2"
    max_output_tokens: 500
    prompt: "You are a helper."
  parse_entry:
    type: structured-output
    enabled: true
    model: "gpt-5.2"
    max_output_tokens: 1200
    prompt: "Return only a JSON object."

offer_schema:
  version: 1
  identity:
    company_name_path: "company_name"
    role_title_path: "role_title"
  required:
    all_of: ["company-name", "role-title", "location"]
    one_of:
      - ["annual-base-salary-usd"]
      - ["hourly-rate-usd", "hours-per-week"]
  card_sections:
    - section_id: "salary"
      title: "Salary"
    - section_id: "monetary"
      title: "Monetary benefits"
    - section_id: "non_monetary"
      title: "Non-monetary benefits"
    - section_id: "meta"
      title: "Date created"
  edit_sections:
    - section_id: "core"
      title: "Core details"
    - section_id: "compensation"
      title: "Compensation"
    - section_id: "monetary"
      title: "Monetary benefits"
    - section_id: "non_monetary"
      title: "Non-monetary benefits"
  fields:
    - id: "company-name"
      label: "Company name"
      storage_path: "company_name"
      data_type: "string"
      group: "core"
      required: true
      default_when_omitted: ""
      card: { visible: false, section_id: "salary", order: 0, style: "labeled_value" }
      edit: { visible: true, section_id: "core", order: 1, widget: "text" }
    - id: "role-title"
      label: "Role title"
      storage_path: "role_title"
      data_type: "string"
      group: "core"
      required: true
      default_when_omitted: ""
      card: { visible: false, section_id: "salary", order: 0, style: "labeled_value" }
      edit: { visible: true, section_id: "core", order: 2, widget: "text" }
    - id: "location"
      label: "Location"
      storage_path: "location"
      data_type: "string"
      group: "core"
      required: true
      default_when_omitted: ""
      card: { visible: false, section_id: "salary", order: 0, style: "labeled_value" }
      edit: { visible: true, section_id: "core", order: 3, widget: "text" }
    - id: "annual-base-salary-usd"
      label: "Annual base salary"
      storage_path: "compensation.annual_base_salary_usd"
      data_type: "number"
      group: "compensation"
      card: { visible: true, section_id: "salary", order: 1, style: "value" }
      edit: { visible: true, section_id: "compensation", order: 1, widget: "number" }
    - id: "hourly-rate-usd"
      label: "Hourly rate"
      storage_path: "compensation.hourly_rate_usd"
      data_type: "number"
      group: "compensation"
      card: { visible: false, section_id: "salary", order: 2, style: "labeled_value" }
      edit: { visible: true, section_id: "compensation", order: 2, widget: "number" }
    - id: "hours-per-week"
      label: "Hours per week"
      storage_path: "compensation.hours_per_week"
      data_type: "number"
      group: "compensation"
      card: { visible: false, section_id: "salary", order: 3, style: "labeled_value" }
      edit: { visible: true, section_id: "compensation", order: 3, widget: "number" }
  migrations: []
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
    invalid_config = VALID_CONFIG.replace(
        "\nagents:\n  entry_creation:\n    type: non-structured\n    enabled: true\n    model: \"gpt-5.2\"\n    max_output_tokens: 500\n    prompt: \"You are a helper.\"\n  parse_entry:\n    type: structured-output\n    enabled: true\n    model: \"gpt-5.2\"\n    max_output_tokens: 1200\n    prompt: \"Return only a JSON object.\"\n",
        "",
    )
    _write_config(config_path, invalid_config)

    with pytest.raises(ConfigLoadError):
        build_app_from_config_path(config_path=config_path, debug=False)


def test_app_build_fails_when_agent_type_is_invalid(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid_agent_type_config.yaml"
    invalid_config = VALID_CONFIG.replace("type: non-structured", "type: invalid", 1)
    _write_config(config_path, invalid_config)

    with pytest.raises(ConfigLoadError):
        build_app_from_config_path(config_path=config_path, debug=False)
