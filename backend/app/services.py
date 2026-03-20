from __future__ import annotations

from dataclasses import dataclass

from .models import Offer


@dataclass(frozen=True)
class OfferMetrics:
    total_comp_annual: float
    total_comp_year1: float
    total_comp_col_adjusted: float


def compute_metrics(offer: Offer) -> OfferMetrics:
    annual = offer.base_salary + offer.annual_bonus + offer.annual_equity
    year1 = annual + offer.sign_on_bonus
    adjusted = annual / offer.col_index
    return OfferMetrics(
        total_comp_annual=round(annual, 2),
        total_comp_year1=round(year1, 2),
        total_comp_col_adjusted=round(adjusted, 2),
    )
