# Job Offer Insight

FastAPI + React app for comparing job offers with sortable compensation metrics and a Recharts dashboard.

## Stack

- Backend: FastAPI, SQLModel, Alembic, SQLite
- Frontend: Vite, React, TypeScript, TanStack Query, Recharts

## Project Layout

- `backend/` API, data model, migrations, tests
- `frontend/` dashboard UI

## Local Setup

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload
```

Backend runs at `http://localhost:8000`.

Backend config defaults live in `configs/config.yaml` (repo-root path: `backend/configs/config.yaml`).
Optional overrides:
- `APP_CONFIG_PATH`: path to an alternate YAML config file.
- `DATABASE_URL`: overrides `database.url` from YAML.

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## API Endpoints

- `GET /health`
- `GET /offers`
- `POST /offers`
- `GET /offers/{offer_id}`
- `PATCH /offers/{offer_id}`
- `DELETE /offers/{offer_id}`
- `GET /offers/compare?sort_by=total_comp_annual&descending=true`
- `POST /dev/seed`

## Running Tests

```bash
cd backend
pytest -q
```

## Notes

- Single-user mode for MVP; auth intentionally deferred.
- Backend runtime behavior is config-driven for:
  - DB connection settings
  - CORS policy
  - `/dev/seed` demo records
- Compensation metrics in compare response:
  - `total_comp_annual = base_salary + annual_bonus + annual_equity`
  - `total_comp_year1 = total_comp_annual + sign_on_bonus`
  - `total_comp_col_adjusted = total_comp_annual / col_index`
