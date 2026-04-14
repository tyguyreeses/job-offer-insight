# Plan: Fix Finish Button Direct Save

## 1. Framework refactor (feature-neutral prep work)

- Add a service method + API endpoint for finalizing an intake session without parsing or agent prompts.

## 2. Feature addition (behavior implementation)

- Wire frontend `Finish` to call the new finalize endpoint instead of conversational intake.
- Validate required fields client-side using `missing_required_fields` before finalize.
- Update tests to cover finalize flow and missing-required feedback.
