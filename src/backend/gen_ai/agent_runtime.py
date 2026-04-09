"""Reusable OpenAI agent runtime primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from ..utils.config_types import OpenAISection
from .agent_registry import AgentDefinition
from .client import OpenAIClientConfigError, build_openai_client

ModelT = TypeVar("ModelT", bound=BaseModel)


class AgentExecutionError(RuntimeError):
    """Raised when an agent cannot return usable output."""


@dataclass(frozen=True)
class NonStructuredAgent:
    agent: AgentDefinition
    openai_config: OpenAISection

    def run(self, user_input: str) -> str:
        client = _build_client(self.openai_config)
        response = client.responses.create(
            model=self.agent.model,
            input=[
                {"role": "system", "content": self.agent.prompt},
                {"role": "user", "content": user_input},
            ],
            max_output_tokens=self.agent.max_output_tokens,
        )
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or output_text.strip() == "":
            raise AgentExecutionError("Non-structured agent response did not include text output.")
        return output_text


@dataclass(frozen=True)
class StructuredOutputAgent:
    agent: AgentDefinition
    openai_config: OpenAISection

    def run(self, user_input: str, output_model: type[ModelT]) -> ModelT:
        client = _build_client(self.openai_config)
        parsed = client.responses.parse(
            model=self.agent.model,
            input=[
                {"role": "system", "content": self.agent.prompt},
                {"role": "user", "content": user_input},
            ],
            max_output_tokens=self.agent.max_output_tokens,
            text_format=output_model,
        )
        output_parsed = parsed.output_parsed
        if output_parsed is None:
            raise AgentExecutionError("Structured agent did not return parsed output.")
        return output_parsed


def _build_client(config: OpenAISection):
    try:
        return build_openai_client(config)
    except OpenAIClientConfigError as exc:
        raise AgentExecutionError(str(exc)) from exc
