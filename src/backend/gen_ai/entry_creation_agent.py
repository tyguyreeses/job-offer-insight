"""Conversational entry-creation agent wrapper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..utils.config_types import OpenAISection
from .agent_registry import AgentRegistry
from .agent_runtime import (
    AgentExecutionError,
    FunctionToolDefinition,
    NonStructuredAgent,
)
from .protocols import ChatAgentReply, ChatToolCall


class EntryCreationAgentError(RuntimeError):
    """Raised when the entry-creation agent cannot produce a usable reply."""


@dataclass(frozen=True)
class ConfiguredEntryCreationAgent:
    registry: AgentRegistry
    openai_config: OpenAISection

    def reply(self, *, transcript: list[dict[str, str]], state: dict[str, Any]) -> ChatAgentReply:
        agent = self.registry.get("entry_creation")
        if not agent.enabled:
            raise EntryCreationAgentError("Entry creation agent is disabled.")

        user_input = json.dumps(
            {
                "conversation_transcript": transcript,
                "structured_state": state,
                "instructions": (
                    "Reply as the assistant in a natural conversational tone. "
                    "Keep it concise and ask for missing required information when needed."
                ),
            },
            ensure_ascii=True,
        )
        tool_definitions = [
            FunctionToolDefinition(name=tool.name, description=tool.description)
            for tool in agent.tools
            if tool.enabled
        ]

        try:
            run_result = NonStructuredAgent(agent=agent, openai_config=self.openai_config).run_with_tools(
                user_input=user_input,
                tools=tool_definitions or None,
            )
            message = run_result.output_text.strip()
            if message == "" and len(run_result.tool_calls) == 0:
                raise AgentExecutionError(
                    "Entry creation agent response did not include text output or tool calls."
                )
            return ChatAgentReply(
                message=message,
                tool_calls=[
                    ChatToolCall(name=tool_call.name, arguments=tool_call.arguments)
                    for tool_call in run_result.tool_calls
                ],
            )
        except AgentExecutionError as exc:
            raise EntryCreationAgentError(str(exc)) from exc
