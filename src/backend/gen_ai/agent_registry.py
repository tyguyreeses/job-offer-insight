"""Config-driven agent registry for backend AI workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..utils.config_types import AgentsSection


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    type: Literal["structured-output", "non-structured"]
    enabled: bool
    model: str
    prompt: str
    max_output_tokens: int


@dataclass(frozen=True)
class AgentRegistry:
    agents: dict[str, AgentDefinition]

    def get(self, name: str) -> AgentDefinition:
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' is not configured.")
        return self.agents[name]


def build_agent_registry(config: AgentsSection) -> AgentRegistry:
    entry_creation_prompt = _resolve_prompt(config.entry_creation.prompt)
    structured_output_prompt = _resolve_prompt(config.structured_output.prompt)
    return AgentRegistry(
        agents={
            "entry_creation": AgentDefinition(
                name="entry_creation",
                type=config.entry_creation.type,
                enabled=config.entry_creation.enabled,
                model=config.entry_creation.model,
                prompt=entry_creation_prompt,
                max_output_tokens=config.entry_creation.max_output_tokens,
            ),
            "structured_output": AgentDefinition(
                name="structured_output",
                type=config.structured_output.type,
                enabled=config.structured_output.enabled,
                model=config.structured_output.model,
                prompt=structured_output_prompt,
                max_output_tokens=config.structured_output.max_output_tokens,
            )
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
