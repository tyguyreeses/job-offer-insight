"""Top-level API router composition."""

from __future__ import annotations

from fastapi import APIRouter

from .v1.health import router as health_router


def build_api_router() -> APIRouter:
    api_router = APIRouter(prefix="/api")
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(health_router, tags=["health"])
    api_router.include_router(v1_router)
    return api_router
