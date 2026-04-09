from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.main import create_app
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


def _build_client(tmp_path: Path) -> TestClient:
    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage5_1_offer_intake_test.db"),
            "enable_wal": False,
        }
    )
    agents_section = config.agents.model_copy(
        update={
            "text_parser": config.agents.text_parser.model_copy(update={"enabled": False})
        }
    )
    config = config.model_copy(update={"database": database_section, "agents": agents_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    app = create_app(container)
    return TestClient(app)


def _post_text_turn(
    client: TestClient,
    *,
    session_id: str | None,
    action: str,
    message_text: str | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {"session_id": session_id, "action": action}
    if message_text is not None:
        request["message_text"] = message_text

    response = client.post("/api/v1/offers/intake/text", json=request)
    assert response.status_code == 200
    return response.json()


def test_conversation_starts_with_required_bundle_prompt(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    payload = _post_text_turn(
        client,
        session_id=None,
        action="submit",
        message_text='{"role_title":"Software Engineer II","compensation":{"annual_base_salary_usd":145000}}',
    )

    assert payload["status"] == "in_progress"
    assert payload["step"] == "collect_required"
    assert payload["current_prompt_key"] == "required_fields_bundle"
    assert payload["offer"] is None
    assert "company_name" in payload["missing_required_fields"]
    assert payload["assistant_message"].startswith(
        "Please share the remaining required information:"
    )


def test_finish_is_blocked_until_required_fields_are_complete(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    started = _post_text_turn(
        client,
        session_id=None,
        action="submit",
        message_text='{"role_title":"ML Engineer"}',
    )
    blocked = _post_text_turn(
        client,
        session_id=started["session_id"],
        action="finish",
    )

    assert blocked["status"] == "blocked_required_fields"
    assert blocked["step"] == "collect_required"
    assert blocked["can_finish"] is False
    assert "company_name" in blocked["missing_required_fields"]
    assert blocked["assistant_message"].startswith(
        "I still need required information before saving:"
    )


def test_incremental_merge_skip_and_finish_saves_offer(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    first = _post_text_turn(
        client,
        session_id=None,
        action="submit",
        message_text=(
            '{"company_name":"Nimbus Health","role_title":"Backend Engineer",'
            '"location":"Denver, CO"}'
        ),
    )
    assert first["step"] == "collect_required"

    second = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="submit",
        message_text='{"compensation":{"annual_base_salary_usd":130000}}',
    )
    assert second["step"] == "collect_monetary_extras"

    third = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="skip_current",
    )
    assert third["step"] == "collect_non_monetary_extras"

    fourth = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="submit",
        message_text="none",
    )
    assert fourth["step"] == "anything_else"
    assert fourth["can_finish"] is True

    saved = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="finish",
    )

    assert saved["status"] == "saved"
    assert saved["step"] == "completed"
    assert saved["offer"] is not None
    offer = saved["offer"]
    assert offer["company_name"] == "Nimbus Health"
    assert offer["role_title"] == "Backend Engineer"
    assert offer["location"] == "Denver, CO"
    assert offer["compensation"]["annual_base_salary_usd"] == 130000
    assert offer["offer_meta"]["source_input_type"] == "text"


def test_prompt_sequence_order_is_deterministic(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    first = _post_text_turn(
        client,
        session_id=None,
        action="submit",
        message_text=(
            '{"company_name":"Acme Robotics","role_title":"Platform Engineer",'
            '"compensation":{"annual_base_salary_usd":150000}}'
        ),
    )
    second = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="submit",
        message_text="{}",
    )
    third = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="skip_current",
    )

    assert [first["step"], second["step"], third["step"]] == [
        "collect_monetary_extras",
        "collect_non_monetary_extras",
        "anything_else",
    ]


def test_typed_omission_detection_does_not_false_trigger_on_substrings(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    first = _post_text_turn(
        client,
        session_id=None,
        action="submit",
        message_text=(
            '{"company_name":"Acme Robotics","role_title":"Platform Engineer",'
            '"compensation":{"annual_base_salary_usd":150000}}'
        ),
    )
    assert first["step"] == "collect_monetary_extras"

    second = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="submit",
        message_text=(
            '{"monetary_benefits":{"other_monetary_benefits":["innovation stipend"]}}'
        ),
    )

    assert second["step"] == "collect_non_monetary_extras"
    assert second["warnings"] == []

    third = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="skip_current",
    )
    assert third["step"] == "anything_else"

    saved = _post_text_turn(
        client,
        session_id=first["session_id"],
        action="finish",
    )
    assert saved["status"] == "saved"
    offer = saved["offer"]
    assert offer is not None
    assert offer["monetary_benefits"]["other_monetary_benefits"] == ["innovation stipend"]


def test_unknown_session_returns_404(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    response = client.post(
        "/api/v1/offers/intake/text",
        json={
            "session_id": "missing-session",
            "action": "submit",
            "message_text": "{}",
        },
    )

    assert response.status_code == 404


def test_submit_requires_message_text(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    response = client.post(
        "/api/v1/offers/intake/text",
        json={"session_id": None, "action": "submit"},
    )

    assert response.status_code == 422
