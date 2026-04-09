"""Text parsing agent that converts open-ended text to validated offer payloads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from ..utils.config_types import OpenAISection
from .agent_runtime import AgentExecutionError, NonStructuredAgent, StructuredOutputAgent
from .agent_registry import AgentRegistry


class TextParserError(RuntimeError):
    """Raised when parser agent output cannot be used safely."""


class CompensationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annual_base_salary_usd: float | None = None
    hourly_rate_usd: float | None = None
    hours_per_week: float | None = None
    signing_bonus_usd: float | None = None
    target_bonus_percent: float | None = None


class MonetaryBenefitsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retirement_match_percent: float | None = None
    retirement_match_cap_usd: float | None = None
    health_insurance_employer_monthly_usd: float | None = None
    hsa_employer_annual_usd: float | None = None
    equity_grant_usd: float | None = None
    equity_vesting_schedule: str | None = None
    other_monetary_benefits: list[str] | None = None


class NonMonetaryBenefitsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_alignment_notes: str | None = None
    culture_notes: str | None = None
    growth_notes: str | None = None
    wellness_notes: str | None = None
    pto_days: int | None = None
    remote_flexibility_notes: str | None = None
    other_non_monetary_benefits: list[str] | None = None


class ExtractedOfferPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str | None = None
    role_title: str | None = None
    location: str | None = None
    employment_type: str | None = None
    work_model: str | None = None
    compensation: CompensationPayload | None = None
    monetary_benefits: MonetaryBenefitsPayload | None = None
    non_monetary_benefits: NonMonetaryBenefitsPayload | None = None


def _parse_json_payload(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(decoded, dict):
        return None
    validated = ExtractedOfferPayload.model_validate(decoded)
    return validated.model_dump(exclude_none=True)


@dataclass(frozen=True)
class ConfiguredTextParserAgent:
    registry: AgentRegistry
    openai_config: OpenAISection

    def parse(self, text: str) -> dict[str, Any]:
        json_payload = _parse_json_payload(text)
        if json_payload is not None:
            return json_payload

        agent = self.registry.get("text_parser")
        if not agent.enabled:
            raise TextParserError("Text parser agent is disabled and non-JSON input cannot be parsed.")

        try:
            if agent.type == "structured-output":
                parsed_model = StructuredOutputAgent(
                    agent=agent,
                    openai_config=self.openai_config,
                ).run(text, ExtractedOfferPayload)
                return parsed_model.model_dump(exclude_none=True)

            agent_output = NonStructuredAgent(
                agent=agent,
                openai_config=self.openai_config,
            ).run(text)
            decoded = json.loads(agent_output)
            if not isinstance(decoded, dict):
                raise TextParserError("Non-structured parser output was not a JSON object.")
            parsed_model = ExtractedOfferPayload.model_validate(decoded)
            return parsed_model.model_dump(exclude_none=True)
        except (ValidationError, AgentExecutionError) as exc:
            raise TextParserError(str(exc)) from exc
        except json.JSONDecodeError as exc:
            raise TextParserError("Non-structured parser output was not valid JSON.") from exc
