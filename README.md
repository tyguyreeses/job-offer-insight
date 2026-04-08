# Job Offer Insight

Stage-based implementation of a job-offer review app.

## Current Stage

- Active branch: `stage_2`
- Stage 2 focus: backend framework skeleton, DI wiring boundaries, and logging/health surfaces

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
