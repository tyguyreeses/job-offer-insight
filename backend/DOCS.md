# Backend

FastAPI service for offer CRUD + comparison metrics.

## Key Files

- `src/main.py`: routes and endpoint behavior
- `src/models.py`: request/response + DB models
- `src/services.py`: compensation math
- `src/database.py`: engine/session setup
- `tests/test_offers_api.py`: expected API behavior
- `alembic/versions/0001_create_offer_table.py`: schema baseline

## Change Areas

- Endpoint logic is defined in `src/main.py`.
- Payload and field constraints are defined in `src/models.py`.
- Metric formulas are implemented in `src/services.py` and exposed by `/offers/compare` in `src/main.py`.
- Schema history lives in `alembic/versions/` and corresponds to `src/models.py`.
