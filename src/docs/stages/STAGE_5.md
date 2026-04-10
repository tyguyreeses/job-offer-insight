# STAGE 5 - Audio Intake Integration

## Metadata
- Stage ID: `5`
- Status: `Completed`
- Completed: `true`
- Started On: `2026-04-09`
- Completed On: `2026-04-09`
- Branch: `stage-5`
- Depends On: `Stage 4`
- Primary Docs: `end-goal.md`, `src/docs/application_interface.md`

## Goal
Add audio ingestion/transcription and route transcript output through the same text intake pipeline.

## Scope
- Audio input endpoint or upload path
- Transcription integration pattern
- Reuse of Stage 4 extraction/validation/missing-field flow
- Reference-guided audio structure decisions using `reference-audio-material/` resources

## Out of Scope
- Dashboard card interaction behavior
- Comparison page behavior

## Entry Criteria
- Stage 4 completed and approved
- Core text intake flow is stable

## Implementation Checklist
- [x] Review `reference-audio-material/README.md` and relevant sample scripts before finalizing audio architecture
- [x] Document which reference patterns are being reused/adapted and why
- [x] Define accepted audio input format(s)
- [x] Implement transcription handoff
- [x] Route transcript through existing text intake pipeline
- [x] Surface errors for transcription failures in observable response form
- [x] Confirm omitted/required validation behavior remains consistent with text path

## Deliverables
- Working audio-to-offer intake path
- Consistent behavior parity with text intake flow

## Test Gate
- [x] Audio happy path test (transcribe -> extract -> validate -> save)
- [x] Transcription failure handling test
- [x] Behavior parity checks against text intake contract

## Exit Criteria
- Audio intake is integrated without duplicating core logic
- Text and audio paths produce consistent contract behavior
- User approves stage outputs before Stage 6

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage
- Reused the file-based transcription pattern from `reference-audio-material/speech_to_text.py`/`speech.py`:
  `client.audio.transcriptions.create(file=..., model=...)`.
- Adapted Stage 5 to server-side file upload (`POST /api/v1/offers/intake/audio`) instead of device-bound microphone capture.
- Accepted audio extensions: `.wav`, `.mp3`, `.m4a`, `.mp4`, `.mpeg`, `.mpga`, `.webm`.
- Audio transcript output is routed through the existing text parser + validation + omission-confirmation + persistence flow.
- Audio transcription failures are returned as observable intake status `transcription_failed`.
