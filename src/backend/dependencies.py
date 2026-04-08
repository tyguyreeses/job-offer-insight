"""Runtime dependency container and DI provider helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Depends, Request

from .domain.services.interfaces import ComparisonService, OfferService
from .domain.services.placeholders import (
    UnimplementedComparisonService,
    UnimplementedOfferService,
)
from .storage.repositories.interfaces import ComparisonRepository, OfferRepository
from .storage.repositories.placeholders import (
    InMemoryPlaceholderComparisonRepository,
    InMemoryPlaceholderOfferRepository,
)
from .utils.config_types import RuntimeConfig


@dataclass(frozen=True)
class RuntimeContainer:
    """Shared runtime state required by routers and DI providers."""

    config: RuntimeConfig
    logger: logging.Logger
    debug: bool
    offer_repository: OfferRepository
    comparison_repository: ComparisonRepository
    offer_service: OfferService
    comparison_service: ComparisonService


def build_runtime_container(config: RuntimeConfig, logger: logging.Logger) -> RuntimeContainer:
    """Build placeholder dependency graph for Stage 2 wiring."""
    offer_repository = InMemoryPlaceholderOfferRepository()
    comparison_repository = InMemoryPlaceholderComparisonRepository()

    return RuntimeContainer(
        config=config,
        logger=logger,
        debug=logger.getEffectiveLevel() <= logging.DEBUG,
        offer_repository=offer_repository,
        comparison_repository=comparison_repository,
        offer_service=UnimplementedOfferService(offer_repository=offer_repository),
        comparison_service=UnimplementedComparisonService(
            comparison_repository=comparison_repository,
            offer_repository=offer_repository,
        ),
    )


def get_container(request: Request) -> RuntimeContainer:
    return request.app.state.runtime_container


def get_offer_service(
    container: RuntimeContainer = Depends(get_container),
) -> OfferService:
    return container.offer_service


def get_comparison_service(
    container: RuntimeContainer = Depends(get_container),
) -> ComparisonService:
    return container.comparison_service
