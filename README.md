# Job Offer Insight

Job-offer review app with AI-assisted intake, offer management, and comparison flows.

## Docs

- Product contract: `src/docs/application_interface.md`
- End-goal reference: `end-goal.md`
- Legacy planning notes: `src/docs/archive`

## Backend

- Entrypoint: `src/backend/main.py`
- Config source: `src/config.yaml`
- Typed config models: `src/backend/utils/config_types.py`
- Config loader/validation: `src/backend/utils/config_loader.py`
- Health endpoints:
  - `GET /api/v1/health`
  - `GET /api/v1/readiness`

## Persistence

- SQLite bootstrap and migration runner: `src/backend/storage/db.py`
- Schema artifacts:
  - `src/backend/storage/schema.sql`
  - `src/backend/storage/migrations/0001_init.sql`
- Repositories:
  - `src/backend/storage/repositories/offer_repository.py`
  - `src/backend/storage/repositories/comparison_repository.py`

## Offer Intake

- Endpoints:
  - `POST /api/v1/offers/intake/text`
  - `POST /api/v1/offers/intake/audio`
  - `GET /api/v1/offers`
  - `GET /api/v1/offers/{offer_id}`
  - `PUT /api/v1/offers/{offer_id}`
- Offer service: `src/backend/domain/services/offer_service.py`
- Intake tests: `tests/backend`

## Frontend

- Frontend root: `src/frontend`
- Dev server:
  - `cd src/frontend && npm install`
  - `npm run dev`
- Frontend tests:
  - `cd src/frontend && npm test`
