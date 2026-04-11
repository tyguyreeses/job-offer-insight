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
            "path": str(tmp_path / "stage6_offer_delete_test.db"),
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


def _seed_offer(offers: OfferRepository, *, company_name: str = "Acme", role_title: str = "Engineer") -> str:
    created = offers.create(
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
    return created.id


def test_delete_offer_returns_204_and_removes_offer(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    offer_id = _seed_offer(offers)

    response = client.delete(f"/api/v1/offers/{offer_id}")
    assert response.status_code == 204
    assert offers.get_by_id(offer_id) is None


def test_delete_offer_returns_404_when_missing(tmp_path: Path) -> None:
    client, _ = _build_client_and_repo(tmp_path)
    response = client.delete("/api/v1/offers/does-not-exist")
    assert response.status_code == 404
