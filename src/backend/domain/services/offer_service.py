"""Offer intake and CRUD orchestration for Stage 4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ...domain.models import OfferRecord
from ...gen_ai.protocols import Agent
from ...gen_ai.text_parser_agent import TextParserError
from ...storage.repositories.interfaces import OfferRepository

_REQUIRED_COMPENSATION_PATHS = (
    "compensation.annual_base_salary_usd",
    "compensation.hourly_rate_usd",
    "compensation.hours_per_week",
)


@dataclass(frozen=True)
class FieldPrompt:
    path: str
    required: bool
    message: str


@dataclass(frozen=True)
class IntakeResult:
    status: str
    errors: list[str]
    warnings: list[str]
    missing_field_prompts: list[FieldPrompt]
    offer: OfferRecord | None


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    return True


def _set_path(payload: dict[str, Any], path: str, value: Any) -> None:
    cursor = payload
    parts = path.split(".")
    for part in parts[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[parts[-1]] = value


def _get_path(payload: dict[str, Any], path: str) -> Any:
    cursor: Any = payload
    for part in path.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned == "":
            return None
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _merge_payloads(*parts: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for part in parts:
        for key, value in part.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = _merge_payloads(merged[key], value)
            else:
                merged[key] = value
    return merged


def _normalize_compensation(payload: dict[str, Any]) -> None:
    compensation = payload.get("compensation")
    if compensation is None:
        compensation = {}
        payload["compensation"] = compensation
    if not isinstance(compensation, dict):
        raise ValueError("compensation must be an object")

    annual_base = _coerce_float(compensation.get("annual_base_salary_usd"))
    hourly_rate = _coerce_float(compensation.get("hourly_rate_usd"))
    hours_per_week = _coerce_float(compensation.get("hours_per_week"))

    if annual_base is not None:
        compensation["annual_base_salary_usd"] = annual_base
    if hourly_rate is not None:
        compensation["hourly_rate_usd"] = hourly_rate
    if hours_per_week is not None:
        compensation["hours_per_week"] = hours_per_week

    if annual_base is None and hourly_rate is not None and hours_per_week is not None:
        compensation["annual_base_salary_usd"] = hourly_rate * hours_per_week * 52


_OPTIONAL_FIELD_DEFAULTS: dict[str, Any] = {
    "location": "",
    "employment_type": "",
    "work_model": "",
    "compensation.signing_bonus_usd": None,
    "compensation.target_bonus_percent": None,
    "monetary_benefits.retirement_match_percent": None,
    "monetary_benefits.retirement_match_cap_usd": None,
    "monetary_benefits.health_insurance_employer_monthly_usd": None,
    "monetary_benefits.hsa_employer_annual_usd": None,
    "monetary_benefits.equity_grant_usd": None,
    "monetary_benefits.equity_vesting_schedule": "",
    "monetary_benefits.other_monetary_benefits": [],
    "non_monetary_benefits.mission_alignment_notes": "",
    "non_monetary_benefits.culture_notes": "",
    "non_monetary_benefits.growth_notes": "",
    "non_monetary_benefits.wellness_notes": "",
    "non_monetary_benefits.pto_days": None,
    "non_monetary_benefits.remote_flexibility_notes": "",
    "non_monetary_benefits.other_non_monetary_benefits": [],
}


def _collect_missing_prompts(payload: dict[str, Any]) -> list[FieldPrompt]:
    prompts: list[FieldPrompt] = []

    if not _is_present(payload.get("company_name")):
        prompts.append(
            FieldPrompt(
                path="company_name",
                required=True,
                message="Provide company_name to save this offer.",
            )
        )
    if not _is_present(payload.get("role_title")):
        prompts.append(
            FieldPrompt(
                path="role_title",
                required=True,
                message="Provide role_title to save this offer.",
            )
        )

    annual_base = _coerce_float(_get_path(payload, "compensation.annual_base_salary_usd"))
    hourly_rate = _coerce_float(_get_path(payload, "compensation.hourly_rate_usd"))
    hours_per_week = _coerce_float(_get_path(payload, "compensation.hours_per_week"))
    has_base_path = annual_base is not None or (hourly_rate is not None and hours_per_week is not None)

    if not has_base_path:
        for path in _REQUIRED_COMPENSATION_PATHS:
            prompts.append(
                FieldPrompt(
                    path=path,
                    required=True,
                    message="Provide required base-pay information to save this offer.",
                )
            )

    for path in _OPTIONAL_FIELD_DEFAULTS:
        if not _is_present(_get_path(payload, path)):
            prompts.append(
                FieldPrompt(
                    path=path,
                    required=False,
                    message=(
                        f"`{path}` is missing. Provide a value or confirm it is not part of this offer."
                    ),
                )
            )

    return prompts


def _apply_optional_omissions(
    payload: dict[str, Any],
    omission_confirmations: dict[str, bool] | None,
) -> tuple[dict[str, Any], list[str], list[FieldPrompt]]:
    confirmations = omission_confirmations or {}
    warnings: list[str] = []
    unresolved_prompts: list[FieldPrompt] = []

    for path, default_value in _OPTIONAL_FIELD_DEFAULTS.items():
        if _is_present(_get_path(payload, path)):
            continue
        if confirmations.get(path, False):
            _set_path(payload, path, default_value)
            warnings.append(f"Stored blank value for omitted field: {path}")
            continue
        unresolved_prompts.append(
            FieldPrompt(
                path=path,
                required=False,
                message=(
                    f"`{path}` is missing. Provide a value or confirm it is not part of this offer."
                ),
            )
        )

    return payload, warnings, unresolved_prompts


def _validate_required(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not _is_present(payload.get("company_name")):
        errors.append("company_name is required")
    if not _is_present(payload.get("role_title")):
        errors.append("role_title is required")

    annual_base = _coerce_float(_get_path(payload, "compensation.annual_base_salary_usd"))
    hourly_rate = _coerce_float(_get_path(payload, "compensation.hourly_rate_usd"))
    hours_per_week = _coerce_float(_get_path(payload, "compensation.hours_per_week"))
    has_base_path = annual_base is not None or (hourly_rate is not None and hours_per_week is not None)

    if not has_base_path:
        errors.append(
            "Provide compensation.annual_base_salary_usd or both compensation.hourly_rate_usd and compensation.hours_per_week"
        )

    return errors


def _record_to_payload(record: OfferRecord) -> dict[str, Any]:
    payload = dict(record.payload)
    payload["id"] = record.id
    payload["company_name"] = record.company_name
    payload["role_title"] = record.role_title
    payload.setdefault("offer_meta", {})
    offer_meta = payload["offer_meta"]
    if isinstance(offer_meta, dict):
        offer_meta.setdefault("created_at", record.created_at)
        offer_meta["updated_at"] = record.updated_at
    return payload


@dataclass(frozen=True)
class Stage4OfferService:
    offer_repository: OfferRepository
    text_parser_agent: Agent

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "offer",
            "status": "stage_4_1_ready",
            "message": "Text intake, validation, missing-field prompts, and persistence are active.",
        }

    def intake_text_offer(
        self,
        *,
        text: str,
        omission_confirmations: dict[str, bool] | None = None,
        extracted_offer_overrides: dict[str, Any] | None = None,
    ) -> IntakeResult:
        try:
            extracted_payload = self.text_parser_agent.parse(text)
        except TextParserError as exc:
            return IntakeResult(
                status="extraction_failed",
                errors=[f"Unable to extract structured offer data: {exc}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        merged_payload = _merge_payloads(extracted_payload, extracted_offer_overrides or {})

        _normalize_compensation(merged_payload)

        required_errors = _validate_required(merged_payload)
        if required_errors:
            return IntakeResult(
                status="blocked_required_fields",
                errors=required_errors,
                warnings=[],
                missing_field_prompts=_collect_missing_prompts(merged_payload),
                offer=None,
            )

        merged_payload, warnings, unresolved_optional_prompts = _apply_optional_omissions(
            merged_payload,
            omission_confirmations,
        )

        if unresolved_optional_prompts:
            return IntakeResult(
                status="missing_information",
                errors=[],
                warnings=[],
                missing_field_prompts=unresolved_optional_prompts,
                offer=None,
            )

        now = datetime.now(UTC).isoformat()
        merged_payload.setdefault("offer_meta", {})
        offer_meta = merged_payload["offer_meta"]
        if isinstance(offer_meta, dict):
            offer_meta.setdefault("status", "active")
            offer_meta.setdefault("source_input_type", "text")
            offer_meta.setdefault("created_at", now)
            offer_meta["updated_at"] = now

        record = self.offer_repository.create(
            company_name=str(merged_payload["company_name"]),
            role_title=str(merged_payload["role_title"]),
            payload=merged_payload,
        )

        return IntakeResult(
            status="saved",
            errors=[],
            warnings=warnings,
            missing_field_prompts=[],
            offer=record,
        )

    def list_offers(self) -> list[OfferRecord]:
        return self.offer_repository.list_all()

    def get_offer(self, offer_id: str) -> OfferRecord | None:
        return self.offer_repository.get_by_id(offer_id)

    def update_offer(self, *, offer_id: str, payload: dict[str, Any]) -> IntakeResult:
        normalized_payload = dict(payload)
        _normalize_compensation(normalized_payload)

        required_errors = _validate_required(normalized_payload)
        if required_errors:
            return IntakeResult(
                status="blocked_required_fields",
                errors=required_errors,
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        existing = self.offer_repository.get_by_id(offer_id)
        if existing is None:
            return IntakeResult(
                status="not_found",
                errors=[f"Offer not found: {offer_id}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        updated = self.offer_repository.update(
            offer_id=offer_id,
            company_name=str(normalized_payload["company_name"]),
            role_title=str(normalized_payload["role_title"]),
            payload=normalized_payload,
        )
        if updated is None:
            return IntakeResult(
                status="not_found",
                errors=[f"Offer not found: {offer_id}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        return IntakeResult(
            status="saved",
            errors=[],
            warnings=[],
            missing_field_prompts=[],
            offer=updated,
        )

    def render_offer_payload(self, record: OfferRecord) -> dict[str, Any]:
        return _record_to_payload(record)
