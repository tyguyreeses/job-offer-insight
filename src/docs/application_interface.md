# Application Interface Contract

This document defines the externally observable behavior for Job Offer Insight.
It is the black-box contract for API behavior, UI behavior, and persistence-visible outcomes.

## Product Scope

Job Offer Insight provides:

1. Offer intake (audio or text) with AI-assisted extraction into a standardized USD-only schema.
2. Offer dashboard browsing and selection for comparison.
3. Comparison page with explicit placeholder behavior while comparison logic is intentionally deferred.
4. Editing existing offers through a structured form.
5. Saving/retrieving comparison records including an optional user note.

Comparison ranking/scoring logic is intentionally out of scope for this version.

## Data Contract (Offer)

### Required Fields

An offer is valid for save only if all required constraints are met:

1. `company_name` (non-empty string)
2. `role_title` (non-empty string)
3. `location` (non-empty string)
4. Base pay path:
   - either `compensation.annual_base_salary_usd`
   - or both `compensation.hourly_rate_usd` and `compensation.hours_per_week`

### Currency and Compensation Rules

1. Currency is USD only.
2. If hourly compensation is provided, annualized base salary defaults to:
   `hourly_rate_usd * hours_per_week * 52`
3. Non-required compensation/benefit fields may be blank.
4. `compensation.annualized_total_cash_usd` is an optional field and may be provided directly.

### Missing Information Behavior

When a field is missing during intake:

1. System asks user explicitly whether the field should be provided or is not part of this offer.
2. If user confirms it is not part of the offer, system stores blank representation (`null`, empty string, or empty array based on field type).
3. Blank fields are treated as "not included in offer," not as an error state.

### Offer Metadata Semantics

1. `offer_meta.source_input_type` reflects intake origin.
2. Text intake saves `offer_meta.source_input_type = "text"`.
3. Audio intake (Stage 5) may reuse text parsing internally but must persist `offer_meta.source_input_type = "audio"` for audio-origin offers.

### Validation Behavior

1. Hard validation blocks save only for required fields.
2. All non-required fields trigger soft warnings only.

## Data Contract (Comparison)

A saved comparison record includes:

1. Selected offer IDs
2. Summary text (placeholder content for now)
3. Optional user note

If user note exists, it is displayed below all other comparison page content.

## UI Contract

### Styling and Motion Baseline

1. Frontend uses custom CSS styling for primary pages and controls.
2. Add Entry main screen is mostly empty with a large, centered primary heading.
3. Selectable interactive elements use a soft blue glow hover effect.
4. Loading/reveal motion uses smooth fades with staged sequencing (top-to-bottom and left-to-right).
5. Navbar styling should present an elegant, clean, minimal look across routes.
6. Dashboard offer cards must follow end-goal styling intent: clean/minimal presentation, consistent card sizing, clear section separation, and readable vertical content rhythm.

## Navbar Behavior

1. `Dashboard` is default when at least one offer entry exists.
2. `Add Entry` is default when no offer entries exist.
3. `Compare` page:
   - If navigated from dashboard compare action, selection context is pre-populated.
   - If opened directly, user can choose offers by company name.
   - If saved comparisons exist, they are listed.

## Add Entry Page

1. Displays large, centered primary prompt: `Create a Job Entry`.
2. Provides two input modes:
   - Audio input
   - Text input
3. Main entry controls appear as two large, centered round buttons.
4. On text-mode selection, mode buttons fade out and text input fades in.
5. On audio-mode selection:
   - Text button fades away.
   - Audio button smoothly slides to the centered position.
   - The same button becomes the recording control with label transitions (`Audio` -> `Record` -> `Stop`).
6. Audio recording behavior:
   - While recording, the full button pulses red.
   - Pressing `Stop` automatically sends the recorded audio to `POST /api/v1/offers/intake/audio` with `action=submit`.
   - During upload/transcription, the centered button is disabled and shows processing state.
   - If auto-submit fails, the button label switches to `Retry` and one tap retries the same captured clip.
7. Button label changes in audio mode animate as fade-out of prior label followed by fade-in of next label.
8. Assistant follow-up messages fade in above the input/conversation controls.
9. Under intake action controls, display a notice that users can edit information later.
10. AI extracts structured offer data.
11. System asks clarifying follow-up questions for missing fields.
12. User can confirm omitted fields as "not part of offer."
13. After a successful save (from `Finish` button or equivalent agent-tool submit), the UI automatically navigates to `Dashboard`.

## Edit Offer Flow

1. Existing offers are editable.
2. Editing uses a pre-filled structured form.
3. Editing does not route user through the initial open-ended AI intake flow.

## Dashboard Page

1. Shows offer cards in horizontal side-scroll layout.
2. Default ordering is date-based left-to-right (newest first unless changed by user).
3. Dashboard includes a visible `Sort by` dropdown to change ordering.
4. Cards can be sorted by changeable option selected from `Sort by`.
5. Card vertical display order:
   - Salary
   - Monetary benefits
   - Non-monetary benefits (AI bullet-point summary, generated once then stored)
   - Date created (`mm-dd-yyyy`)
