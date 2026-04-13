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
            "path": str(tmp_path / "stage7_comparisons_test.db"),
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


def _seed_offer(offers: OfferRepository, *, company_name: str, role_title: str) -> str:
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


def test_create_one_to_one_comparison_and_retrieve_detail(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    left_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    right_id = _seed_offer(offers, company_name="Beacon", role_title="Engineer")

    create_response = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": left_id,
            "selected_offer_ids": [left_id, right_id],
            "note": "Prefer Atlas mission.",
        },
    )
    assert create_response.status_code == 200
    created_payload = create_response.json()
    assert created_payload["status"] == "saved"
    created = created_payload["comparison"]
    assert created["comparison_mode"] == "one_to_one"
    assert created["base_offer_id"] == left_id
    assert created["selected_offer_ids"] == [left_id, right_id]
    assert created["note"] == "Prefer Atlas mission."

    detail_response = client.get(f"/api/v1/comparisons/{created['id']}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == created["id"]
    assert detail_payload["selected_offer_ids"] == [left_id, right_id]
    assert detail_payload["summary_text"] == "Comparison summary placeholder."
    assert detail_payload["code_section"] is None
    assert detail_payload["ai_section"] is None


def test_create_one_to_all_comparison_snapshots_all_other_offers(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    base_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    other_a = _seed_offer(offers, company_name="Beacon", role_title="Engineer")
    other_b = _seed_offer(offers, company_name="Canyon", role_title="Engineer")

    create_response = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_all",
            "base_offer_id": base_id,
            "selected_offer_ids": [base_id],
            "note": None,
        },
    )
    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["status"] == "saved"
    created = payload["comparison"]
    assert created["comparison_mode"] == "one_to_all"
    assert created["base_offer_id"] == base_id
    assert created["selected_offer_ids"] == [base_id, other_b, other_a]


def test_create_one_to_one_rejects_invalid_selection_count(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    base_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")

    response = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": base_id,
            "selected_offer_ids": [base_id],
            "note": None,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "validation_error"
    assert "requires exactly 2 selected offer ids" in payload["errors"][0]
    assert payload["comparison"] is None


def test_comparisons_list_returns_saved_entries(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    left_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    right_id = _seed_offer(offers, company_name="Beacon", role_title="Engineer")

    create_response = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": left_id,
            "selected_offer_ids": [left_id, right_id],
            "note": "Saved note",
        },
    )
    assert create_response.status_code == 200

    list_response = client.get("/api/v1/comparisons")
    assert list_response.status_code == 200
    comparisons = list_response.json()["comparisons"]
    assert len(comparisons) == 1
    assert comparisons[0]["comparison_mode"] == "one_to_one"
    assert comparisons[0]["note"] == "Saved note"


def test_one_to_one_save_overrides_existing_same_offer_pair(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    left_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    right_id = _seed_offer(offers, company_name="Beacon", role_title="Engineer")

    first = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": left_id,
            "selected_offer_ids": [left_id, right_id],
            "note": "First",
        },
    )
    assert first.status_code == 200
    first_id = first.json()["comparison"]["id"]

    second = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": right_id,
            "selected_offer_ids": [right_id, left_id],
            "note": "Second",
        },
    )
    assert second.status_code == 200
    second_payload = second.json()["comparison"]
    assert second_payload["id"] == first_id
    assert second_payload["base_offer_id"] == right_id
    assert second_payload["note"] == "Second"

    listing = client.get("/api/v1/comparisons")
    assert listing.status_code == 200
    assert len(listing.json()["comparisons"]) == 1


def test_one_to_all_save_overrides_existing_same_base_offer(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    base_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    _seed_offer(offers, company_name="Beacon", role_title="Engineer")

    first = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_all",
            "base_offer_id": base_id,
            "selected_offer_ids": [base_id],
            "note": "First",
        },
    )
    assert first.status_code == 200
    first_payload = first.json()["comparison"]

    _seed_offer(offers, company_name="Canyon", role_title="Engineer")
    second = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_all",
            "base_offer_id": base_id,
            "selected_offer_ids": [base_id],
            "note": "Second",
        },
    )
    assert second.status_code == 200
    second_payload = second.json()["comparison"]
    assert second_payload["id"] == first_payload["id"]
    assert second_payload["note"] == "Second"
    assert len(second_payload["selected_offer_ids"]) == 3

    listing = client.get("/api/v1/comparisons")
    assert listing.status_code == 200
    assert len(listing.json()["comparisons"]) == 1


def test_delete_saved_comparison_removes_it(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    left_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    right_id = _seed_offer(offers, company_name="Beacon", role_title="Engineer")

    created = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": left_id,
            "selected_offer_ids": [left_id, right_id],
            "note": None,
        },
    )
    assert created.status_code == 200
    comparison_id = created.json()["comparison"]["id"]

    delete_response = client.delete(f"/api/v1/comparisons/{comparison_id}")
    assert delete_response.status_code == 204

    detail_response = client.get(f"/api/v1/comparisons/{comparison_id}")
    assert detail_response.status_code == 404


def test_create_comparison_persists_generated_sections_when_provided(tmp_path: Path) -> None:
    client, offers = _build_client_and_repo(tmp_path)
    left_id = _seed_offer(offers, company_name="Atlas", role_title="Engineer")
    right_id = _seed_offer(offers, company_name="Beacon", role_title="Engineer")

    create_response = client.post(
        "/api/v1/comparisons",
        json={
            "mode": "one_to_one",
            "base_offer_id": left_id,
            "selected_offer_ids": [left_id, right_id],
            "summary_text": "### AI Summary\n- Atlas has stronger mission fit",
            "code_section": {
                "mode": "one_to_one",
                "metrics": [{"metric_label": "Annual base salary", "percentage_difference": 12.0}],
                "notes": "Draft calculations",
            },
            "ai_section": "### AI Summary\n- Atlas has stronger mission fit",
            "note": "User note",
        },
    )
    assert create_response.status_code == 200
    comparison = create_response.json()["comparison"]
    assert comparison["summary_text"].startswith("### AI Summary")
    assert comparison["code_section"]["mode"] == "one_to_one"
    assert comparison["ai_section"].startswith("### AI Summary")
    assert comparison["note"] == "User note"
