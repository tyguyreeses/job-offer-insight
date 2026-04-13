from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.main import create_app
from src.backend.storage.repositories.interfaces import OfferRepository
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


def _build_client_and_repo(tmp_path: Path) -> tuple[TestClient, OfferRepository]:
    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage8_comparisons_test.db"),
            "enable_wal": False,
        }
    )
    agents_section = config.agents.model_copy(
        update={
            "entry_creation": config.agents.entry_creation.model_copy(update={"enabled": False}),
            "parse_entry": config.agents.parse_entry.model_copy(update={"enabled": False}),
            "comparison_one_to_one": config.agents.comparison_one_to_one.model_copy(update={"enabled": False}),
            "comparison_one_to_all": config.agents.comparison_one_to_all.model_copy(update={"enabled": False}),
        }
    )
    config = config.model_copy(update={"database": database_section, "agents": agents_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    app = create_app(container)
    return TestClient(app), container.offer_repository


def _seed_offer(
    offers: OfferRepository,
    *,
    company_name: str,
    role_title: str,
    salary: float,
    tax_override_state: str | None = None,
) -> str:
    payload = {
        "company_name": company_name,
        "role_title": role_title,
        "location": "Denver, CO",
        "compensation": {
            "annual_base_salary_usd": salary,
            "signing_bonus_usd": 10000,
            "target_bonus_percent": 10,
        },
        "monetary_benefits": {
            "retirement_match_percent": 4,
            "health_insurance_employer_monthly_usd": 700,
            "equity_grant_usd": 50000,
        },
        "offer_meta": {},
    }
    if tax_override_state:
        payload["tax_overrides"] = {
            "state": tax_override_state,
            "filing_status": "single",
            "pre_tax_deduction_percent": 5,
        }
    created = offers.create(
        company_name=company_name,
        role_title=role_title,
        payload=payload,
    )
    return created.id


def test_generate_one_to_one_draft_then_ai(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    left_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer", salary=160000)
    right_id = _seed_offer(offers, company_name="Beacon", role_title="Engineer", salary=180000)

    code_response = client.post(
        "/api/v1/comparisons/generate",
        json={
            "mode": "one_to_one",
            "base_offer_id": left_id,
            "selected_offer_ids": [left_id, right_id],
            "note": "Draft note",
        },
    )
    assert code_response.status_code == 200
    code_payload = code_response.json()
    assert code_payload["status"] == "draft_ready"
    assert code_payload["draft_id"] is not None
    assert code_payload["code_section"]["mode"] == "one_to_one"
    assert len(code_payload["code_section"]["metrics"]) > 0

    ai_response = client.post(f"/api/v1/comparisons/generate/{code_payload['draft_id']}/ai")
    assert ai_response.status_code == 200
    ai_payload = ai_response.json()
    assert ai_payload["status"] == "completed"
    assert "ai_section" in ai_payload
    assert isinstance(ai_payload["ai_section"], str)
    assert "###" in ai_payload["ai_section"]


def test_generate_one_to_all_includes_similarity_and_highest(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    base_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer", salary=160000)
    _seed_offer(offers, company_name="Beacon", role_title="Engineer", salary=180000)
    _seed_offer(offers, company_name="Canyon", role_title="Engineer", salary=170000)

    code_response = client.post(
        "/api/v1/comparisons/generate",
        json={
            "mode": "one_to_all",
            "base_offer_id": base_id,
            "selected_offer_ids": [base_id],
            "note": None,
        },
    )
    assert code_response.status_code == 200
    payload = code_response.json()
    assert payload["status"] == "draft_ready"
    assert payload["code_section"]["mode"] == "one_to_all"
    assert len(payload["selected_offer_ids"]) == 3
    assert any(
        "most_similar_offer_id" in row and "highest_other_offer_id" in row
        for row in payload["code_section"]["metrics"]
    )


def test_offer_payload_includes_derived_monetary_and_tax_override_effect(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    default_tax_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer", salary=160000)
    override_tax_id = _seed_offer(
        offers,
        company_name="Beacon",
        role_title="Engineer",
        salary=160000,
        tax_override_state="CA",
    )

    default_offer = client.get(f"/api/v1/offers/{default_tax_id}").json()["offer"]
    override_offer = client.get(f"/api/v1/offers/{override_tax_id}").json()["offer"]

    default_monthly = default_offer["derived_monetary"]["estimated_monthly_take_home_usd"]
    override_monthly = override_offer["derived_monetary"]["estimated_monthly_take_home_usd"]
    assert default_offer["derived_monetary"]["estimated_total_annual_monetary_benefits_usd"] > 0
    assert override_offer["derived_monetary"]["tax_profile_used"]["state"] == "CA"
    assert override_monthly < default_monthly
