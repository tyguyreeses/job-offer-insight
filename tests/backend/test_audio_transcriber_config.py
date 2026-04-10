from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

import src.backend.gen_ai.audio_transcriber as audio_transcriber_module
from src.backend.gen_ai.audio_transcriber import AudioTranscriptionError, ConfiguredAudioTranscriber
from src.backend.utils.config_types import OpenAISection


@dataclass
class FakeTranscriptionResponse:
    text: str


class FakeTranscriptions:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, *, file: Any, model: str) -> FakeTranscriptionResponse:
        self.calls.append({"file_name": getattr(file, "name", ""), "model": model})
        return FakeTranscriptionResponse(text="Structured transcript")


class FakeAudio:
    def __init__(self) -> None:
        self.transcriptions = FakeTranscriptions()


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.audio = FakeAudio()


def test_transcriber_uses_configured_extension_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = FakeOpenAIClient()
    monkeypatch.setattr(audio_transcriber_module, "build_openai_client", lambda _config: fake_client)

    config = OpenAISection(
        model="gpt-5.2",
        transcription_model="gpt-4o-mini-transcribe",
        accepted_audio_extensions=[".ogg"],
    )
    transcriber = ConfiguredAudioTranscriber(openai_config=config)

    transcript = transcriber.transcribe(audio_bytes=b"fake-bytes", filename="offer.ogg")

    assert transcript == "Structured transcript"
    assert fake_client.audio.transcriptions.calls == [
        {"file_name": "offer.ogg", "model": "gpt-4o-mini-transcribe"}
    ]


def test_transcriber_rejects_extensions_not_in_configured_allowlist() -> None:
    config = OpenAISection(
        model="gpt-5.2",
        transcription_model="gpt-4o-mini-transcribe",
        accepted_audio_extensions=[".wav"],
    )
    transcriber = ConfiguredAudioTranscriber(openai_config=config)

    with pytest.raises(AudioTranscriptionError) as exc:
        transcriber.transcribe(audio_bytes=b"fake-bytes", filename="offer.webm")

    assert "Unsupported audio format" in str(exc.value)
