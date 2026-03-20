# Backend `src`

Core app code.

## Key Files

- `main.py`: route handlers and status codes
- `models.py`: validation + schema contracts
- `services.py`: computed metric formulas
- `database.py`: DB URL, engine, and session dependency

## Key Contract

- `/offers/compare` allows `sort_by` values: `total_comp_annual`, `total_comp_year1`, `total_comp_col_adjusted`
