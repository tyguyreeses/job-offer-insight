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
            "path": str(tmp_path / "stage6_offers_list_test.db"),
            "enable_wal": False,
        }
    )
    agents_section = config.agents.model_copy(
        update={
            "entry_creation": config.agents.entry_creation.model_copy(update={"enabled": False}),
            "parse_entry": config.agents.parse_entry.model_copy(update={"enabled": False}),
        }
    )
    config = config.model_copy(update={"database": database_section, "agents": agents_section})
    logger = setup_logger(debug=False, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    app = create_app(container)
    return TestClient(app), container.offer_repository


def _seed_offer(offers: OfferRepository, *, company_name: str, role_title: str) -> None:
    offers.create(
        company_name=company_name,
        role_title=role_title,
        payload={
            "company_name": company_name,
            "role_title": role_title,
            "location": "Denver, CO",
            "compensation": {"annual_base_salary_usd": 150000},
            "offer_meta": {},
        },
    )


def test_list_offers_defaults_to_created_at_desc(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    _seed_offer(offers, company_name="B Company", role_title="Engineer")
    _seed_offer(offers, company_name="A Company", role_title="Architect")
    _seed_offer(offers, company_name="C Company", role_title="Manager")

    response = client.get("/api/v1/offers")
    assert response.status_code == 200
    payload = response.json()

    timestamps = [offer["offer_meta"]["created_at"] for offer in payload["offers"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_list_offers_supports_company_name_sorting(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    _seed_offer(offers, company_name="Nimbus", role_title="Engineer")
    _seed_offer(offers, company_name="Acme", role_title="Architect")
    _seed_offer(offers, company_name="Zephyr", role_title="Manager")

    asc_response = client.get("/api/v1/offers?sort_by=company_name&sort_direction=asc")
    assert asc_response.status_code == 200
    asc_names = [offer["company_name"] for offer in asc_response.json()["offers"]]
    assert asc_names == ["Acme", "Nimbus", "Zephyr"]

    desc_response = client.get("/api/v1/offers?sort_by=company_name&sort_direction=desc")
    assert desc_response.status_code == 200
    desc_names = [offer["company_name"] for offer in desc_response.json()["offers"]]
    assert desc_names == ["Zephyr", "Nimbus", "Acme"]