6. Card styling and formatting should align to end-goal decisions:
   - clean/minimal visual style
   - side-by-side cards with horizontal scroll emphasis
   - clear section formatting for salary, monetary, non-monetary, and date blocks
   - soft blue glow on selectable/interactive elements
7. Optional-field display rule:
   - optional fields that are blank/omitted are not rendered on the card at all
   - do not display placeholder values such as `None`, `null`, `N/A`, or "missing"
8. Compare selection rules:
   - Maximum two selected cards
   - On selecting a third card, earliest selected card is automatically deselected
9. Selected-card quick actions:
   - When a card is selected/highlighted, show `Edit` and `Delete` actions on the card
   - `Delete` uses a two-step confirm interaction (`Delete` -> `Confirm`) before removal
   - On confirmed delete, remove the offer from persistence and the dashboard list

## Compare Page

### One-to-one mode

Triggered when two cards are selected.

1. Left section: first selected offer card
2. Middle section: empty placeholder summary area
3. Right section: second selected offer card

### One-to-all mode

Triggered when one card is selected and user requests one-to-all compare flow.

1. Left section: selected base offer card
2. Middle section: empty placeholder summary area
3. Right section: empty placeholder area

No ranking/scoring output is shown in this version.

## API Contract (External Behavior)

Endpoint paths may evolve, but external behavior must remain equivalent.

### Offer Intake and CRUD

1. Create offer from text/audio-derived payload.
2. Text intake endpoint accepts JSON body at `POST /api/v1/offers/intake/text`.
3. Audio intake endpoint accepts multipart conversational turns at `POST /api/v1/offers/intake/audio` with:
   - `action`: `submit | skip_current | finish`
   - optional `session_id` for continuing a prior turn
   - required `audio_file` for `action=submit` (`.wav`, `.mp3`, `.m4a`, `.mp4`, `.mpeg`, `.mpga`, `.webm`)
4. Audio and text intake return the same conversational response contract:
   - `session_id`, `status`, `assistant_message`, `step`, `can_finish`, `missing_required_fields`, `current_prompt_key`, `errors`, `warnings`, `messages`, `offer`
   - `messages` is a full chronological transcript list of `{ role, content }` entries (`user` and `assistant`)
5. `skip_current` and `finish` on audio follow the same state machine and gating behavior as text.
6. Audio transcription failures are returned as observable conversational status `transcription_failed`.
7. Save accepted blanks as omitted fields.
8. Retrieve offer list and single offer details.
   - `GET /api/v1/offers` supports sort controls:
     - `sort_by`: `created_at | company_name | role_title` (default `created_at`)
     - `sort_direction`: `asc | desc` (default `desc`)
9. Update offer by ID via structured form payload.
10. Delete offer by ID via `DELETE /api/v1/offers/{offer_id}`.
11. During conversational turns, the entry-creation agent may trigger the same save flow as `action=finish` by calling its configured `submit_entry` tool when the user indicates they are done.
12. Successful save completion (including chat-agent-triggered submit) returns/propagates enough outcome state for the frontend to route to Dashboard.

### Comparison

1. Accept up to two selected offer IDs for one-to-one.
2. Accept one selected base offer for one-to-all placeholder layout.
3. Persist saved comparison with IDs, placeholder summary, and optional note.
4. Return saved comparisons for listing and detail display.

### Observability

1. Application exposes health/readiness endpoint(s).
2. Runtime log level is selectable via app startup debug flag (`--debug` toggles debug vs info level).

## Runtime Configuration Contract

Runtime startup reads `src/config.yaml` and validates the config shape before serving requests.

The config contract includes six required top-level sections:

1. `app`
2. `logging`
3. `database`
4. `openai`
5. `workflow`
6. `agents`

Validation behavior:

1. Missing required section or invalid value type results in startup failure with explicit error details.
2. Unknown/extra keys are treated as config errors.
3. Optional keys may use defaults defined by backend config types.
4. `agents.entry_creation` and `agents.parse_entry` must be configured:
   - `entry_creation` drives natural-language conversational assistant replies
   - `parse_entry` parses user turns/conversation transcript into mergeable structured offer data
5. `agents.entry_creation.tools` configures optional function tools the chat agent can call (for example `submit_entry`).
6. `openai.accepted_audio_extensions` defines the allowed file extensions for audio transcription intake validation.

## Persistence Contract

SQLite is the system of record.

Persisted entities must support:

1. Offer create/read/update
2. Stored blank values for omitted offer fields
3. Saved comparison records with selected offer IDs, summary text, and optional note
4. Created/updated timestamps for offers and saved comparisons

## Out-of-Scope (Current Version)

1. Comparison scoring/ranking logic
2. Multi-currency support
3. Authentication/authorization
4. Multi-user tenancy
