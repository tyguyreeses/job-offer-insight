"""Audio transcription adapter for Stage 5 intake flow."""

from __future__ import annotations

import io
from dataclasses import dataclass
from time import perf_counter

from .client import OpenAIClientConfigError, build_openai_client
from ..utils.config_types import OpenAISection
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AudioTranscriptionError(RuntimeError):
    """Raised when audio cannot be transcribed for intake."""


@dataclass(frozen=True)
class ConfiguredAudioTranscriber:
    openai_config: OpenAISection

    def transcribe(self, *, audio_bytes: bytes, filename: str, content_type: str | None = None) -> str:
        logger.debug(
            "Starting transcription for filename=%s content_type=%s bytes=%d",
            filename,
            content_type or "unknown",
            len(audio_bytes),
        )
        if not audio_bytes:
            raise AudioTranscriptionError("Audio file is empty.")

        accepted_extensions = {
            extension.strip().lower()
            for extension in self.openai_config.accepted_audio_extensions
            if extension.strip() != ""
        }
        if not accepted_extensions:
            raise AudioTranscriptionError("No accepted audio extensions are configured.")

        lowered_name = filename.strip().lower()
        if lowered_name == "" or not any(
            lowered_name.endswith(extension) for extension in accepted_extensions
        ):
            accepted = ", ".join(sorted(accepted_extensions))
            raise AudioTranscriptionError(
                f"Unsupported audio format. Accepted extensions: {accepted}"
            )

        file_handle = io.BytesIO(audio_bytes)
        file_handle.name = lowered_name

        start = perf_counter()
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

        elapsed_ms = (perf_counter() - start) * 1000
        logger.debug("Transcription request completed in %.1fms", elapsed_ms)

        if isinstance(response, str):
            transcript = response.strip()
        else:
            transcript = str(getattr(response, "text", "")).strip()

        if transcript == "":
            raise AudioTranscriptionError("No transcript text was returned for this audio input.")

        logger.debug("Transcription complete: %s", transcript)
        return transcript
