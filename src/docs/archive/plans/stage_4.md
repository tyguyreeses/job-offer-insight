# Stage 4 Plan (`stage_4`)

## Framework refactor (feature-neutral prep work)

1. Replace the placeholder offer service with a concrete Stage 4 offer service implementation.
2. Extend the offer service interface so API routes can consume stable intake/list/get/update behavior.
3. Add a versioned offers API router and wire it into top-level API composition.

## Feature addition (behavior implementation)

1. Implement text intake orchestration:
   - structured extraction via JSON input when available
   - fallback text parsing for key offer fields
2. Implement required field enforcement:
   - `company_name`
   - `role_title`
   - base pay path (`annual_base_salary_usd` OR hourly + hours/week)
3. Implement soft warning + missing-info flow for non-required fields with explicit omission confirmations.
4. Implement annualization behavior:
   - `hourly_rate_usd * hours_per_week * 52`
5. Persist accepted offer payloads (including blank omission semantics) and expose:
   - `POST /api/v1/offers/intake/text`
   - `GET /api/v1/offers`
   - `GET /api/v1/offers/{offer_id}`
   - `PUT /api/v1/offers/{offer_id}`
6. Add black-box API tests for Stage 4 gate behavior.
