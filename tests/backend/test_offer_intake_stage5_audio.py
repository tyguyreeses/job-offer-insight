from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.domain.offer_schema import build_configured_offer_schema
from src.backend.domain.services.offer_service import Stage4OfferService
from src.backend.gen_ai.audio_transcriber import AudioTranscriptionError
from src.backend.main import create_app
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


class DeterministicParser:
    def parse(self, text: str) -> dict[str, Any]:
        if text == "audio turn one":
            return {
                "company_name": "Aurora Dynamics",
                "role_title": "ML Engineer",
                "location": "Denver, CO",
                "compensation": {"annual_base_salary_usd": 172000},
            }
        if text == "audio final detail":
            return {"non_monetary_benefits": {"culture_notes": "Collaborative team"}}
        return {}


class MissingRequiredParser:
    def parse(self, text: str) -> dict[str, Any]:
        _ = text
        return {
            "role_title": "ML Engineer",
        }


class DeterministicTranscriber:
    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        _ = filename
        _ = content_type
        if audio_bytes == b"turn-one":
            return "audio turn one"
        if audio_bytes == b"turn-two":
            return "audio final detail"
        return ""


class BrokenTranscriber:
    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        _ = audio_bytes
        _ = filename
        _ = content_type
        raise AudioTranscriptionError("upstream provider timeout")


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
        offer_schema=build_configured_offer_schema(config.offer_schema),
        tax_config=config.tax_profile,
    )
    app = create_app(replace(container, offer_service=service))
    return TestClient(app)


def _post_audio_turn(
    client: TestClient,
    *,
    action: str,
    session_id: str | None = None,
    audio_bytes: bytes | None = None,
) -> tuple[int, dict[str, Any]]:
    data: dict[str, Any] = {"action": action}
    if session_id is not None:
        data["session_id"] = session_id
    files = None
    if audio_bytes is not None:
        files = {"audio_file": ("offer.wav", audio_bytes, "audio/wav")}

    response = client.post("/api/v1/offers/intake/audio", data=data, files=files)
    return response.status_code, response.json()


def test_audio_submit_starts_conversation_with_text_workflow_shape(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=DeterministicTranscriber(),
    )

    status_code, payload = _post_audio_turn(client, action="submit", audio_bytes=b"turn-one")
    assert status_code == 200
    assert payload["status"] == "in_progress"
    assert payload["step"] == "collect_monetary_extras"
    assert payload["current_prompt_key"] == "monetary_benefits"
    assert payload["missing_required_fields"] == []
    assert payload["offer"] is None


def test_audio_skip_then_finish_saves_offer_with_audio_source_type(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=DeterministicTranscriber(),
    )

    _, first = _post_audio_turn(client, action="submit", audio_bytes=b"turn-one")
    session_id = first["session_id"]

    _, second = _post_audio_turn(client, action="skip_current", session_id=session_id)
    assert second["step"] == "collect_non_monetary_extras"

    _, third = _post_audio_turn(client, action="skip_current", session_id=session_id)
    assert third["step"] == "anything_else"
    assert third["can_finish"] is True

    status_code, saved = _post_audio_turn(client, action="finish", session_id=session_id)
    assert status_code == 200
    assert saved["status"] == "saved"
    assert saved["step"] == "completed"
    offer = saved["offer"]
    assert offer is not None
    assert offer["company_name"] == "Aurora Dynamics"
    assert offer["offer_meta"]["source_input_type"] == "audio"


def test_audio_finish_blocks_when_required_fields_missing(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=MissingRequiredParser(),
        transcriber=DeterministicTranscriber(),
    )

    _, started = _post_audio_turn(client, action="submit", audio_bytes=b"turn-one")
    session_id = started["session_id"]

    status_code, blocked = _post_audio_turn(client, action="finish", session_id=session_id)
    assert status_code == 200
    assert blocked["status"] == "blocked_required_fields"
    assert blocked["step"] == "collect_required"
    assert "company_name" in blocked["missing_required_fields"]
    assert "location" in blocked["missing_required_fields"]


def test_audio_submit_requires_audio_file(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=DeterministicTranscriber(),
    )

    response = client.post("/api/v1/offers/intake/audio", data={"action": "submit"})
    assert response.status_code == 422


def test_audio_unknown_session_is_404(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=DeterministicTranscriber(),
    )

    status_code, payload = _post_audio_turn(
        client,
        action="skip_current",
        session_id="missing-session",
    )
    assert status_code == 404
    assert "Conversation session not found" in payload["detail"]


def test_audio_transcription_failure_is_observable(tmp_path: Path) -> None:
    client = _build_app_with_overrides(
        tmp_path,
        parser=DeterministicParser(),
        transcriber=BrokenTranscriber(),
    )

    status_code, payload = _post_audio_turn(client, action="submit", audio_bytes=b"turn-one")
    assert status_code == 200
    assert payload["status"] == "transcription_failed"
    assert payload["offer"] is None
    assert "Unable to transcribe audio input" in payload["errors"][0]
