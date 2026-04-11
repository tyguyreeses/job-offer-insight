"""Saved comparison persistence model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ComparisonRecord:
    id: str
    comparison_mode: Literal["one_to_one", "one_to_all"]
    base_offer_id: str
    selected_offer_ids: list[str]
    summary_text: str
    note: str | None
    created_at: str
    updated_at: str
