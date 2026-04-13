# Stage 3 Plan (`stage_3`)

## Framework refactor (feature-neutral prep work)

1. Replace Stage 2 placeholder repositories with SQLite-backed repository implementations.
2. Add database bootstrap + migration execution support in `src/backend/storage/db.py`.
3. Add schema artifacts for initial persistence setup:
   - `src/backend/storage/schema.sql`
   - `src/backend/storage/migrations/0001_init.sql`
4. Introduce domain persistence models for offers/comparisons to keep storage boundaries explicit.

## Feature addition (behavior implementation)

1. Implement offer persistence CRUD repository methods.
2. Implement comparison persistence CRUD repository methods.
3. Preserve omitted-field blank semantics (`null`, `""`, `[]`) by storing and retrieving payload JSON without coercion.
4. Add repository-level tests for:
   - offer create/read/update
   - comparison save/list/detail
   - blank-value semantics persistence
