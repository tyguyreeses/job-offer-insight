from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.domain.services.offer_service import Stage4OfferService
from src.backend.gen_ai.text_parser_agent import TextParserError
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


def test_open_ended_text_is_parsed_into_required_fields(tmp_path: Path) -> None:
    class DeterministicParser:
        def parse(self, text: str) -> dict[str, Any]:
            assert "Elevation Labs" in text
            return {
                "company_name": "Elevation Labs",
                "role_title": "Platform Engineer",
                "compensation": {"annual_base_salary_usd": 150000},
            }

    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage4_offer_intake_open_ended.db"),
            "enable_wal": False,
        }
    )
    config = config.model_copy(update={"database": database_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    service = Stage4OfferService(
        offer_repository=container.offer_repository,
        text_parser_agent=DeterministicParser(),
    )
    app = create_app(replace(container, offer_service=service))
    client = TestClient(app)

    saved = _intake_until_saved(
        client,
        {
            "text": "Company: Elevation Labs\nRole: Platform Engineer\nAnnual base salary: $150,000"
        },
    )

    offer = saved["offer"]
    assert offer is not None
    assert offer["company_name"] == "Elevation Labs"
    assert offer["role_title"] == "Platform Engineer"
    assert offer["compensation"]["annual_base_salary_usd"] == 150000


def test_parser_failure_returns_extraction_failed_status(tmp_path: Path) -> None:
    class BrokenParser:
        def parse(self, text: str) -> dict[str, Any]:
            raise TextParserError("parser output did not match schema")

    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage4_offer_intake_parser_failure.db"),
            "enable_wal": False,
        }
    )
    config = config.model_copy(update={"database": database_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    failing_service = Stage4OfferService(
        offer_repository=container.offer_repository,
        text_parser_agent=BrokenParser(),
    )
    app = create_app(replace(container, offer_service=failing_service))
    client = TestClient(app)

    response = client.post(
        "/api/v1/offers/intake/text",
        json={"text": "Some raw input text"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "extraction_failed"
    assert payload["offer"] is None
    assert "Unable to extract structured offer data" in payload["errors"][0]
