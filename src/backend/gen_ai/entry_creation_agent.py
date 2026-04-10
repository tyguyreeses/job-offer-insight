"""Conversational entry-creation agent wrapper."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..utils.config_types import OpenAISection
from .agent_registry import AgentRegistry
from .agent_runtime import AgentExecutionError, NonStructuredAgent


class EntryCreationAgentError(RuntimeError):
    """Raised when the entry-creation agent cannot produce a usable reply."""


@dataclass(frozen=True)
class ConfiguredEntryCreationAgent:
    registry: AgentRegistry
    openai_config: OpenAISection

    def reply(self, *, transcript: list[dict[str, str]], state: dict[str, Any]) -> str:
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
        try:
            return NonStructuredAgent(agent=agent, openai_config=self.openai_config).run(user_input).strip()
        except AgentExecutionError as exc:
            raise EntryCreationAgentError(str(exc)) from exc
