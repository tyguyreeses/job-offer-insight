# Implementation Plan (Suggested Order of Operations)

Branch: `project-skeleton`

This plan follows the `myteam` feature-pipeline/testing guidance while staying within current scope:
- define and lock the external interface first
- establish framework foundations before feature behavior
- update tests based on black-box contract
- then implement behavior in small, verifiable slices

## Phase 0 - Process Setup

1. Confirm branch is not `main` (done: `project-skeleton`).
2. Treat `src/docs/application_interface.md` as contract source for feature behavior and tests.
3. Keep commits phase-based so framework prep, tests, and implementation are separated.

## Phase 1 - Contract and Planning Docs (No runtime behavior)

1. Finalize `src/docs/application_interface.md` from `end-goal.md`.
2. Finalize this `PLAN.md` as execution order and acceptance checklist.
3. Optionally mirror this plan into `src/docs/plans/project-skeleton.md` to align with feature-pipeline convention.

Deliverable:
- documented, decision-complete contract and implementation order.

## Phase 2 - Framework Refactor / Foundations (Feature-neutral prep)

Start with configuration system as requested.

### 2.1 Config and App Bootstrap

1. Expand `src/config.yaml` into complete runtime config sections:
   - app/server
   - logging
   - database/sqlite
   - openai
   - ai workflow toggles
2. Define typed config models in `src/backend/utils/config_types.py`.
3. Implement config parsing/validation in `src/backend/utils/config_loader.py`.
4. Wire `src/backend/main.py` to:
   - load config
   - configure logger level (`--debug` -> debug, else info)
   - construct app-level dependencies

### 2.2 Backend Structure and Dependency Injection

1. Create API router composition (`api/router.py`, versioned routes).
2. Create domain service interfaces and DI wiring points.
3. Create storage interfaces and repository boundaries.
4. Keep business behavior minimal; focus on skeleton contracts and wiring.

### 2.3 Persistence Foundation

1. Set up SQLite connection/session management.
2. Add initial schema/migration scaffolding for offers and comparisons.
3. Add repository method signatures for offer CRUD and comparison CRUD.

### 2.4 Frontend Foundation

1. Initialize Vite React structure and routing.
2. Add baseline layout and navbar shell.
3. Add shared type definitions and API client wrappers.
4. Add styling token files (including animation token/keyframe location).

Deliverable:
- runnable app skeleton with config, DI, routing, storage foundations, and page shells.

## Phase 3 - Test Suite Design and Build (Before full behavior)

Use `myteam/testing` principles:
- test external behavior from `src/docs/application_interface.md`
- avoid internal-implementation-coupled assertions
- run with `poetry run pytest -q` (or `python -m pytest -q` in active env)

### 3.1 Backend Black-box Tests

1. Offer create validation tests:
   - required fields enforced
   - soft warning behavior represented in responses
2. Missing-field flow tests:
   - explicit ask/confirm decision path
   - omit-as-blank persistence behavior
3. Annualization tests:
   - hourly -> annual formula correctness
4. Offer update tests:
   - edit existing via structured payload
5. Comparison tests:
   - one-to-one accepts two selected IDs
   - one-to-all accepts one base ID
   - saved comparison persists IDs + placeholder summary + optional note
6. Health/logging surface tests (observable outcomes only).

### 3.2 Frontend Behavior Tests

1. Dashboard selection cap behavior:
   - max two selections
   - selecting third deselects oldest
2. Compare layout behavior:
   - one-to-one left/right cards + placeholder middle
   - one-to-all left card + placeholder middle/right
3. Edit flow behavior:
   - opens pre-filled form
   - does not route through initial AI intake page
4. Saved comparison note rendering below page content.

### 3.3 End-to-End Coverage

1. Text intake to saved offer happy path.
2. Missing field confirm-as-omitted path.
3. Dashboard select -> compare placeholder rendering.
4. Save comparison with optional note -> view in compare list/details.

Deliverable:
- tests that prove interface contract behavior before/alongside implementation.

## Phase 4 - Feature Implementation (Behavior slices)

Implement in vertical slices, each with tests passing before moving on.

### Slice A - Offer Intake Core

1. Text intake endpoint + extraction orchestration.
2. Missing-field question/confirmation flow.
3. Required-field blocking + soft warnings.
4. Offer persistence.

### Slice B - Audio Intake Path

1. Audio ingestion/transcription integration pattern based on `reference-audio-material` guidance.
2. Feed transcript into same extraction/missing-field pipeline as text.

### Slice C - Dashboard and Selection Behavior

1. Offer card listing/sorting.
2. Non-monetary AI bullet summary display (stored summary).
3. Two-selection cap with oldest deselection behavior.

### Slice D - Compare Placeholder Modes

1. One-to-one layout rendering contract.
2. One-to-all layout rendering contract.
3. Placeholder-only middle/right sections per mode.

### Slice E - Saved Comparisons

1. Persist selected IDs + placeholder summary + optional note.
2. Retrieve/list saved comparisons.
3. Render optional note below page content.

### Slice F - Edit Existing Offer

1. Pre-filled structured form.
2. Update endpoint integration.
3. Preserve existing omit-as-blank semantics.

Deliverable:
- all behavior in `application_interface.md` implemented except explicitly out-of-scope ranking logic.

## Phase 5 - Hardening and Release Readiness

1. Validate config defaults and failure messages for misconfiguration.
2. Verify logging and startup behavior in debug/info modes.
3. Run full test suite from repo root.
4. Update docs (`README.md`) with run/test instructions.
5. Final review against interface contract checklist.

Deliverable:
- branch ready for merge with passing tests and aligned docs.

## Suggested Commit Cadence

1. Docs contract + plan
2. Config/bootstrap foundation
3. Backend framework structure
4. Storage foundation
5. Frontend foundation
6. Test suite additions
7. Feature slices A-F (one commit per slice)
8. Hardening/docs cleanup

## Team Roles and Skills Usage Notes

Based on current `myteam` configuration:

1. Load/use `feature-pipeline` whenever changing behavior, tests, or behavior-facing docs.
2. Load/use `feature-pipeline/framework-oriented-design` before framework refactor or implementation changes.
3. Load/use `testing` when adding/modifying tests.
4. If `spawn-agent` becomes part of workflow:
   - available role currently listed is `Meta Agent` (agent-building support)
   - optional support roles under feature-pipeline are:
     - `feature-pipeline/code-linter` for readiness confirmation
     - `feature-pipeline/project-myteam-update` for `.myteam` migrations

## Acceptance Checklist

1. Interface doc and implementation behavior are aligned.
2. Config system drives startup and dependency setup.
3. Required vs soft-validation behavior matches contract.
4. Offer edit flow bypasses initial AI intake.
5. Compare page placeholder behavior matches selected mode.
6. Saved comparison includes IDs, placeholder summary, optional note display.
7. Test suite demonstrates black-box contract coverage.
8. Comparison ranking logic remains intentionally unimplemented.
