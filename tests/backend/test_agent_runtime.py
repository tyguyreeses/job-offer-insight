from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

import src.backend.gen_ai.agent_runtime as agent_runtime_module
from src.backend.gen_ai.agent_registry import AgentDefinition
from src.backend.gen_ai.agent_runtime import AgentExecutionError, NonStructuredAgent
from src.backend.utils.config_types import OpenAISection


@dataclass
class _FakeResponses:
    response: Any

    def create(self, **_kwargs: object) -> Any:
        return self.response


@dataclass
class _FakeClient:
    response: Any

    @property
    def responses(self) -> _FakeResponses:
        return _FakeResponses(response=self.response)


def _build_agent() -> NonStructuredAgent:
    return NonStructuredAgent(
        agent=AgentDefinition(
            name="comparison_one_to_one",
            type="non-structured",
            enabled=True,
            model="gpt-5.2",
            prompt="prompt",
            max_output_tokens=300,
            tools=[],
        ),
        openai_config=OpenAISection(),
    )


def test_non_structured_agent_reads_text_from_message_content(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "id": "resp_123",
        "status": "completed",
        "output_text": "",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "First paragraph."},
                    {"type": "output_text", "text": "Second paragraph."},
                ],
            }
        ],
    }
    monkeypatch.setattr(
        agent_runtime_module,
        "_build_client",
        lambda _config: _FakeClient(response=response),
    )

    result = _build_agent().run("input")

    assert result == "First paragraph.\nSecond paragraph."


def test_non_structured_agent_raises_with_response_summary_when_text_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {
        "id": "resp_456",
        "status": "completed",
        "output_text": "",
        "output": [{"type": "function_call", "name": "noop", "arguments": "{}"}],
    }
    monkeypatch.setattr(
        agent_runtime_module,
        "_build_client",
        lambda _config: _FakeClient(response=response),
    )

    with pytest.raises(AgentExecutionError) as exc:
        _build_agent().run("input")

    message = str(exc.value)
    assert "response_summary=" in message
    assert "output_item_types" in message
