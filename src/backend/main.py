"""Backend bootstrap entrypoint for local smoke checks."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .utils.config_loader import ConfigLoadError, load_config
    from .utils.logging import log_config_payload, setup_error_logger, setup_logger
except ImportError:  # Allows direct execution via `python src/backend/main.py`
    from utils.config_loader import ConfigLoadError, load_config
    from utils.logging import log_config_payload, setup_error_logger, setup_logger


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


def main() -> int:
    args = parse_args()
    config_path = resolve_config_path(args.config)

    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        logger = setup_error_logger()
        logger.error("Failed to load config: %s", exc)
        return 1

    logger = setup_logger(debug=args.debug, configured_level=config.logging.level)
    logger.info("Loaded config from %s", config_path)
    log_config_payload(logger, config.model_dump())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
