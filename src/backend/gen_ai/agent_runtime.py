"""Reusable OpenAI agent runtime primitives."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from ..utils.config_types import OpenAISection
from ..utils.logging import get_logger
from .agent_registry import AgentDefinition
from .client import OpenAIClientConfigError, build_openai_client

ModelT = TypeVar("ModelT", bound=BaseModel)
_LOGGER = get_logger(__name__)


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
    response_summary: dict[str, object]


@dataclass(frozen=True)
class NonStructuredAgent:
    agent: AgentDefinition
    openai_config: OpenAISection

    def run(self, user_input: str) -> str:
        run_result = self.run_with_tools(user_input=user_input, tools=None)
        output_text = run_result.output_text
        if output_text.strip() != "":
            return output_text

        initial_summary = run_result.response_summary
        if _should_retry_for_incomplete_no_text(initial_summary):
            retry_max_output_tokens = _retry_max_output_tokens(self.agent.max_output_tokens)
            _LOGGER.warning(
                "Non-structured agent returned incomplete response without text. "
                "Retrying with higher max_output_tokens. agent=%s previous_max_output_tokens=%s retry_max_output_tokens=%s response_summary=%s",
                self.agent.name,
                self.agent.max_output_tokens,
                retry_max_output_tokens,
                initial_summary,
            )
            retry_result = self.run_with_tools(
                user_input=user_input,
                tools=None,
                max_output_tokens_override=retry_max_output_tokens,
            )
            retry_output = retry_result.output_text
            if retry_output.strip() != "":
                return retry_output
            _LOGGER.warning(
                "Non-structured agent retry also produced no text output. agent=%s response_summary=%s",
                self.agent.name,
                retry_result.response_summary,
            )
            raise AgentExecutionError(
                "Non-structured agent response did not include text output after retry. "
                f"initial_response_summary={initial_summary}; retry_response_summary={retry_result.response_summary}"
            )

        if output_text.strip() == "":
            _LOGGER.warning(
                "Non-structured agent produced no text output. agent=%s response_summary=%s",
                self.agent.name,
                initial_summary,
            )
            raise AgentExecutionError(
                "Non-structured agent response did not include text output. "
                f"response_summary={initial_summary}"
            )
        return output_text

    def run_with_tools(
        self,
        *,
        user_input: str,
        tools: list[FunctionToolDefinition] | None,
        max_output_tokens_override: int | None = None,
    ) -> NonStructuredRunResult:
        client = _build_client(self.openai_config)
        request_kwargs: dict[str, object] = {
            "model": self.agent.model,
            "input": [
                {"role": "system", "content": self.agent.prompt},
                {"role": "user", "content": user_input},
            ],
            "max_output_tokens": max_output_tokens_override or self.agent.max_output_tokens,
        }
        if self.agent.reasoning is not None:
            request_kwargs["reasoning"] = self.agent.reasoning
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
        parsed_output_text = _extract_response_text(response)
        response_summary = _build_response_summary(response)
        return NonStructuredRunResult(
            output_text=parsed_output_text,
            tool_calls=_parse_tool_calls(response),
            response_summary=response_summary,
        )


def _extract_response_text(response: object) -> str:
    output_text = _value_from(response, "output_text")
    if isinstance(output_text, str) and output_text.strip() != "":
        return output_text

    output = _value_from(response, "output")
    if not isinstance(output, list):
        return output_text if isinstance(output_text, str) else ""

    chunks: list[str] = []
    for item in output:
        if _value_from(item, "type") != "message":
            continue
        content = _value_from(item, "content")
        if not isinstance(content, list):
            continue
        for content_item in content:
            if _value_from(content_item, "type") != "output_text":
                continue
            text_value = _value_from(content_item, "text")
            if isinstance(text_value, str) and text_value.strip() != "":
                chunks.append(text_value)
    return "\n".join(chunks)


def _build_response_summary(response: object) -> dict[str, object]:
    output = _value_from(response, "output")
    output_items = output if isinstance(output, list) else []

    output_types: list[str] = []
    content_types: list[str] = []
    for item in output_items:
        output_type = _value_from(item, "type")
        if isinstance(output_type, str):
            output_types.append(output_type)
        content = _value_from(item, "content")
        if not isinstance(content, list):
            continue
        for content_item in content:
            content_type = _value_from(content_item, "type")
            if isinstance(content_type, str):
                content_types.append(content_type)

    return {
        "id": _value_from(response, "id"),
        "status": _value_from(response, "status"),
        "model": _value_from(response, "model"),
        "incomplete_details": _value_from(response, "incomplete_details"),
        "output_text_len": len((_value_from(response, "output_text") or "")),
        "usage_output_tokens": _usage_value(response, "output_tokens"),
        "usage_total_tokens": _usage_value(response, "total_tokens"),
        "output_item_count": len(output_items),
        "output_item_types": output_types,
        "message_content_types": content_types,
    }


def _value_from(obj: object, name: str) -> object | None:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _usage_value(response: object, key: str) -> object | None:
    usage = _value_from(response, "usage")
    if usage is None:
        return None
    return _value_from(usage, key)


def _should_retry_for_incomplete_no_text(response_summary: dict[str, object]) -> bool:
    status = response_summary.get("status")
    return status == "incomplete"


def _retry_max_output_tokens(base_max_output_tokens: int) -> int:
    return min(base_max_output_tokens * 2, 6000)


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
        request_kwargs: dict[str, object] = {
            "model": self.agent.model,
            "input": [
                {"role": "system", "content": self.agent.prompt},
                {"role": "user", "content": user_input},
            ],
            "max_output_tokens": self.agent.max_output_tokens,
            "text_format": output_model,
        }
        if self.agent.reasoning is not None:
            request_kwargs["reasoning"] = self.agent.reasoning

        parsed = client.responses.parse(**request_kwargs)
        output_parsed = parsed.output_parsed
        if output_parsed is None:
            raise AgentExecutionError("Structured agent did not return parsed output.")
        return output_parsed


def _build_client(config: OpenAISection):
    try:
        return build_openai_client(config)
    except OpenAIClientConfigError as exc:
        raise AgentExecutionError(str(exc)) from exc
