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
            "path": str(tmp_path / "stage4_offer_intake_test.db"),
            "enable_wal": False,
        }
    )
    config = config.model_copy(update={"database": database_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    app = create_app(container)
    return TestClient(app)


def _intake_until_saved(client: TestClient, request: dict[str, Any]) -> dict[str, Any]:
    first_response = client.post("/api/v1/offers/intake/text", json=request)
    assert first_response.status_code == 200
    first_payload = first_response.json()

    if first_payload["status"] == "saved":
        return first_payload

    assert first_payload["status"] == "missing_information"
    omission_confirmations = {
        prompt["path"]: True
        for prompt in first_payload["missing_field_prompts"]
        if not prompt["required"]
    }
    second_response = client.post(
        "/api/v1/offers/intake/text",
        json={**request, "omission_confirmations": omission_confirmations},
    )
    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["status"] == "saved"
    return second_payload


def test_required_field_failures_block_save(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    response = client.post(
        "/api/v1/offers/intake/text",
        json={
            "text": '{"role_title":"Software Engineer II","compensation":{"annual_base_salary_usd":145000}}'
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked_required_fields"
    assert payload["offer"] is None
    assert "company_name is required" in payload["errors"]


def test_non_required_missing_fields_warn_and_confirmed_omissions_are_stored(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    saved = _intake_until_saved(
        client,
        {
            "text": '{"company_name":"Nimbus Health","role_title":"Backend Engineer","compensation":{"annual_base_salary_usd":130000}}'
        },
    )

    assert saved["errors"] == []
    assert saved["warnings"] != []
    offer = saved["offer"]
    assert offer is not None
    offer_id = offer["id"]

    detail_response = client.get(f"/api/v1/offers/{offer_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()["offer"]
    assert detail["location"] == ""
    assert detail["monetary_benefits"]["other_monetary_benefits"] == []
    assert detail["non_monetary_benefits"]["mission_alignment_notes"] == ""


def test_hourly_offer_is_annualized_before_save(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    saved = _intake_until_saved(
        client,
        {
            "text": (
                '{"company_name":"Acme Robotics","role_title":"Software Engineer II",'
                '"compensation":{"hourly_rate_usd":100,"hours_per_week":40}}'
            )
        },
    )

    offer = saved["offer"]
    assert offer is not None
    assert offer["compensation"]["annual_base_salary_usd"] == 208000
