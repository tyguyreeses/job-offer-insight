"""Backend bootstrap and FastAPI application wiring for Stage 2."""

from __future__ import annotations

import argparse
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.backend.api.router import build_api_router
from src.backend.dependencies import RuntimeContainer, build_runtime_container
from src.backend.utils.config_loader import ConfigLoadError, load_config
from src.backend.utils.logging import (
    get_logger,
    log_config_payload,
    setup_error_logger,
    setup_logger,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Offer Insight backend bootstrap")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("src/config.yaml"),
        help="Path to runtime YAML config file.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Force debug logging regardless of configured logging level.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the HTTP server after successful bootstrap validation.",
    )
    return parser.parse_args()


def resolve_config_path(config_path: Path) -> Path:
    """Resolve config path from cwd, with fallback to `src/<config_path>`."""
    if config_path.exists():
        return config_path
    if config_path.is_absolute():
        return config_path

    src_fallback = Path("src") / config_path
    if src_fallback.exists():
        return src_fallback
    return config_path


def _build_lifespan(container: RuntimeContainer):
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        container.logger.info("Backend startup complete")
        yield
        container.logger.info("Backend shutdown complete")

    return lifespan


def create_app(container: RuntimeContainer) -> FastAPI:
    app = FastAPI(title=container.config.app.name, lifespan=_build_lifespan(container))
    app.state.runtime_container = container
    app.include_router(build_api_router())

    @app.get("/")
    def root() -> dict[str, str]:
        return {"service": container.config.app.name, "status": "running"}

    return app


def build_app_from_config_path(config_path: Path, debug: bool) -> FastAPI:
    config = load_config(config_path)
    logger = setup_logger(
        debug=debug,
        configured_level=config.logging.level,
        include_timestamps=config.logging.include_timestamps,
        json_logs=config.logging.json_logs,
    )
    log_config_payload(logger, config.model_dump())
    container = build_runtime_container(config=config, logger=logger)
    return create_app(container)


def _run_uvicorn(app: FastAPI, config_path: Path, logger: logging.Logger) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        logger.error("Cannot serve app because uvicorn is not installed: %s", exc)
        return 1

    app_config = app.state.runtime_container.config.app
    logger.info("Serving app using config at %s", config_path)
    uvicorn.run(
        app,
        host=app_config.host,
        port=app_config.port,
        log_level="debug" if app.state.runtime_container.debug else "info",
    )
    return 0


def main() -> int:
    args = parse_args()
    config_path = resolve_config_path(args.config)

    try:
        app = build_app_from_config_path(config_path=config_path, debug=args.debug)
    except ConfigLoadError as exc:
        logger = setup_error_logger()
        logger.error("Failed to load config: %s", exc)
        return 1

    logger = app.state.runtime_container.logger
    get_logger(__name__).debug("Application logger initialized at level %s", logger.getEffectiveLevel())
    logger.info("Loaded config from %s", config_path)
    if args.serve:
        return _run_uvicorn(app, config_path, logger)
    logger.info("Bootstrap completed without --serve; exiting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
