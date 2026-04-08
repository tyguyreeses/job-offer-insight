"""Health and readiness endpoint surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...dependencies import RuntimeContainer, get_container

router = APIRouter()


@router.get("/health")
def health(container: RuntimeContainer = Depends(get_container)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": container.config.app.name,
    }


@router.get("/readiness")
def readiness(container: RuntimeContainer = Depends(get_container)) -> dict[str, object]:
    repositories_ready = (
        container.offer_repository.ping() and container.comparison_repository.ping()
    )
    components = {
        "config_loaded": True,
        "logger_configured": True,
        "repositories_ready": repositories_ready,
        "services_wired": bool(container.offer_service and container.comparison_service),
    }
    status = "ready" if all(components.values()) else "not_ready"
    return {
        "status": status,
        "components": components,
    }
