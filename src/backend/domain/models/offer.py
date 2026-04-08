"""Offer persistence model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OfferRecord:
    id: str
    company_name: str
    role_title: str
    payload: dict[str, Any]
    created_at: str
    updated_at: str
