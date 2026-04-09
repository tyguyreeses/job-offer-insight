"""Placeholder service implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...domain.models import OfferRecord
from ...storage.repositories.interfaces import ComparisonRepository, OfferRepository
from .offer_service import FieldPrompt, IntakeResult, TextConversationResult


@dataclass(frozen=True)
class UnimplementedOfferService:
    offer_repository: OfferRepository

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "offer",
            "status": "placeholder",
            "message": "Offer behavior will be implemented in later stages.",
        }

    def intake_text_offer(
        self,
        *,
        session_id: str | None,
        action: str,
        message_text: str | None = None,
    ) -> TextConversationResult:
        _ = action
        _ = message_text
        return TextConversationResult(
            session_id=session_id or "unimplemented",
            status="not_implemented",
            assistant_message="Offer intake is not implemented.",
            step="collect_required",
            can_finish=False,
            missing_required_fields=["company_name", "role_title"],
            current_prompt_key="required_fields_bundle",
            errors=["Offer intake is not implemented."],
            warnings=[],
            offer=None,
        )

    def list_offers(self) -> list[OfferRecord]:
        return self.offer_repository.list_all()

    def get_offer(self, offer_id: str) -> OfferRecord | None:
        return self.offer_repository.get_by_id(offer_id)

    def update_offer(self, *, offer_id: str, payload: dict[str, Any]) -> IntakeResult:
        return IntakeResult(
            status="not_implemented",
            errors=["Offer update is not implemented."],
            warnings=[],
            missing_field_prompts=[],
            offer=None,
        )

    def render_offer_payload(self, record: OfferRecord) -> dict[str, Any]:
        payload = dict(record.payload)
        payload["id"] = record.id
        payload["company_name"] = record.company_name
        payload["role_title"] = record.role_title
        return payload


@dataclass(frozen=True)
class UnimplementedComparisonService:
    comparison_repository: ComparisonRepository
    offer_repository: OfferRepository

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "comparison",
            "status": "placeholder",
            "message": "Comparison behavior will be implemented in later stages.",
        }
