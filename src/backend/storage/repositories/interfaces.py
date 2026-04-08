"""Repository interfaces used for dependency boundaries."""

from __future__ import annotations

from typing import Protocol


class OfferRepository(Protocol):
    """Contract for offer persistence boundary."""

    def ping(self) -> bool:
        """Return whether the backing store appears reachable."""


class ComparisonRepository(Protocol):
    """Contract for comparison persistence boundary."""

    def ping(self) -> bool:
        """Return whether the backing store appears reachable."""
