"""Service interfaces used by API and dependency wiring."""

from __future__ import annotations

from typing import Any, Protocol

from .offer_service import IntakeResult, TextConversationResult
from ..models import OfferRecord


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
    ) -> TextConversationResult:
        """Intake text conversation turns and return stateful outcomes."""

    def intake_audio_offer(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None = None,
        omission_confirmations: dict[str, bool] | None = None,
        extracted_offer_overrides: dict[str, Any] | None = None,
    ) -> IntakeResult:
        """Intake offer audio and return save/missing/blocked outcomes."""

    def list_offers(self) -> list[OfferRecord]:
        """Return all saved offers."""

    def get_offer(self, offer_id: str) -> OfferRecord | None:
        """Return one saved offer."""

    def update_offer(self, *, offer_id: str, payload: dict[str, Any]) -> IntakeResult:
        """Update one offer and return save/blocked outcomes."""

    def render_offer_payload(self, record: OfferRecord) -> dict[str, Any]:
        """Return API-shaped payload for one offer record."""


class ComparisonService(Protocol):
    """Contract for comparison-focused orchestration behavior."""

    def describe_capabilities(self) -> dict[str, str]:
        """Return high-level service status/capabilities."""
