"""Text parsing agent that converts open-ended text to validated offer payloads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..utils.config_types import OpenAISection
from .agent_runtime import AgentExecutionError, NonStructuredAgent, StructuredOutputAgent
from .agent_registry import AgentRegistry


class TextParserError(RuntimeError):
    """Raised when parser agent output cannot be used safely."""


class CompensationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annual_base_salary_usd: float | None = Field(
        default=None,
        description="Annual base salary in USD for salaried offers.",
    )
    hourly_rate_usd: float | None = Field(
        default=None,
        description="Hourly pay rate in USD when compensation is hourly.",
    )
    hours_per_week: float | None = Field(
        default=None,
        description="Typical number of paid hours worked per week for hourly compensation.",
    )
    annualized_total_cash_usd: float | None = Field(
        default=None,
        description="Estimated annualized total cash compensation in USD.",
    )
    signing_bonus_usd: float | None = Field(
        default=None,
        description="One-time signing bonus amount in USD.",
    )
    target_bonus_percent: float | None = Field(
        default=None,
        description="Target annual bonus as a percent of base salary.",
    )


class MonetaryBenefitsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retirement_match_percent: float | None = Field(
        default=None,
        description="Employer retirement match percentage.",
    )
    retirement_match_cap_usd: float | None = Field(
        default=None,
        description="Annual USD cap for employer retirement match, if applicable.",
    )
    health_insurance_employer_monthly_usd: float | None = Field(
        default=None,
        description="Estimated employer-paid monthly health insurance value in USD.",
    )
    hsa_employer_annual_usd: float | None = Field(
        default=None,
        description="Annual employer contribution to HSA in USD.",
    )
    equity_grant_usd: float | None = Field(
        default=None,
        description="Estimated USD value of equity grant.",
    )
    equity_vesting_schedule: str | None = Field(
        default=None,
        description="Text description of equity vesting schedule.",
    )
    other_monetary_benefits: list[str] | None = Field(
        default=None,
        description="List of additional monetary benefits and stipends.",
    )


class NonMonetaryBenefitsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mission_alignment_notes: str | None = Field(
        default=None,
        description="Notes about mission alignment or meaningful impact.",
    )
    culture_notes: str | None = Field(
        default=None,
        description="Notes about team and company culture.",
    )
    growth_notes: str | None = Field(
        default=None,
        description="Notes about learning, mentorship, or career growth.",
    )
    wellness_notes: str | None = Field(
        default=None,
        description="Notes about wellness and quality-of-life benefits.",
    )
    pto_days: int | None = Field(
        default=None,
        description="Number of paid time off days per year.",
    )
    remote_flexibility_notes: str | None = Field(
        default=None,
        description="Notes describing remote flexibility and in-office expectations.",
    )
    other_non_monetary_benefits: list[str] | None = Field(
        default=None,
        description="List of additional non-monetary benefits.",
    )


class ExtractedOfferPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str | None = Field(
        default=None,
        description="Company name associated with the offer.",
    )
    role_title: str | None = Field(
        default=None,
        description="Job title for the offer.",
    )
    location: str | None = Field(
        default=None,
        description="Role location such as city/state or remote location context.",
    )
    employment_type: str | None = Field(
        default=None,
        description="Employment type, for example full_time, part_time, or contract.",
    )
    work_model: str | None = Field(
        default=None,
        description="Work model such as remote, hybrid, or on_site.",
    )
    compensation: CompensationPayload | None = Field(
        default=None,
        description="Compensation details for salary, hourly rates, and bonus targets.",
    )
    monetary_benefits: MonetaryBenefitsPayload | None = Field(
        default=None,
        description="Monetary benefits including retirement, insurance, and equity value.",
    )
    non_monetary_benefits: NonMonetaryBenefitsPayload | None = Field(
        default=None,
        description="Non-monetary benefits, culture, growth, and flexibility notes.",
    )


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
