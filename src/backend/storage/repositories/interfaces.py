"""Repository interfaces used for dependency boundaries."""

from __future__ import annotations

from typing import Any, Literal, Mapping, Protocol, Sequence

from ...domain.models import ComparisonRecord, OfferRecord

OfferSortBy = Literal["created_at", "company_name", "role_title"]
SortDirection = Literal["asc", "desc"]


class OfferRepository(Protocol):
    """Contract for offer persistence boundary."""

    def create(
        self,
        *,
        company_name: str,
        role_title: str,
        payload: Mapping[str, Any],
        offer_id: str | None = None,
    ) -> OfferRecord:
        """Persist and return a newly created offer record."""

    def get_by_id(self, offer_id: str) -> OfferRecord | None:
        """Return one offer record by id."""

    def list_all(
        self,
        *,
        sort_by: OfferSortBy = "created_at",
        sort_direction: SortDirection = "desc",
    ) -> list[OfferRecord]:
        """Return all offer records."""

    def update(
        self,
        *,
        offer_id: str,
        payload: Mapping[str, Any],
        company_name: str | None = None,
        role_title: str | None = None,
    ) -> OfferRecord | None:
        """Update and return one offer record if it exists."""

    def delete(self, offer_id: str) -> bool:
        """Delete one offer record and return whether one row was removed."""

    def ping(self) -> bool:
        """Return whether the backing store appears reachable."""


class ComparisonRepository(Protocol):
    """Contract for comparison persistence boundary."""

    def create(
        self,
        *,
        comparison_mode: str,
        base_offer_id: str,
        selected_offer_ids: Sequence[str],
        summary_text: str,
        note: str | None = None,
        comparison_id: str | None = None,
    ) -> ComparisonRecord:
        """Persist and return a newly created comparison record."""

    def get_by_id(self, comparison_id: str) -> ComparisonRecord | None:
        """Return one comparison record by id."""

    def list_all(self) -> list[ComparisonRecord]:
        """Return all comparison records."""

    def update(
        self,
        *,
        comparison_id: str,
        comparison_mode: str | None = None,
        base_offer_id: str | None = None,
        selected_offer_ids: Sequence[str] | None = None,
        summary_text: str | None = None,
        note: str | None = None,
    ) -> ComparisonRecord | None:
        """Update and return one comparison record if it exists."""

    def delete(self, comparison_id: str) -> bool:
        """Delete one comparison record and return whether one row was removed."""

    def ping(self) -> bool:
        """Return whether the backing store appears reachable."""
