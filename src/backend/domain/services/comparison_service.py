"""Comparison orchestration for Stage 7 compare workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ...domain.models import ComparisonRecord
from ...storage.repositories.interfaces import ComparisonRepository, OfferRepository

ComparisonMode = Literal["one_to_one", "one_to_all"]
_PLACEHOLDER_SUMMARY_TEXT = "Comparison summary placeholder."


@dataclass(frozen=True)
class ComparisonCreateResult:
    status: str
    errors: list[str]
    comparison: ComparisonRecord | None


@dataclass(frozen=True)
class Stage7ComparisonService:
    comparison_repository: ComparisonRepository
    offer_repository: OfferRepository

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "comparison",
            "status": "ready",
            "message": "Comparison save/list/detail behavior is implemented.",
        }

    def create_comparison(
        self,
        *,
        mode: ComparisonMode,
        selected_offer_ids: list[str],
        base_offer_id: str | None,
        note: str | None,
    ) -> ComparisonCreateResult:
        normalized_selected_offer_ids = _normalize_selected_offer_ids(selected_offer_ids)
        resolved_base_offer_id = (base_offer_id or "").strip()
        if resolved_base_offer_id == "" and normalized_selected_offer_ids:
            resolved_base_offer_id = normalized_selected_offer_ids[0]

        if mode == "one_to_one":
            return self._create_one_to_one(
                selected_offer_ids=normalized_selected_offer_ids,
                base_offer_id=resolved_base_offer_id,
                note=note,
            )
        return self._create_one_to_all(base_offer_id=resolved_base_offer_id, note=note)

    def list_comparisons(self) -> list[ComparisonRecord]:
        return self.comparison_repository.list_all()

    def get_comparison(self, comparison_id: str) -> ComparisonRecord | None:
        return self.comparison_repository.get_by_id(comparison_id)

    def _create_one_to_one(
        self,
        *,
        selected_offer_ids: list[str],
        base_offer_id: str,
        note: str | None,
    ) -> ComparisonCreateResult:
        if len(selected_offer_ids) != 2:
            return ComparisonCreateResult(
                status="validation_error",
                errors=["one_to_one mode requires exactly 2 selected offer ids."],
                comparison=None,
            )
        if base_offer_id == "":
            return ComparisonCreateResult(
                status="validation_error",
                errors=["base_offer_id is required."],
                comparison=None,
            )
        if base_offer_id not in selected_offer_ids:
            return ComparisonCreateResult(
                status="validation_error",
                errors=["base_offer_id must be one of selected_offer_ids."],
                comparison=None,
            )

        missing_ids = self._missing_offer_ids(selected_offer_ids)
        if missing_ids:
            return ComparisonCreateResult(
                status="validation_error",
                errors=[f"Offer not found: {offer_id}" for offer_id in missing_ids],
                comparison=None,
            )

        note_value = _normalize_note(note)
        existing_match = self._find_existing_one_to_one(selected_offer_ids)
        if existing_match is not None:
            updated = self.comparison_repository.update(
                comparison_id=existing_match.id,
                comparison_mode="one_to_one",
                base_offer_id=base_offer_id,
                selected_offer_ids=selected_offer_ids,
                summary_text=_PLACEHOLDER_SUMMARY_TEXT,
                note=note_value,
            )
            if updated is not None:
                self._delete_other_matches_one_to_one(
                    keep_comparison_id=updated.id,
                    selected_offer_ids=selected_offer_ids,
                )
                return ComparisonCreateResult(status="saved", errors=[], comparison=updated)

        created = self.comparison_repository.create(
            comparison_mode="one_to_one",
            base_offer_id=base_offer_id,
            selected_offer_ids=selected_offer_ids,
            summary_text=_PLACEHOLDER_SUMMARY_TEXT,
            note=note_value,
        )
        return ComparisonCreateResult(status="saved", errors=[], comparison=created)

    def _create_one_to_all(
        self,
        *,
        base_offer_id: str,
        note: str | None,
    ) -> ComparisonCreateResult:
        if base_offer_id == "":
            return ComparisonCreateResult(
                status="validation_error",
                errors=["base_offer_id is required."],
                comparison=None,
            )

        if self.offer_repository.get_by_id(base_offer_id) is None:
            return ComparisonCreateResult(
                status="validation_error",
                errors=[f"Offer not found: {base_offer_id}"],
                comparison=None,
            )

        all_offers = self.offer_repository.list_all(sort_by="created_at", sort_direction="desc")
        compared_offer_ids = [offer.id for offer in all_offers if offer.id != base_offer_id]
        if len(compared_offer_ids) == 0:
            return ComparisonCreateResult(
                status="validation_error",
                errors=["one_to_all mode requires at least 1 additional offer."],
                comparison=None,
            )

        snapshot_ids = [base_offer_id, *compared_offer_ids]
        note_value = _normalize_note(note)
        existing_match = self._find_existing_one_to_all(base_offer_id)
        if existing_match is not None:
            updated = self.comparison_repository.update(
                comparison_id=existing_match.id,
                comparison_mode="one_to_all",
                base_offer_id=base_offer_id,
                selected_offer_ids=snapshot_ids,
                summary_text=_PLACEHOLDER_SUMMARY_TEXT,
                note=note_value,
            )
            if updated is not None:
                self._delete_other_matches_one_to_all(
                    keep_comparison_id=updated.id,
                    base_offer_id=base_offer_id,
                )
                return ComparisonCreateResult(status="saved", errors=[], comparison=updated)

        created = self.comparison_repository.create(
            comparison_mode="one_to_all",
            base_offer_id=base_offer_id,
            selected_offer_ids=snapshot_ids,
            summary_text=_PLACEHOLDER_SUMMARY_TEXT,
            note=note_value,
        )
        return ComparisonCreateResult(status="saved", errors=[], comparison=created)

    def _missing_offer_ids(self, offer_ids: list[str]) -> list[str]:
        missing: list[str] = []
        for offer_id in offer_ids:
            if self.offer_repository.get_by_id(offer_id) is None:
                missing.append(offer_id)
        return missing

    def _find_existing_one_to_one(self, selected_offer_ids: list[str]) -> ComparisonRecord | None:
        target_ids = set(selected_offer_ids)
        for comparison in self.comparison_repository.list_all():
            if comparison.comparison_mode != "one_to_one":
                continue
            if set(comparison.selected_offer_ids) == target_ids:
                return comparison
        return None

    def _find_existing_one_to_all(self, base_offer_id: str) -> ComparisonRecord | None:
        for comparison in self.comparison_repository.list_all():
            if comparison.comparison_mode != "one_to_all":
                continue
            if comparison.base_offer_id == base_offer_id:
                return comparison
        return None

    def _delete_other_matches_one_to_one(
        self,
        *,
        keep_comparison_id: str,
        selected_offer_ids: list[str],
    ) -> None:
        target_ids = set(selected_offer_ids)
        for comparison in self.comparison_repository.list_all():
            if comparison.id == keep_comparison_id:
                continue
            if comparison.comparison_mode != "one_to_one":
                continue
            if set(comparison.selected_offer_ids) == target_ids:
                self.comparison_repository.delete(comparison.id)

    def _delete_other_matches_one_to_all(
        self,
        *,
        keep_comparison_id: str,
        base_offer_id: str,
    ) -> None:
        for comparison in self.comparison_repository.list_all():
            if comparison.id == keep_comparison_id:
                continue
            if comparison.comparison_mode != "one_to_all":
                continue
            if comparison.base_offer_id == base_offer_id:
                self.comparison_repository.delete(comparison.id)


def _normalize_selected_offer_ids(selected_offer_ids: list[str]) -> list[str]:
    normalized: list[str] = []
    for offer_id in selected_offer_ids:
        cleaned = offer_id.strip()
        if cleaned == "" or cleaned in normalized:
            continue
        normalized.append(cleaned)
    return normalized


def _normalize_note(note: str | None) -> str | None:
    if note is None:
        return None
    cleaned = note.strip()
    return cleaned if cleaned != "" else None
