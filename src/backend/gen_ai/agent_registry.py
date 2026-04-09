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
    prompt = _resolve_prompt(config.text_parser.prompt)
    return AgentRegistry(
        agents={
            "text_parser": AgentDefinition(
                name="text_parser",
                type=config.text_parser.type,
                enabled=config.text_parser.enabled,
                model=config.text_parser.model,
                prompt=prompt,
                max_output_tokens=config.text_parser.max_output_tokens,
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
