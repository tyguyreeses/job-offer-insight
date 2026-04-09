"""Config-driven agent registry for backend AI workflows."""

from __future__ import annotations

from dataclasses import dataclass

from ..utils.config_types import AgentsSection


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    enabled: bool
    model: str
    system_prompt: str
    temperature: float
    max_output_tokens: int


@dataclass(frozen=True)
class AgentRegistry:
    agents: dict[str, AgentDefinition]

    def get(self, name: str) -> AgentDefinition:
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' is not configured.")
        return self.agents[name]


def build_agent_registry(config: AgentsSection) -> AgentRegistry:
    return AgentRegistry(
        agents={
            "text_parser": AgentDefinition(
                name="text_parser",
                enabled=config.text_parser.enabled,
                model=config.text_parser.model,
                system_prompt=config.text_parser.system_prompt,
                temperature=config.text_parser.temperature,
                max_output_tokens=config.text_parser.max_output_tokens,
            )
        }
    )
