"""Stage 2 placeholder service implementations."""

from __future__ import annotations

from dataclasses import dataclass

from ...storage.repositories.interfaces import ComparisonRepository, OfferRepository


@dataclass(frozen=True)
class UnimplementedOfferService:
    offer_repository: OfferRepository

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "offer",
            "status": "placeholder",
            "message": "Offer behavior will be implemented in later stages.",
        }


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
