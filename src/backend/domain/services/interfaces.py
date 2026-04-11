"""Service interfaces used by API and dependency wiring."""

from __future__ import annotations

from typing import Any, Literal, Protocol

from .offer_service import IntakeResult, TextConversationResult
from ..models import ComparisonRecord, OfferRecord
from .comparison_service import (
    ComparisonCreateResult,
    ComparisonGenerateAIResult,
    ComparisonGenerateCodeResult,
    ComparisonMode,
)

OfferSortBy = Literal["created_at", "company_name", "role_title"]
SortDirection = Literal["asc", "desc"]


class OfferService(Protocol):
    """Contract for offer-focused orchestration behavior."""

    def describe_capabilities(self) -> dict[str, str]:
        """Return high-level service status/capabilities."""

    def intake_text_offer(
        self,
        *,
        session_id: str | None,
        action: str,
        message_text: str | None = None,
        source_input_type: str = "text",
    ) -> TextConversationResult:
        """Intake text conversation turns and return stateful outcomes."""

    def intake_audio_offer(
        self,
        *,
        session_id: str | None,
        action: str,
        audio_bytes: bytes | None = None,
        filename: str = "",
        content_type: str | None = None,
    ) -> TextConversationResult:
        """Intake conversational audio turns and return stateful outcomes."""

    def list_offers(
        self,
        *,
        sort_by: OfferSortBy = "created_at",
        sort_direction: SortDirection = "desc",
    ) -> list[OfferRecord]:
        """Return all saved offers."""

    def get_offer(self, offer_id: str) -> OfferRecord | None:
        """Return one saved offer."""

    def delete_offer(self, offer_id: str) -> bool:
        """Delete one saved offer and return whether it existed."""

    def seed_demo_offers(self) -> list[OfferRecord]:
        """Create and return demo offers for temporary debug workflows."""

    def update_offer(self, *, offer_id: str, payload: dict[str, Any]) -> IntakeResult:
        """Update one offer and return save/blocked outcomes."""

    def render_offer_payload(self, record: OfferRecord) -> dict[str, Any]:
        """Return API-shaped payload for one offer record."""

    def get_offer_schema(self) -> dict[str, Any]:
        """Return the normalized config-driven offer schema contract."""


class ComparisonService(Protocol):
    """Contract for comparison-focused orchestration behavior."""

    def describe_capabilities(self) -> dict[str, str]:
        """Return high-level service status/capabilities."""

    def create_comparison(
        self,
        *,
        mode: ComparisonMode,
        selected_offer_ids: list[str],
        base_offer_id: str | None,
        note: str | None,
    ) -> ComparisonCreateResult:
        """Create and return one saved comparison."""

    def generate_comparison_draft(
        self,
        *,
        mode: ComparisonMode,
        selected_offer_ids: list[str],
        base_offer_id: str | None,
        note: str | None,
    ) -> ComparisonGenerateCodeResult:
        """Generate deterministic draft comparison output (non-persisted)."""

    def generate_comparison_ai_section(self, *, draft_id: str) -> ComparisonGenerateAIResult:
        """Generate AI comparison text for an existing draft id."""

    def list_comparisons(self) -> list[ComparisonRecord]:
        """Return all saved comparisons."""

    def get_comparison(self, comparison_id: str) -> ComparisonRecord | None:
        """Return one saved comparison by id."""

    def delete_comparison(self, comparison_id: str) -> bool:
        """Delete one saved comparison and return whether it existed."""
