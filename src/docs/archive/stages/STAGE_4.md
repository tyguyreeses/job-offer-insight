# STAGE 4 - Offer Intake (Text) + Missing-Info Flow + Validation

## Metadata
- Stage ID: `4`
- Status: `Completed`
- Completed: `true`
- Started On: `2026-04-08`
- Completed On: `2026-04-08`
- Branch: `stage_4`
- Depends On: `Stage 3`
- Primary Docs: `src/docs/application_interface.md`, `end-goal.md`

## Goal
Implement core text-based offer intake and enforce required-vs-soft validation behavior.

## Scope
- Text intake path
- Structured extraction orchestration
- Missing-field explicit ask/confirm flow
- Required-field blocking validation
- Soft warning behavior for non-required fields
- Annualization formula behavior for hourly offers

## Out of Scope
- Audio ingestion/transcription
- Dashboard and compare UI rendering

## Entry Criteria
- Stage 3 completed and approved
- Storage layer can persist offer payloads

## Implementation Checklist
- [x] Implement text intake endpoint/handler
- [x] Implement extraction-to-schema mapping flow
- [x] Implement missing-field decision prompts
- [x] Implement required field enforcement and soft warnings
- [x] Implement hourly annualization formula
- [x] Persist accepted offer data with omission semantics

## Deliverables
- End-to-end text offer intake behavior per contract
- Observable missing-field prompt/decision behavior

## Test Gate
- [x] Required field failure cases block save
- [x] Non-required missing fields produce warnings only
- [x] Confirmed omitted fields store as blanks
- [x] Hourly annualization formula test coverage

## Exit Criteria
- Text intake path is contract-complete and reviewable
- Validation behavior exactly matches interface contract
- User approves stage outputs before Stage 5

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage

