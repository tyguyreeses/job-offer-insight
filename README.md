# Job Offer Insight

Stage-based implementation of a job-offer review app.

## Current Stage

- Active branch: `stage_6`
- Stage 6 focus:
  - Dashboard page with horizontal side-scroll offer cards
  - Card section ordering and optional-field omission rendering (no `null`/`N/A` placeholders)
  - Max-two selection with oldest-selection auto-deselect on third selection
  - Backend/frontend sorting integration via `Sort by` controls
  - Automatic Add Entry -> Dashboard transition after successful save (`Finish` or chat-agent tool-driven submit)

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
