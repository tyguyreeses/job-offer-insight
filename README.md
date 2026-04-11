# Job Offer Insight

Stage-based implementation of a job-offer review app.

## Current Stage

- Active branch: `stage_7`
- Stage 7 focus:
  - Compare page supports one-to-one and one-to-all draft layouts
  - Compare canvas preserves layout height and keeps controls in a stable position
  - Saved comparisons are listable/selectable from the compare page
  - Saved comparison selection can be toggled off to return to the draft builder
  - One-to-all saves are de-duplicated by base offer (latest save overrides prior one-to-all for that base)
  - Save comparison flow includes animated button states and success feedback

## Backend Config Foundation (Stage 1)

- Runtime config source: `src/config.yaml`
- Typed config models: `src/backend/utils/config_types.py`
- Config loader/validation: `src/backend/utils/config_loader.py`

## Validation Notes

- Config startup validation fails on missing required top-level sections.
- Unknown config keys are rejected.
- Stage 1 aligned docs: `src/docs/application_interface.md` and `src/docs/stages/STAGE_1.md`.

## Backend Skeleton (Stage 2)

- App entrypoint: `src/backend/main.py`
- Bootstrap-only mode: `python -m src.backend.main`
- Serve mode: `python -m src.backend.main --serve`
- API health endpoint: `GET /api/v1/health`
- API readiness endpoint: `GET /api/v1/readiness`

## Persistence Layer (Stage 3)

- SQLite bootstrap and migration runner: `src/backend/storage/db.py`
- Initial schema artifacts:
  - `src/backend/storage/schema.sql`
  - `src/backend/storage/migrations/0001_init.sql`
- Repository implementations:
  - `src/backend/storage/repositories/offer_repository.py`
  - `src/backend/storage/repositories/comparison_repository.py`

## Offer Intake (Stage 4)

- Offer endpoints:
  - `POST /api/v1/offers/intake/text`
    - Stage 5.1 request: `session_id`, `action`, `message_text`
    - Stage 5.1 response: conversational step/status fields plus optional saved offer
  - `POST /api/v1/offers/intake/audio`
  - `GET /api/v1/offers`
  - `GET /api/v1/offers/{offer_id}`
  - `PUT /api/v1/offers/{offer_id}`
- Offer service:
  - `src/backend/domain/services/offer_service.py`
- Offer intake tests:
  - `tests/backend/test_offer_intake_stage4.py`
  - `tests/backend/test_offer_intake_stage5_audio.py`

## Frontend (Stage 6)

- Frontend root: `src/frontend`
- Start dev server:
  - `cd src/frontend && npm install`
  - `npm run dev`
- Frontend tests:
  - `cd src/frontend && npm test`
