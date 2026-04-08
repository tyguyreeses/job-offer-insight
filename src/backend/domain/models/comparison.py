"""Saved comparison persistence model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComparisonRecord:
    id: str
    selected_offer_ids: list[str]
    summary_text: str
    note: str | None
    created_at: str
    updated_at: str
