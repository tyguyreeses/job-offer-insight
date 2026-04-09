from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.domain.services.offer_service import Stage4OfferService
from src.backend.gen_ai.audio_transcriber import AudioTranscriptionError
from src.backend.main import create_app
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


class DeterministicParser:
    def parse(self, text: str) -> dict[str, Any]:
        assert text == "Transcribed offer details"
        return {
            "company_name": "Aurora Dynamics",
            "role_title": "ML Engineer",
            "compensation": {"annual_base_salary_usd": 172000},
        }


class DeterministicTranscriber:
    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        assert audio_bytes == b"fake audio bytes"
        assert filename == "offer.wav"
        return "Transcribed offer details"


class BrokenTranscriber:
    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        raise AudioTranscriptionError("upstream provider timeout")


class MissingRequiredParser:
    def parse(self, text: str) -> dict[str, Any]:
        return {
            "role_title": "ML Engineer",
            "compensation": {"annual_base_salary_usd": 172000},
        }


def _build_app_with_overrides(
    tmp_path: Path,
    *,
    parser: Any,
    transcriber: Any,
) -> TestClient:
    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage5_offer_audio_test.db"),
            "enable_wal": False,
        }
    )
    config = config.model_copy(update={"database": database_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    service = Stage4OfferService(
        offer_repository=container.offer_repository,
        text_parser_agent=parser,
        audio_transcriber=transcriber,
    )
    app = create_app(replace(container, offer_service=service))
    return TestClient(app)


def _post_audio_intake(
    client: TestClient,
    *,
    omission_confirmations: dict[str, bool] | None = None,
) -> dict[str, Any]:
    data = {}
    if omission_confirmations is not None:
        data["omission_confirmations_json"] = json.dumps(omission_confirmations)

    response = client.post(
        "/api/v1/offers/intake/audio",
        data=data,
        files={"audio_file": ("offer.wav", b"fake audio bytes", "audio/wav")},
    )
    assert response.status_code == 200
    return response.json()


def test_audio_happy_path_routes_to_existing_intake_pipeline(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=DeterministicTranscriber(),
    )

    first = _post_audio_intake(client)
    assert first["status"] == "missing_information"
    omission_confirmations = {
        prompt["path"]: True
        for prompt in first["missing_field_prompts"]
        if not prompt["required"]
    }

    saved = _post_audio_intake(client, omission_confirmations=omission_confirmations)
    assert saved["status"] == "saved"
    offer = saved["offer"]
    assert offer is not None
    assert offer["company_name"] == "Aurora Dynamics"
    assert offer["offer_meta"]["source_input_type"] == "audio"


def test_audio_transcription_failure_is_observable(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=BrokenTranscriber(),
    )

    payload = _post_audio_intake(client)
    assert payload["status"] == "transcription_failed"
    assert payload["offer"] is None
    assert "Unable to transcribe audio input" in payload["errors"][0]


def test_audio_path_preserves_required_field_validation_contract(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=MissingRequiredParser(),
        transcriber=DeterministicTranscriber(),
    )

    payload = _post_audio_intake(client)
    assert payload["status"] == "blocked_required_fields"
    assert payload["offer"] is None
    assert "company_name is required" in payload["errors"]
