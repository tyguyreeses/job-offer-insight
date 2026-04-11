from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.dependencies import build_runtime_container
from src.backend.main import create_app
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


def _build_client(tmp_path: Path) -> TestClient:
    config = load_default_config()
    database_section = config.database.model_copy(
        update={
            "path": str(tmp_path / "stage6_offer_demo_seed_test.db"),
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
    return TestClient(app)


def test_debug_seed_creates_three_demo_offers(tmp_path: Path) -> None:
    client = _build_client(tmp_path)

    response = client.post("/api/v1/offers/debug/demo-seed")
    assert response.status_code == 200
    payload = response.json()

    assert len(payload["offers"]) == 3
    companies = {offer["company_name"] for offer in payload["offers"]}
    assert companies == {"Northstar Robotics", "Sierra Data Labs", "Canyon Cloud Systems"}

    list_response = client.get("/api/v1/offers")
    assert list_response.status_code == 200
    assert len(list_response.json()["offers"]) == 3
