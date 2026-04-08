"""Runtime dependency container and DI provider helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Depends, Request

from .domain.services.interfaces import ComparisonService, OfferService
from .domain.services.offer_service import Stage4OfferService
from .domain.services.placeholders import UnimplementedComparisonService
from .storage.db import SQLiteDatabase, build_sqlite_database
from .storage.repositories.comparison_repository import SQLiteComparisonRepository
from .storage.repositories.interfaces import ComparisonRepository, OfferRepository
from .storage.repositories.offer_repository import SQLiteOfferRepository
from .utils.config_types import RuntimeConfig


@dataclass(frozen=True)
class RuntimeContainer:
    """Shared runtime state required by routers and DI providers."""

    config: RuntimeConfig
    logger: logging.Logger
    debug: bool
    database: SQLiteDatabase
    offer_repository: OfferRepository
    comparison_repository: ComparisonRepository
    offer_service: OfferService
    comparison_service: ComparisonService


def build_runtime_container(config: RuntimeConfig, logger: logging.Logger) -> RuntimeContainer:
    """Build Stage 4 runtime dependencies with SQLite-backed repositories."""
    database = build_sqlite_database(config.database)
    database.initialize()
    offer_repository = SQLiteOfferRepository(database=database)
    comparison_repository = SQLiteComparisonRepository(database=database)

    return RuntimeContainer(
        config=config,
        logger=logger,
        debug=logger.getEffectiveLevel() <= logging.DEBUG,
        database=database,
        offer_repository=offer_repository,
        comparison_repository=comparison_repository,
        offer_service=Stage4OfferService(offer_repository=offer_repository),
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
