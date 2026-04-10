"""Text parsing agent that converts open-ended text to validated offer payloads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from ..domain.offer_schema import ConfiguredOfferSchema
from ..utils.config_types import OpenAISection
from .agent_registry import AgentRegistry
from .agent_runtime import AgentExecutionError, NonStructuredAgent, StructuredOutputAgent


class TextParserError(RuntimeError):
    """Raised when parser agent output cannot be used safely."""


@dataclass(frozen=True)
class ConfiguredTextParserAgent:
    registry: AgentRegistry
    openai_config: OpenAISection
    offer_schema: ConfiguredOfferSchema

    def _parse_json_payload(self, text: str) -> dict[str, Any] | None:
        stripped = text.strip()
        if not stripped:
            return None
        try:
            decoded = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if not isinstance(decoded, dict):
            return None
        validated = self.offer_schema.build_parser_model().model_validate(decoded)
        return validated.model_dump(exclude_none=True)

    def parse(self, text: str) -> dict[str, Any]:
        json_payload = self._parse_json_payload(text)
        if json_payload is not None:
            return json_payload

        agent = self.registry.get("parse_entry")
        if not agent.enabled:
            raise TextParserError(
                "Structured output parser agent is disabled and non-JSON input cannot be parsed."
            )

        output_model: type[BaseModel] = self.offer_schema.build_parser_model()

        try:
            if agent.type == "structured-output":
                parsed_model = StructuredOutputAgent(
                    agent=agent,
                    openai_config=self.openai_config,
                ).run(text, output_model)
                return parsed_model.model_dump(exclude_none=True)

            agent_output = NonStructuredAgent(
                agent=agent,
                openai_config=self.openai_config,
            ).run(text)
            decoded = json.loads(agent_output)
            if not isinstance(decoded, dict):
                raise TextParserError("Non-structured parser output was not a JSON object.")
            parsed_model = output_model.model_validate(decoded)
            return parsed_model.model_dump(exclude_none=True)
        except (ValidationError, AgentExecutionError) as exc:
            raise TextParserError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise TextParserError("Non-structured parser output was not valid JSON.") from exc
