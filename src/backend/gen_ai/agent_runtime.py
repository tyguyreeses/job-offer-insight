"""Reusable OpenAI agent runtime primitives."""

from __future__ import annotations

import json
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
class FunctionToolDefinition:
    name: str
    description: str


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, object]


@dataclass(frozen=True)
class NonStructuredRunResult:
    output_text: str
    tool_calls: list[ToolCall]


@dataclass(frozen=True)
class NonStructuredAgent:
    agent: AgentDefinition
    openai_config: OpenAISection

    def run(self, user_input: str) -> str:
        run_result = self.run_with_tools(user_input=user_input, tools=None)
        output_text = run_result.output_text
        if output_text.strip() == "":
            raise AgentExecutionError("Non-structured agent response did not include text output.")
        return output_text

    def run_with_tools(
        self,
        *,
        user_input: str,
        tools: list[FunctionToolDefinition] | None,
    ) -> NonStructuredRunResult:
        client = _build_client(self.openai_config)
        request_kwargs: dict[str, object] = {
            "model": self.agent.model,
            "input": [
                {"role": "system", "content": self.agent.prompt},
                {"role": "user", "content": user_input},
            ],
            "max_output_tokens": self.agent.max_output_tokens,
        }
        if tools:
            request_kwargs["tools"] = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                }
                for tool in tools
            ]
            request_kwargs["tool_choice"] = "auto"

        response = client.responses.create(**request_kwargs)
        output_text = getattr(response, "output_text", None)
        parsed_output_text = output_text if isinstance(output_text, str) else ""
        return NonStructuredRunResult(
            output_text=parsed_output_text,
            tool_calls=_parse_tool_calls(response),
        )


def _parse_tool_calls(response: object) -> list[ToolCall]:
    output = getattr(response, "output", None)
    if not isinstance(output, list):
        return []

    tool_calls: list[ToolCall] = []
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type is None and isinstance(item, dict):
            item_type = item.get("type")
        if item_type != "function_call":
            continue

        name = getattr(item, "name", None)
        if name is None and isinstance(item, dict):
            name = item.get("name")
        if not isinstance(name, str) or name.strip() == "":
            continue

        arguments_raw = getattr(item, "arguments", None)
        if arguments_raw is None and isinstance(item, dict):
            arguments_raw = item.get("arguments")

        parsed_arguments: dict[str, object] = {}
        if isinstance(arguments_raw, str) and arguments_raw.strip() != "":
            try:
                decoded = json.loads(arguments_raw)
                if isinstance(decoded, dict):
                    parsed_arguments = decoded
            except json.JSONDecodeError:
                parsed_arguments = {}

        tool_calls.append(ToolCall(name=name, arguments=parsed_arguments))

    return tool_calls


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
