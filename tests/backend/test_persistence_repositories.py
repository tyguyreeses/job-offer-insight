from __future__ import annotations

from pathlib import Path

from src.backend.storage.db import SQLiteDatabase
from src.backend.storage.repositories.comparison_repository import SQLiteComparisonRepository
from src.backend.storage.repositories.offer_repository import SQLiteOfferRepository


def _build_repositories(tmp_path: Path) -> tuple[SQLiteOfferRepository, SQLiteComparisonRepository]:
    database = SQLiteDatabase(
        path=tmp_path / "job_offer_insight_test.db",
        enable_wal=False,
        timeout_seconds=5.0,
    )
    database.initialize()
    return (
        SQLiteOfferRepository(database=database),
        SQLiteComparisonRepository(database=database),
    )


def test_offer_create_read_update_persistence(tmp_path: Path) -> None:
    offers, _ = _build_repositories(tmp_path)

    created = offers.create(
        company_name="Acme Robotics",
        role_title="Software Engineer II",
        payload={
            "company_name": "Acme Robotics",
            "role_title": "Software Engineer II",
            "compensation": {"annual_base_salary_usd": 145000},
        },
    )

    fetched = offers.get_by_id(created.id)
    assert fetched is not None
    assert fetched.company_name == "Acme Robotics"
    assert fetched.payload["compensation"]["annual_base_salary_usd"] == 145000

    updated = offers.update(
        offer_id=created.id,
        company_name="Acme Robotics",
        role_title="Senior Software Engineer II",
        payload={
            "company_name": "Acme Robotics",
            "role_title": "Senior Software Engineer II",
            "compensation": {"annual_base_salary_usd": 152000},
        },
    )
    assert updated is not None
    assert updated.role_title == "Senior Software Engineer II"
    assert updated.payload["compensation"]["annual_base_salary_usd"] == 152000
    assert updated.updated_at != created.updated_at

    listed = offers.list_all()
    assert len(listed) == 1
    assert listed[0].id == created.id


def test_comparison_save_list_and_detail_persistence(tmp_path: Path) -> None:
    offers, comparisons = _build_repositories(tmp_path)
    left_offer = offers.create(
        company_name="Acme Robotics",
        role_title="Software Engineer II",
        payload={"company_name": "Acme Robotics", "role_title": "Software Engineer II"},
    )
    right_offer = offers.create(
        company_name="Beacon Labs",
        role_title="Software Engineer II",
        payload={"company_name": "Beacon Labs", "role_title": "Software Engineer II"},
    )

    saved = comparisons.create(
        selected_offer_ids=[left_offer.id, right_offer.id],
        summary_text="Comparison summary placeholder.",
        note="Prefer mission alignment.",
    )

    detail = comparisons.get_by_id(saved.id)
    assert detail is not None
    assert detail.selected_offer_ids == [left_offer.id, right_offer.id]
    assert detail.summary_text == "Comparison summary placeholder."
    assert detail.note == "Prefer mission alignment."

    listing = comparisons.list_all()
    assert len(listing) == 1
    assert listing[0].id == saved.id


def test_blank_field_semantics_are_preserved_as_non_errors(tmp_path: Path) -> None:
    offers, _ = _build_repositories(tmp_path)

    created = offers.create(
        company_name="Nimbus Health",
        role_title="Backend Engineer",
        payload={
            "company_name": "Nimbus Health",
            "role_title": "Backend Engineer",
            "compensation": {
                "annual_base_salary_usd": 130000,
                "signing_bonus_usd": None,
            },
            "monetary_benefits": {
                "other_monetary_benefits": [],
            },
            "non_monetary_benefits": {
                "mission_alignment_notes": "",
            },
        },
    )

    fetched = offers.get_by_id(created.id)
    assert fetched is not None
    assert fetched.payload["compensation"]["signing_bonus_usd"] is None
    assert fetched.payload["monetary_benefits"]["other_monetary_benefits"] == []
    assert fetched.payload["non_monetary_benefits"]["mission_alignment_notes"] == ""
