# Stage 5 Plan - Audio Intake Integration

Branch: `stage-5`

## Framework Refactor (Feature-Neutral)

1. Introduce a shared OpenAI client factory in `src/backend/gen_ai/client.py` so text and audio runtime adapters use the same credential/timeout construction.
2. Extend DI container wiring to provide an audio transcription adapter alongside the existing text parser agent.
3. Keep existing Stage 4 text intake behavior unchanged.

## Feature Addition (Behavior)

1. Add `POST /api/v1/offers/intake/audio` multipart endpoint in offers API.
2. Accept audio upload plus optional omission confirmations and extraction overrides.
3. Transcribe audio input using configured transcription model.
4. Route transcript through the existing text extraction/validation/missing-field/persistence path.
5. Persist `offer_meta.source_input_type = "audio"` for audio-origin offers.
6. Return observable `transcription_failed` status when transcription cannot produce transcript text.

## Reference Patterns Reused

1. From `reference-audio-material/speech_to_text.py` and `reference-audio-material/speech.py`: file-based upload transcription pattern using `client.audio.transcriptions.create(file=..., model=...)`.
2. Adaptation decision: keep Stage 5 as API upload flow (not local microphone capture) to match backend service contract and avoid CLI-device dependencies.

## Test Plan

1. Audio happy path: transcribe -> parse -> required validation -> missing optional prompts -> save.
2. Transcription failure: endpoint returns `transcription_failed` with observable error.
3. Contract parity: audio path enforces required field blocking identical to text path.
