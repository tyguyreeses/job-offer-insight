"""OpenAI client factory shared by GenAI runtime components."""

from __future__ import annotations

import os

from openai import OpenAI

from ..utils.config_types import OpenAISection


class OpenAIClientConfigError(RuntimeError):
    """Raised when OpenAI client configuration is invalid at runtime."""


def build_openai_client(config: OpenAISection) -> OpenAI:
    api_key = os.getenv(config.api_key_env_var)
    if not api_key:
        raise OpenAIClientConfigError(
            f"OpenAI API key environment variable '{config.api_key_env_var}' is unset."
        )
    return OpenAI(api_key=api_key, timeout=config.timeout_seconds)
