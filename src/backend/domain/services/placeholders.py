"""Placeholder service implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ...domain.models import ComparisonRecord, OfferRecord
from ...storage.repositories.interfaces import (
    ComparisonRepository,
    OfferRepository,
)
from .comparison_service import ComparisonCreateResult
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
        source_input_type: str = "text",
    ) -> TextConversationResult:
        _ = action
        _ = message_text
        _ = source_input_type
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

    def intake_audio_offer(
        self,
        *,
        session_id: str | None,
        action: str,
        audio_bytes: bytes | None = None,
        filename: str = "",
        content_type: str | None = None,
    ) -> TextConversationResult:
        _ = action
        _ = audio_bytes
        _ = filename
        _ = content_type
        return TextConversationResult(
            session_id=session_id or "unimplemented",
            status="not_implemented",
            assistant_message="Offer audio intake is not implemented.",
            step="collect_required",
            can_finish=False,
            missing_required_fields=["company_name", "role_title"],
            current_prompt_key="required_fields_bundle",
            errors=["Offer audio intake is not implemented."],
            warnings=[],
            offer=None,
        )

    def list_offers(
        self,
        *,
        sort_by: Literal["created_at", "company_name", "role_title"] = "created_at",
        sort_direction: Literal["asc", "desc"] = "desc",
    ) -> list[OfferRecord]:
        return self.offer_repository.list_all(sort_by=sort_by, sort_direction=sort_direction)

    def get_offer(self, offer_id: str) -> OfferRecord | None:
        return self.offer_repository.get_by_id(offer_id)

    def delete_offer(self, offer_id: str) -> bool:
        return self.offer_repository.delete(offer_id)

    def seed_demo_offers(self) -> list[OfferRecord]:
        return []

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

    def get_offer_schema(self) -> dict[str, Any]:
        return {}


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

    def create_comparison(
        self,
        *,
        mode: Literal["one_to_one", "one_to_all"],
        selected_offer_ids: list[str],
        base_offer_id: str | None,
        note: str | None,
    ) -> ComparisonCreateResult:
        _ = mode
        _ = selected_offer_ids
        _ = base_offer_id
        _ = note
        return ComparisonCreateResult(
            status="not_implemented",
            errors=["Comparison save is not implemented."],
            comparison=None,
        )

    def list_comparisons(self) -> list[ComparisonRecord]:
        return []

    def get_comparison(self, comparison_id: str) -> ComparisonRecord | None:
        _ = comparison_id
        return None
