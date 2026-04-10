from __future__ import annotations

import pytest

from src.backend.domain.offer_schema import build_configured_offer_schema
from src.backend.gen_ai.agent_registry import AgentDefinition, AgentRegistry
from src.backend.gen_ai.text_parser_agent import ConfiguredTextParserAgent, TextParserError
from src.backend.utils.config_loader import load_default_config


def _build_agent(enabled: bool) -> ConfiguredTextParserAgent:
    config = load_default_config()
    registry = AgentRegistry(
        agents={
            "parse_entry": AgentDefinition(
                name="parse_entry",
                type="structured-output",
                enabled=enabled,
                model=config.agents.parse_entry.model,
                prompt="ignored for this test",
                max_output_tokens=config.agents.parse_entry.max_output_tokens,
                tools=[],
            )
        }
    )
    return ConfiguredTextParserAgent(
        registry=registry,
        openai_config=config.openai,
        offer_schema=build_configured_offer_schema(config.offer_schema),
    )


def test_parser_accepts_valid_json_input_without_agent_call() -> None:
    parser = _build_agent(enabled=False)

    payload = parser.parse(
        '{"company_name":"Acme","role_title":"Software Engineer II","compensation":{"annual_base_salary_usd":145000,"annualized_total_cash_usd":157000}}'
    )

    assert payload["company_name"] == "Acme"
    assert payload["role_title"] == "Software Engineer II"
    assert payload["compensation"]["annual_base_salary_usd"] == 145000
    assert payload["compensation"]["annualized_total_cash_usd"] == 157000


def test_parser_rejects_non_json_input_when_agent_disabled() -> None:
    parser = _build_agent(enabled=False)

    with pytest.raises(TextParserError):
        parser.parse("Company: Acme, Role: Software Engineer II")
