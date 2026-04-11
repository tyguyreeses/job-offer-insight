"""Comparison orchestration for Stage 8 generation + persistence workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from ...domain.models import ComparisonRecord, OfferRecord
from ...domain.offer_schema import ConfiguredOfferSchema, get_path
from ...gen_ai.agent_registry import AgentRegistry
from ...gen_ai.agent_runtime import AgentExecutionError, NonStructuredAgent
from ...storage.repositories.interfaces import ComparisonRepository, OfferRepository
from ...utils.config_types import OpenAISection
from .monetary_calculations import compute_derived_monetary_summary

ComparisonMode = Literal["one_to_one", "one_to_all"]
_PLACEHOLDER_SUMMARY_TEXT = "Comparison summary placeholder."


@dataclass(frozen=True)
class ComparisonCreateResult:
    status: str
    errors: list[str]
    comparison: ComparisonRecord | None


@dataclass(frozen=True)
class ComparisonGenerateCodeResult:
    status: str
    errors: list[str]
    draft_id: str | None
    mode: ComparisonMode | None
    base_offer_id: str | None
    selected_offer_ids: list[str]
    code_section: dict[str, Any] | None
    ai_section_pending: bool


@dataclass(frozen=True)
class ComparisonGenerateAIResult:
    status: str
    errors: list[str]
    draft_id: str | None
    ai_section: dict[str, Any] | None


@dataclass
class _GeneratedDraft:
    draft_id: str
    mode: ComparisonMode
    base_offer_id: str
    selected_offer_ids: list[str]
    offers_by_id: dict[str, OfferRecord]
    code_section: dict[str, Any]
    note: str | None
    ai_section: dict[str, Any] | None = None


def _coerce_number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        if cleaned == "":
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _percent_difference(base: float, other: float) -> float | None:
    if base == 0:
        return 0.0 if other == 0 else None
    return ((other - base) / abs(base)) * 100.0


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


@dataclass
class Stage8ComparisonService:
    comparison_repository: ComparisonRepository
    offer_repository: OfferRepository
    offer_schema: ConfiguredOfferSchema
    tax_config: Any
    agent_registry: AgentRegistry | None = None
    openai_config: OpenAISection | None = None
    generated_drafts: dict[str, _GeneratedDraft] = field(default_factory=dict)

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "comparison",
            "status": "stage_8_ready",
            "message": "Comparison persistence and generation behavior is implemented.",
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

    def generate_comparison_draft(
        self,
        *,
        mode: ComparisonMode,
        selected_offer_ids: list[str],
        base_offer_id: str | None,
        note: str | None,
    ) -> ComparisonGenerateCodeResult:
        normalized_selected_offer_ids = _normalize_selected_offer_ids(selected_offer_ids)
        resolved_base_offer_id = (base_offer_id or "").strip()
        if resolved_base_offer_id == "" and normalized_selected_offer_ids:
            resolved_base_offer_id = normalized_selected_offer_ids[0]

        if mode == "one_to_one":
            if len(normalized_selected_offer_ids) != 2:
                return ComparisonGenerateCodeResult(
                    status="validation_error",
                    errors=["one_to_one mode requires exactly 2 selected offer ids."],
                    draft_id=None,
                    mode=None,
                    base_offer_id=None,
                    selected_offer_ids=[],
                    code_section=None,
                    ai_section_pending=True,
                )
            if resolved_base_offer_id not in normalized_selected_offer_ids:
                return ComparisonGenerateCodeResult(
                    status="validation_error",
                    errors=["base_offer_id must be one of selected_offer_ids."],
                    draft_id=None,
                    mode=None,
                    base_offer_id=None,
                    selected_offer_ids=[],
                    code_section=None,
                    ai_section_pending=True,
                )
            selected_ids = normalized_selected_offer_ids
        else:
            if resolved_base_offer_id == "":
                return ComparisonGenerateCodeResult(
                    status="validation_error",
                    errors=["base_offer_id is required."],
                    draft_id=None,
                    mode=None,
                    base_offer_id=None,
                    selected_offer_ids=[],
                    code_section=None,
                    ai_section_pending=True,
                )
            all_offers = self.offer_repository.list_all(sort_by="created_at", sort_direction="desc")
            other_ids = [offer.id for offer in all_offers if offer.id != resolved_base_offer_id]
            if len(other_ids) == 0:
                return ComparisonGenerateCodeResult(
                    status="validation_error",
                    errors=["one_to_all mode requires at least 1 additional offer."],
                    draft_id=None,
                    mode=None,
                    base_offer_id=None,
                    selected_offer_ids=[],
                    code_section=None,
                    ai_section_pending=True,
                )
            selected_ids = [resolved_base_offer_id, *other_ids]

        offers_by_id: dict[str, OfferRecord] = {}
        for offer_id in selected_ids:
            offer = self.offer_repository.get_by_id(offer_id)
            if offer is None:
                return ComparisonGenerateCodeResult(
                    status="validation_error",
                    errors=[f"Offer not found: {offer_id}"],
                    draft_id=None,
                    mode=None,
                    base_offer_id=None,
                    selected_offer_ids=[],
                    code_section=None,
                    ai_section_pending=True,
                )
            offers_by_id[offer_id] = offer

        code_section = self._build_code_section(
            mode=mode,
            base_offer_id=resolved_base_offer_id,
            selected_offer_ids=selected_ids,
            offers_by_id=offers_by_id,
        )
        draft_id = str(uuid4())
        self.generated_drafts[draft_id] = _GeneratedDraft(
            draft_id=draft_id,
            mode=mode,
            base_offer_id=resolved_base_offer_id,
            selected_offer_ids=selected_ids,
            offers_by_id=offers_by_id,
            code_section=code_section,
            note=_normalize_note(note),
        )
        return ComparisonGenerateCodeResult(
            status="draft_ready",
            errors=[],
            draft_id=draft_id,
            mode=mode,
            base_offer_id=resolved_base_offer_id,
            selected_offer_ids=selected_ids,
            code_section=code_section,
            ai_section_pending=True,
        )

    def generate_comparison_ai_section(self, *, draft_id: str) -> ComparisonGenerateAIResult:
        draft = self.generated_drafts.get(draft_id)
        if draft is None:
            return ComparisonGenerateAIResult(
                status="validation_error",
                errors=[f"Comparison draft not found: {draft_id}"],
                draft_id=None,
                ai_section=None,
            )
        if draft.ai_section is None:
            draft.ai_section = self._build_ai_section(draft)
        return ComparisonGenerateAIResult(
            status="completed",
            errors=[],
            draft_id=draft.draft_id,
            ai_section=draft.ai_section,
        )

    def list_comparisons(self) -> list[ComparisonRecord]:
        return self.comparison_repository.list_all()

    def get_comparison(self, comparison_id: str) -> ComparisonRecord | None:
        return self.comparison_repository.get_by_id(comparison_id)

    def delete_comparison(self, comparison_id: str) -> bool:
        return self.comparison_repository.delete(comparison_id)

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

    def _build_code_section(
        self,
        *,
        mode: ComparisonMode,
        base_offer_id: str,
        selected_offer_ids: list[str],
        offers_by_id: dict[str, OfferRecord],
    ) -> dict[str, Any]:
        if mode == "one_to_one":
            other_offer_id = selected_offer_ids[0] if selected_offer_ids[1] == base_offer_id else selected_offer_ids[1]
            return self._build_one_to_one_code_section(
                base_offer=offers_by_id[base_offer_id],
                other_offer=offers_by_id[other_offer_id],
            )
        return self._build_one_to_all_code_section(
            base_offer=offers_by_id[base_offer_id],
            other_offers=[offers_by_id[offer_id] for offer_id in selected_offer_ids if offer_id != base_offer_id],
        )

    def _numeric_metrics(self, payload: dict[str, Any]) -> dict[str, float]:
        metrics: dict[str, float] = {}
        for field in self.offer_schema.fields:
            if field.data_type not in ("number", "integer"):
                continue
            if field.group not in ("compensation", "monetary"):
                continue
            value = _coerce_number(get_path(payload, field.storage_path))
            if value is None:
                continue
            metrics[field.storage_path] = value

        derived = compute_derived_monetary_summary(payload, tax_config=self.tax_config)
        metrics["derived_monetary.estimated_total_annual_monetary_benefits_usd"] = (
            derived.estimated_total_annual_monetary_benefits_usd
        )
        metrics["derived_monetary.estimated_monthly_take_home_usd"] = derived.estimated_monthly_take_home_usd
        return metrics

    def _metric_label(self, path: str) -> str:
        if path == "derived_monetary.estimated_total_annual_monetary_benefits_usd":
            return "Estimated Total Annual Monetary Benefits"
        if path == "derived_monetary.estimated_monthly_take_home_usd":
            return "Monthly Take-Home"
        field = self.offer_schema.field_by_path.get(path)
        return field.label if field is not None else path

    def _build_one_to_one_code_section(
        self,
        *,
        base_offer: OfferRecord,
        other_offer: OfferRecord,
    ) -> dict[str, Any]:
        base_metrics = self._numeric_metrics(base_offer.payload)
        other_metrics = self._numeric_metrics(other_offer.payload)
        metric_rows: list[dict[str, Any]] = []
        for path in sorted(set(base_metrics.keys()) & set(other_metrics.keys())):
            base_value = base_metrics[path]
            other_value = other_metrics[path]
            metric_rows.append(
                {
                    "metric_path": path,
                    "metric_label": self._metric_label(path),
                    "base_value": round(base_value, 2),
                    "other_value": round(other_value, 2),
                    "percentage_difference": _percent_difference(base_value, other_value),
                }
            )

        return {
            "title": "Deterministic Numeric Comparison",
            "mode": "one_to_one",
            "base_offer_id": base_offer.id,
            "other_offer_id": other_offer.id,
            "metrics": metric_rows,
            "notes": "Optional numeric fields are compared only when present in both offers.",
        }

    def _build_one_to_all_code_section(
        self,
        *,
        base_offer: OfferRecord,
        other_offers: list[OfferRecord],
    ) -> dict[str, Any]:
        base_metrics = self._numeric_metrics(base_offer.payload)
        other_metric_maps = {offer.id: self._numeric_metrics(offer.payload) for offer in other_offers}

        metric_rows: list[dict[str, Any]] = []
        for path, base_value in base_metrics.items():
            candidates: list[tuple[str, float]] = []
            for offer_id, metric_map in other_metric_maps.items():
                other_value = metric_map.get(path)
                if other_value is None:
                    continue
                candidates.append((offer_id, other_value))
            if len(candidates) == 0:
                continue
            highest_offer_id, highest_value = max(candidates, key=lambda candidate: candidate[1])
            similar_offer_id, similar_value = min(
                candidates, key=lambda candidate: abs(candidate[1] - base_value)
            )
            metric_rows.append(
                {
                    "metric_path": path,
                    "metric_label": self._metric_label(path),
                    "base_value": round(base_value, 2),
                    "highest_other_offer_id": highest_offer_id,
                    "highest_other_value": round(highest_value, 2),
                    "percentage_difference_to_highest": _percent_difference(base_value, highest_value),
                    "most_similar_offer_id": similar_offer_id,
                    "most_similar_value": round(similar_value, 2),
                }
            )

        return {
            "title": "Deterministic Base-vs-All Numeric Comparison",
            "mode": "one_to_all",
            "base_offer_id": base_offer.id,
            "other_offer_ids": [offer.id for offer in other_offers],
            "metrics": metric_rows,
            "notes": "Per metric, compares base vs highest other and identifies closest-by-value offer.",
        }

    def _build_ai_section(self, draft: _GeneratedDraft) -> dict[str, Any]:
        generated_text = self._run_ai_generation(draft)
        if generated_text is None:
            generated_text = self._fallback_ai_text(draft)
        return {
            "title": "AI Comparison Narrative",
            "mode": draft.mode,
            "text": generated_text,
        }

    def _run_ai_generation(self, draft: _GeneratedDraft) -> str | None:
        if self.agent_registry is None or self.openai_config is None:
            return None
        agent_name = "comparison_one_to_one" if draft.mode == "one_to_one" else "comparison_one_to_all"
        try:
            agent = self.agent_registry.get(agent_name)
            if not agent.enabled:
                return None
            user_input = json.dumps(
                {
                    "mode": draft.mode,
                    "base_offer_id": draft.base_offer_id,
                    "selected_offer_ids": draft.selected_offer_ids,
                    "offers": {
                        offer_id: record.payload for offer_id, record in draft.offers_by_id.items()
                    },
                    "deterministic_code_section": draft.code_section,
                    "note": draft.note,
                },
                ensure_ascii=True,
            )
            text = NonStructuredAgent(agent=agent, openai_config=self.openai_config).run(user_input)
            cleaned = text.strip()
            return cleaned if cleaned != "" else None
        except (AgentExecutionError, KeyError):
            return None

    def _fallback_ai_text(self, draft: _GeneratedDraft) -> str:
        base_offer = draft.offers_by_id[draft.base_offer_id]
        base_non_monetary = [
            item
            for item in (get_path(base_offer.payload, "non_monetary_summary_bullets") or [])
            if isinstance(item, str) and item.strip() != ""
        ]
        if draft.mode == "one_to_one":
            other_id = draft.selected_offer_ids[0] if draft.selected_offer_ids[1] == draft.base_offer_id else draft.selected_offer_ids[1]
            other_offer = draft.offers_by_id[other_id]
            other_non_monetary = [
                item
                for item in (get_path(other_offer.payload, "non_monetary_summary_bullets") or [])
                if isinstance(item, str) and item.strip() != ""
            ]
            unique_base = [item for item in base_non_monetary if item not in other_non_monetary]
            unique_other = [item for item in other_non_monetary if item not in base_non_monetary]
            return (
                "Non-monetary comparison:\n"
                f"- Base-only strengths: {', '.join(unique_base) if unique_base else 'None identified'}.\n"
                f"- Other-offer strengths: {', '.join(unique_other) if unique_other else 'None identified'}.\n"
                "- Included non-required field differences were reviewed alongside deterministic numeric deltas."
            )

        other_offers = [
            draft.offers_by_id[offer_id]
            for offer_id in draft.selected_offer_ids
            if offer_id != draft.base_offer_id
        ]
        other_non_monetary_items: list[str] = []
        for offer in other_offers:
            for item in (get_path(offer.payload, "non_monetary_summary_bullets") or []):
                if isinstance(item, str) and item.strip() != "":
                    other_non_monetary_items.append(item)
        unique_base = [item for item in base_non_monetary if item not in other_non_monetary_items]
        missing_items = [item for item in other_non_monetary_items if item not in base_non_monetary]
        missing_unique = sorted(set(missing_items))
        return (
            "Base offer narrative across all other offers:\n"
            f"- Unique strengths: {', '.join(unique_base) if unique_base else 'No unique strengths found'}.\n"
            f"- Unique weaknesses/missing-item downsides: {', '.join(missing_unique) if missing_unique else 'No clear missing-item downside'}.\n"
            "- Summary: Use deterministic metric gaps to weigh tradeoffs against these non-monetary themes."
        )

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
