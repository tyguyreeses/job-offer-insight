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
    queued_responses: list[Any]
    calls: list[dict[str, object]]

    def create(self, **kwargs: object) -> Any:
        self.calls.append(dict(kwargs))
        if len(self.queued_responses) == 0:
            raise AssertionError("No fake responses configured.")
        return self.queued_responses.pop(0)


@dataclass
class _FakeClient:
    queued_responses: list[Any]
    calls: list[dict[str, object]]

    @property
    def responses(self) -> _FakeResponses:
        return _FakeResponses(queued_responses=self.queued_responses, calls=self.calls)


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
        lambda _config: _FakeClient(queued_responses=[response], calls=[]),
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
        lambda _config: _FakeClient(queued_responses=[response], calls=[]),
    )

    with pytest.raises(AgentExecutionError) as exc:
        _build_agent().run("input")

    message = str(exc.value)
    assert "response_summary=" in message
    assert "output_item_types" in message


def test_non_structured_agent_retries_incomplete_response_with_higher_output_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    first_response = {
        "id": "resp_incomplete",
        "status": "incomplete",
        "output_text": "",
        "output": [{"type": "reasoning"}],
        "incomplete_details": {"reason": "max_output_tokens"},
        "usage": {"output_tokens": 300, "total_tokens": 1200},
    }
    second_response = {
        "id": "resp_complete",
        "status": "completed",
        "output_text": "Final comparison summary",
        "output": [],
        "usage": {"output_tokens": 480, "total_tokens": 1380},
    }
    fake_client = _FakeClient(queued_responses=[first_response, second_response], calls=calls)
    monkeypatch.setattr(
        agent_runtime_module,
        "_build_client",
        lambda _config: fake_client,
    )

    result = _build_agent().run("input")

    assert result == "Final comparison summary"
    assert len(calls) == 2
    assert calls[0]["max_output_tokens"] == 300
    assert calls[1]["max_output_tokens"] == 600


def test_non_structured_agent_includes_reasoning_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    response = {
        "id": "resp_reasoning",
        "status": "completed",
        "output_text": "ok",
        "output": [],
    }
    fake_client = _FakeClient(queued_responses=[response], calls=calls)
    monkeypatch.setattr(
        agent_runtime_module,
        "_build_client",
        lambda _config: fake_client,
    )
    agent = NonStructuredAgent(
        agent=AgentDefinition(
            name="comparison_one_to_one",
            type="non-structured",
            enabled=True,
            model="gpt-5.2",
            prompt="prompt",
            max_output_tokens=300,
            tools=[],
            reasoning={"effort": "medium"},
        ),
        openai_config=OpenAISection(),
    )

    result = agent.run("input")

    assert result == "ok"
    assert calls[0]["reasoning"] == {"effort": "medium"}
