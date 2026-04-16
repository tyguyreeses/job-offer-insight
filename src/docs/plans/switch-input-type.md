# Plan: Switch Intake Input Type

## Framework refactor

- None. The existing Add Entry page state and helpers are sufficient for mode switching.

## Feature addition

- Update `src/frontend/src/pages/AddEntryPage.tsx` to replace `Skip` with mode-switch controls.
- Add a reusable helper for entering audio mode from both the chooser and text mode while preserving session/transcript state.
- Ensure switching modes does not clear `sessionId` or `conversation` and does not trigger new API calls.
- Disable mode switching while audio is recording or a request is in flight.
- Update `src/frontend/src/pages/AddEntryPage.test.tsx` to cover:
  - Text mode shows `Switch to Audio Input` instead of `Skip`.
  - Audio mode shows `Switch to Text Input` instead of `Skip`.
  - Switching modes preserves existing session/transcript context.
