from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.main import create_app
from src.backend.dependencies import build_runtime_container
from src.backend.utils.config_loader import load_default_config
from src.backend.utils.logging import setup_logger


def _build_client(debug: bool = False) -> TestClient:
    config = load_default_config()
    logger = setup_logger(debug=debug, configured_level=config.logging.level)
    container = build_runtime_container(config=config, logger=logger)
    app = create_app(container)
    return TestClient(app)


def test_health_endpoint_returns_ok_status() -> None:
    client = _build_client()
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint_returns_ready_status() -> None:
    client = _build_client()
    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["components"]["repositories_ready"] is True
