# Stage 6 Plan - Dashboard + Selection Rules

## Framework Refactor (Feature-Neutral Prep Work)

1. Add sorted listing parameters to backend offer list interfaces (`sort_by`, `sort_direction`) so dashboard sorting is a first-class API behavior.
2. Align frontend app shell composition so navbar-level navigation owns page switching while feature pages focus on page behavior.

## Feature Addition (Behavior Implementation)

1. Add dashboard page with horizontal card scroll and required section ordering:
   - Salary
   - Monetary benefits
   - Non-monetary benefits summary bullets
   - Date created (`mm-dd-yyyy`)
2. Add dashboard `Sort by` dropdown and wire selection to backend sorting query params.
3. Hide blank optional fields on dashboard cards (render nothing for omitted values).
4. Implement max-two selection with oldest-selection auto-deselect when a third card is selected.
5. Route to dashboard after successful intake save from:
   - `Finish` action
   - chat-agent-driven `submit_entry` save flow (observable as `status="saved"` on submit turn)
6. Add backend and frontend tests for Stage 6 test-gate behavior.
