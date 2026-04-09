"""Audio transcription adapter for Stage 5 intake flow."""

from __future__ import annotations

import io
from dataclasses import dataclass

from .client import OpenAIClientConfigError, build_openai_client
from ..utils.config_types import OpenAISection

_ACCEPTED_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".webm",
}


class AudioTranscriptionError(RuntimeError):
    """Raised when audio cannot be transcribed for intake."""


@dataclass(frozen=True)
class ConfiguredAudioTranscriber:
    openai_config: OpenAISection

    def transcribe(self, *, audio_bytes: bytes, filename: str, content_type: str | None = None) -> str:
        if not audio_bytes:
            raise AudioTranscriptionError("Audio file is empty.")

        lowered_name = filename.strip().lower()
        if lowered_name == "" or not any(
            lowered_name.endswith(extension) for extension in _ACCEPTED_AUDIO_EXTENSIONS
        ):
            accepted = ", ".join(sorted(_ACCEPTED_AUDIO_EXTENSIONS))
            raise AudioTranscriptionError(
                f"Unsupported audio format. Accepted extensions: {accepted}"
            )

        file_handle = io.BytesIO(audio_bytes)
        file_handle.name = lowered_name

        try:
            client = build_openai_client(self.openai_config)
            response = client.audio.transcriptions.create(
                file=file_handle,
                model=self.openai_config.transcription_model,
            )
        except OpenAIClientConfigError as exc:
            raise AudioTranscriptionError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - provider/runtime surface
            raise AudioTranscriptionError(f"Transcription request failed: {exc}") from exc

        if isinstance(response, str):
            transcript = response.strip()
        else:
            transcript = str(getattr(response, "text", "")).strip()

        if transcript == "":
            raise AudioTranscriptionError("No transcript text was returned for this audio input.")

        return transcript
