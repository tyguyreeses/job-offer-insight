from __future__ import annotations

import logging

from src.backend.utils.logging import APP_LOGGER_NAME, get_logger, setup_logger


def test_logger_uses_configured_level_without_debug_flag() -> None:
    logger = setup_logger(debug=False, configured_level="INFO")
    assert logger.getEffectiveLevel() == logging.INFO


def test_logger_switches_to_debug_when_debug_flag_set() -> None:
    logger = setup_logger(debug=True, configured_level="INFO")
    assert logger.getEffectiveLevel() == logging.DEBUG


def test_get_logger_returns_namespaced_logger_for_backend_module() -> None:
    logger = get_logger("src.backend.api.v1.offers")
    assert logger.name == f"{APP_LOGGER_NAME}.api.v1.offers"


def test_get_logger_preserves_app_logger_prefix() -> None:
    logger = get_logger(f"{APP_LOGGER_NAME}.custom")
    assert logger.name == f"{APP_LOGGER_NAME}.custom"


def test_debug_mode_keeps_third_party_loggers_quiet() -> None:
    setup_logger(debug=True, configured_level="INFO")
    assert logging.getLogger(APP_LOGGER_NAME).getEffectiveLevel() == logging.DEBUG


def test_logging_emits_only_app_namespace(capsys) -> None:
    setup_logger(debug=True, configured_level="INFO")
    get_logger("src.backend.api.v1.offers").error("app log")
    logging.getLogger("python_multipart").error("third party log")
    captured = capsys.readouterr()
    assert "app log" in captured.err
    assert "third party log" not in captured.err
