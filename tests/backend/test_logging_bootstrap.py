from __future__ import annotations

import logging

from src.backend.utils.logging import setup_logger


def test_logger_uses_configured_level_without_debug_flag() -> None:
    logger = setup_logger(debug=False, configured_level="INFO")
    assert logger.getEffectiveLevel() == logging.INFO


def test_logger_switches_to_debug_when_debug_flag_set() -> None:
    logger = setup_logger(debug=True, configured_level="INFO")
    assert logger.getEffectiveLevel() == logging.DEBUG
