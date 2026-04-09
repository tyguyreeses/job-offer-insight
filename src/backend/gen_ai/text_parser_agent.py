"""Text parsing agent that converts open-ended text to validated offer payloads."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Protocol

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, ValidationError

from ..utils.config_types import OpenAISection
from .framework import AgentRegistry


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


class TextParserAgent(Protocol):
    def parse(self, text: str) -> dict[str, Any]:
        """Parse intake text into schema-aligned offer payload fields."""


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned == "":
            return None
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    validated = ExtractedOfferPayload.model_validate(payload)
    return validated.model_dump(exclude_none=True)


def _extract_json_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {}
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        return {}
    if not isinstance(decoded, dict):
        return {}
    return _validate_payload(decoded)


def _extract_fallback_payload(text: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    company_match = re.search(r"(?:company(?: name)?)[\\s:=-]+(.+)", text, flags=re.IGNORECASE)
    if company_match:
        payload["company_name"] = company_match.group(1).strip()

    role_match = re.search(r"(?:role|title|role title)[\\s:=-]+(.+)", text, flags=re.IGNORECASE)
    if role_match:
        payload["role_title"] = role_match.group(1).strip()

    annual_match = re.search(
        r"(?:annual(?: base)? salary|base salary)[^0-9$]*([$]?[0-9][0-9,]*(?:\\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )
    hourly_match = re.search(
        r"(?:hourly(?: rate)?|hourly pay)[^0-9$]*([$]?[0-9][0-9,]*(?:\\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )
    hours_match = re.search(
        r"(?:hours\\s*/\\s*week|hours per week)[^0-9]*([0-9]+(?:\\.[0-9]+)?)",
        text,
        flags=re.IGNORECASE,
    )

    compensation: dict[str, Any] = {}
    annual_value = _coerce_float(annual_match.group(1)) if annual_match else None
    hourly_value = _coerce_float(hourly_match.group(1)) if hourly_match else None
    hours_value = _coerce_float(hours_match.group(1)) if hours_match else None

    if annual_value is not None:
        compensation["annual_base_salary_usd"] = annual_value
    if hourly_value is not None:
        compensation["hourly_rate_usd"] = hourly_value
    if hours_value is not None:
        compensation["hours_per_week"] = hours_value
    if compensation:
        payload["compensation"] = compensation

    return _validate_payload(payload)


def _get_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    raise TextParserError("Agent response did not include text output.")


@dataclass(frozen=True)
class ConfiguredTextParserAgent:
    registry: AgentRegistry
    openai_config: OpenAISection
    logger: logging.Logger

    def parse(self, text: str) -> dict[str, Any]:
        json_payload = _extract_json_payload(text)
        if json_payload:
            return json_payload

        agent = self.registry.get("text_parser")
        if not agent.enabled:
            return _extract_fallback_payload(text)

        api_key = os.getenv(self.openai_config.api_key_env_var)
        if not api_key:
            self.logger.warning(
                "OpenAI API key environment variable '%s' is unset; falling back to heuristic text parsing.",
                self.openai_config.api_key_env_var,
            )
            return _extract_fallback_payload(text)

        try:
            payload = self._parse_with_agent(text=text, api_key=api_key)
            return _validate_payload(payload)
        except (TextParserError, ValidationError, json.JSONDecodeError) as exc:
            raise TextParserError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - depends on network/provider runtime.
            self.logger.warning(
                "AI parser agent failed (%s); falling back to heuristic text parsing.",
                exc,
            )
            return _extract_fallback_payload(text)

    def _parse_with_agent(self, *, text: str, api_key: str) -> dict[str, Any]:
        agent = self.registry.get("text_parser")
        client = OpenAI(api_key=api_key, timeout=self.openai_config.timeout_seconds)
        response = client.responses.create(
            model=agent.model,
            input=[
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=agent.temperature,
            max_output_tokens=agent.max_output_tokens,
        )
        response_text = _get_response_text(response).strip()
        try:
            decoded = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise TextParserError("Agent returned non-JSON output for text parsing.") from exc

        if not isinstance(decoded, dict):
            raise TextParserError("Agent returned JSON that is not an object.")
        return decoded
