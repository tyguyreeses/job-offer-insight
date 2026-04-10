"""Shared protocol interface for GenAI agents."""

from __future__ import annotations

from typing import Any, Protocol


class Agent(Protocol):
    """Base protocol for repository-defined agent implementations."""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse intake text and return a schema-aligned payload object."""


class ChatAgent(Protocol):
    """Base protocol for chat-style assistant agents."""

    def reply(self, *, transcript: list[dict[str, str]], state: dict[str, Any]) -> str:
        """Generate one assistant reply for the current turn."""


class AudioTranscriber(Protocol):
    """Protocol for audio -> transcript adapters used by intake flows."""

    def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        """Transcribe uploaded audio and return transcript text."""
