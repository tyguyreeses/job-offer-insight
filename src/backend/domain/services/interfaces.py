"""Service interfaces used by API and dependency wiring."""

from __future__ import annotations

from typing import Protocol


class OfferService(Protocol):
    """Contract for offer-focused orchestration behavior."""

    def describe_capabilities(self) -> dict[str, str]:
        """Return high-level service status/capabilities."""


class ComparisonService(Protocol):
    """Contract for comparison-focused orchestration behavior."""

    def describe_capabilities(self) -> dict[str, str]:
        """Return high-level service status/capabilities."""
