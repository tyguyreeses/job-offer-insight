# Backend `src`

Core app code.

## Key Files

- `main.py`: app factory, dependency providers, and route handlers
- `models.py`: validation + schema contracts
- `services.py`: computed metric formulas
- `database.py`: engine construction and session dependency factories

## Key Contract

- `/dev/seed` records are config-driven via `configs/config.yaml` (from repo root: `backend/configs/config.yaml`).
