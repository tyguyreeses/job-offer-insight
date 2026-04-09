# Job Offer Insight

Stage-based implementation of a job-offer review app.

## Current Stage

- Active branch: `stage-4.1-gen-ai`
- Stage 4.1 focus: AI text extraction to schema, config-driven agents, omission confirmations, required-vs-soft validation, and annualization behavior

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
  - `GET /api/v1/offers`
  - `GET /api/v1/offers/{offer_id}`
  - `PUT /api/v1/offers/{offer_id}`
- Stage 4 offer service:
  - `src/backend/domain/services/offer_service.py`
- Stage 4 API tests:
  - `tests/backend/test_offer_intake_stage4.py`
