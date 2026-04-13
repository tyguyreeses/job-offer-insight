"""Config-driven agent registry for backend AI workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..utils.config_types import AgentsSection, AgentToolConfig


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    type: Literal["structured-output", "non-structured"]
    enabled: bool
    model: str
    prompt: str
    max_output_tokens: int
    tools: list["AgentToolDefinition"]
    reasoning: dict[str, object] | None = None


@dataclass(frozen=True)
class AgentToolDefinition:
    name: str
    description: str
    enabled: bool


@dataclass(frozen=True)
class AgentRegistry:
    agents: dict[str, AgentDefinition]

    def get(self, name: str) -> AgentDefinition:
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' is not configured.")
        return self.agents[name]


def build_agent_registry(config: AgentsSection) -> AgentRegistry:
    entry_creation_prompt = _resolve_prompt(config.entry_creation.prompt)
    parse_entry_prompt = _resolve_prompt(config.parse_entry.prompt)
    comparison_one_to_one_prompt = _resolve_prompt(config.comparison_one_to_one.prompt)
    comparison_one_to_all_prompt = _resolve_prompt(config.comparison_one_to_all.prompt)
    return AgentRegistry(
        agents={
            "entry_creation": AgentDefinition(
                name="entry_creation",
                type=config.entry_creation.type,
                enabled=config.entry_creation.enabled,
                model=config.entry_creation.model,
                prompt=entry_creation_prompt,
                max_output_tokens=config.entry_creation.max_output_tokens,
                tools=_resolve_tools(config.entry_creation.tools),
                reasoning=_resolve_reasoning(config.entry_creation.reasoning),
            ),
            "parse_entry": AgentDefinition(
                name="parse_entry",
                type=config.parse_entry.type,
                enabled=config.parse_entry.enabled,
                model=config.parse_entry.model,
                prompt=parse_entry_prompt,
                max_output_tokens=config.parse_entry.max_output_tokens,
                tools=_resolve_tools(config.parse_entry.tools),
                reasoning=_resolve_reasoning(config.parse_entry.reasoning),
            ),
            "comparison_one_to_one": AgentDefinition(
                name="comparison_one_to_one",
                type=config.comparison_one_to_one.type,
                enabled=config.comparison_one_to_one.enabled,
                model=config.comparison_one_to_one.model,
                prompt=comparison_one_to_one_prompt,
                max_output_tokens=config.comparison_one_to_one.max_output_tokens,
                tools=_resolve_tools(config.comparison_one_to_one.tools),
                reasoning=_resolve_reasoning(config.comparison_one_to_one.reasoning),
            ),
            "comparison_one_to_all": AgentDefinition(
                name="comparison_one_to_all",
                type=config.comparison_one_to_all.type,
                enabled=config.comparison_one_to_all.enabled,
                model=config.comparison_one_to_all.model,
                prompt=comparison_one_to_all_prompt,
                max_output_tokens=config.comparison_one_to_all.max_output_tokens,
                tools=_resolve_tools(config.comparison_one_to_all.tools),
                reasoning=_resolve_reasoning(config.comparison_one_to_all.reasoning),
            ),
        }
    )


def _resolve_prompt(value: str) -> str:
    stripped = value.strip()
    if stripped == "":
        raise ValueError("Agent prompt must be non-empty.")

    if "\n" in stripped or "\r" in stripped:
        return stripped

    candidate_paths = (
        Path(stripped),
        Path(__file__).resolve().parents[1] / "prompts" / stripped,
    )
    for path in candidate_paths:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8").strip()

    return stripped


def _resolve_tools(config_tools: list[AgentToolConfig]) -> list[AgentToolDefinition]:
    return [
        AgentToolDefinition(
            name=tool.name,
            description=tool.description,
            enabled=tool.enabled,
        )
        for tool in config_tools
    ]


def _resolve_reasoning(reasoning: object) -> dict[str, object] | None:
    if reasoning is None:
        return None
    dumped = getattr(reasoning, "model_dump", None)
    if callable(dumped):
        value = dumped(exclude_none=True)
        return value if isinstance(value, dict) and len(value) > 0 else None
    return None
