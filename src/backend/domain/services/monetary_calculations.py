"""Deterministic monetary summary calculators used by Stage 8."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...domain.offer_schema import get_path
from ...utils.config_types import TaxProfileSection


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


def _percent_to_ratio(value: float | None) -> float:
    if value is None:
        return 0.0
    return max(0.0, value) / 100.0


def _resolve_annual_base(payload: dict[str, Any]) -> float:
    annual_base = _coerce_number(get_path(payload, "compensation.annual_base_salary_usd"))
    if annual_base is not None:
        return annual_base
    hourly = _coerce_number(get_path(payload, "compensation.hourly_rate_usd"))
    hours = _coerce_number(get_path(payload, "compensation.hours_per_week"))
    if hourly is None or hours is None:
        return 0.0
    return hourly * hours * 52


def _resolve_total_cash(payload: dict[str, Any], annual_base: float) -> float:
    explicit = _coerce_number(get_path(payload, "compensation.annualized_total_cash_usd"))
    if explicit is not None:
        return explicit
    signing_bonus = _coerce_number(get_path(payload, "compensation.signing_bonus_usd")) or 0.0
    target_bonus_percent = _percent_to_ratio(
        _coerce_number(get_path(payload, "compensation.target_bonus_percent"))
    )
    return annual_base + signing_bonus + (annual_base * target_bonus_percent)


def _resolve_retirement_match_value(payload: dict[str, Any], annual_base: float) -> float:
    match_percent = _percent_to_ratio(
        _coerce_number(get_path(payload, "monetary_benefits.retirement_match_percent"))
    )
    if match_percent <= 0:
        return 0.0
    raw_value = annual_base * match_percent
    cap = _coerce_number(get_path(payload, "monetary_benefits.retirement_match_cap_usd"))
    if cap is None:
        return raw_value
    return min(raw_value, cap)


def _resolve_tax_profile(payload: dict[str, Any], config: TaxProfileSection) -> tuple[str, str, float]:
    override_state = str(get_path(payload, "tax_overrides.state") or "").strip().upper()
    resolved_state = override_state if len(override_state) == 2 else config.default_state

    override_status = str(get_path(payload, "tax_overrides.filing_status") or "").strip().lower()
    if override_status not in {"single", "married_joint", "head_of_household"}:
        override_status = ""
    resolved_status = override_status or config.default_filing_status

    override_pre_tax = _coerce_number(get_path(payload, "tax_overrides.pre_tax_deduction_percent"))
    resolved_pre_tax = (
        override_pre_tax
        if override_pre_tax is not None
        else config.default_pre_tax_deduction_percent
    )
    resolved_pre_tax = min(max(resolved_pre_tax, 0.0), 100.0)
    return resolved_state, resolved_status, resolved_pre_tax


@dataclass(frozen=True)
class DerivedMonetarySummary:
    estimated_total_annual_monetary_benefits_usd: float
    estimated_monthly_take_home_usd: float
    tax_profile_used: dict[str, Any]
    explanation: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "estimated_total_annual_monetary_benefits_usd": round(
                self.estimated_total_annual_monetary_benefits_usd, 2
            ),
            "estimated_monthly_take_home_usd": round(self.estimated_monthly_take_home_usd, 2),
            "tax_profile_used": self.tax_profile_used,
            "explanation": self.explanation,
        }


def compute_derived_monetary_summary(
    payload: dict[str, Any],
    *,
    tax_config: TaxProfileSection,
) -> DerivedMonetarySummary:
    annual_base = _resolve_annual_base(payload)
    total_cash = _resolve_total_cash(payload, annual_base)
    retirement = _resolve_retirement_match_value(payload, annual_base)
    equity = _coerce_number(get_path(payload, "monetary_benefits.equity_grant_usd")) or 0.0
    health_monthly = (
        _coerce_number(get_path(payload, "monetary_benefits.health_insurance_employer_monthly_usd"))
        or 0.0
    )
    dental_monthly = (
        _coerce_number(get_path(payload, "monetary_benefits.dental_insurance_employer_monthly_usd"))
        or 0.0
    )
    hsa_annual = _coerce_number(get_path(payload, "monetary_benefits.hsa_employer_annual_usd")) or 0.0

    estimated_total = (
        total_cash
        + retirement
        + equity
        + (health_monthly * 12.0)
        + (dental_monthly * 12.0)
        + hsa_annual
    )

    state, filing_status, pre_tax_percent = _resolve_tax_profile(payload, tax_config)
    state_rate = tax_config.state_tax_rates.get(state, 0.0)
    total_tax_rate = min(0.95, tax_config.federal_tax_rate + tax_config.fica_tax_rate + state_rate)
    taxable_income = total_cash * (1.0 - (pre_tax_percent / 100.0))
    monthly_take_home = max(0.0, taxable_income * (1.0 - total_tax_rate) / 12.0)

    explanation = (
        "Monthly take-home uses deterministic defaults and optional overrides: "
        f"federal={tax_config.federal_tax_rate:.2%}, "
        f"fica={tax_config.fica_tax_rate:.2%}, "
        f"state({state})={state_rate:.2%}, "
        f"pre-tax={pre_tax_percent:.1f}%."
    )
    return DerivedMonetarySummary(
        estimated_total_annual_monetary_benefits_usd=estimated_total,
        estimated_monthly_take_home_usd=monthly_take_home,
        tax_profile_used={
            "state": state,
            "filing_status": filing_status,
            "pre_tax_deduction_percent": pre_tax_percent,
            "federal_tax_rate": tax_config.federal_tax_rate,
            "fica_tax_rate": tax_config.fica_tax_rate,
            "state_tax_rate": state_rate,
        },
        explanation=explanation,
    )
