from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.storage.repositories.interfaces import OfferRepository
from src.backend.main import create_app
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


def _build_client_and_repo(tmp_path: Path) -> tuple[TestClient, OfferRepository]:
    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage6_offer_update_test.db"),
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


def _seed_offer(offers: OfferRepository) -> str:
    created = offers.create(
        company_name="Acme",
        role_title="Engineer",
        payload={
            "company_name": "Acme",
            "role_title": "Engineer",
            "location": "Denver, CO",
            "compensation": {"annual_base_salary_usd": 150000},
            "offer_meta": {},
        },
    )
    return created.id


def test_update_offer_missing_id_returns_404_before_required_validation(tmp_path: Path) -> None:
    client, _ = _build_client_and_repo(tmp_path)

    response = client.put(
        "/api/v1/offers/does-not-exist",
        json={"payload": {"company_name": "Acme"}},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Offer not found: does-not-exist"


def test_update_offer_existing_id_still_blocks_on_missing_required_fields(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    offer_id = _seed_offer(offers)

    response = client.put(
        f"/api/v1/offers/{offer_id}",
        json={"payload": {"company_name": "Acme"}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked_required_fields"
    assert "role_title is required" in payload["errors"]
    assert "location is required" in payload["errors"]
