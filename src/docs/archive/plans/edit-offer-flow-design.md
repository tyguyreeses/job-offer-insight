# Edit Offer Flow Design (Draft)

## Goal

Define how `Edit` on selected dashboard cards should work without sending users back into open-ended conversational intake.

## Constraints from Existing Contract

1. Editing must use a structured form pre-filled with existing values.
2. Editing must not route through the initial AI intake page.
3. Existing backend `PUT /api/v1/offers/{offer_id}` already supports full-payload updates with required-field validation.

## Proposed UX

1. User selects a card on Dashboard.
2. `Edit` action appears on the selected card.
3. Clicking `Edit` opens a dedicated edit view (`/edit/:offerId` route or in-app panel) with:
   - pre-populated required fields
   - pre-populated optional fields
   - clear required vs optional visual grouping
4. User can:
   - `Save` (submit full payload to `PUT /api/v1/offers/{offer_id}`)
   - `Cancel` (return to dashboard with no changes)
5. On successful save:
   - show success feedback
   - return to dashboard
   - refreshed card reflects updated values

## Data/Validation Behavior

1. Frontend fetches current payload via `GET /api/v1/offers/{offer_id}` before rendering edit form.
2. Save sends full normalized payload to `PUT /api/v1/offers/{offer_id}`.
3. If required fields are missing/invalid, backend returns blocked response and frontend displays inline errors.
4. Optional blank fields remain allowed and should continue to be omitted in dashboard rendering.

## Implementation Phases

1. Add route + page shell for edit form.
2. Define typed form model mirroring offer payload shape.
3. Build grouped form sections:
   - Core role/company/location + base comp
   - Monetary benefits
   - Non-monetary benefits
4. Add save/cancel action bar and request handling.
5. Add frontend tests:
   - prefill behavior
   - save success
   - required-field error handling
   - cancel behavior

## Open Questions for Finalization

1. Route style:
   - full page (`/edit/:offerId`) vs modal/panel overlay
2. Form density:
   - compact one-page form vs section-by-section progressive form
3. Post-save navigation:
   - always return to dashboard vs stay on form with success message
