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
3. Base pay path:
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

## Navbar Behavior

1. `Dashboard` is default when at least one offer entry exists.
2. `Add Entry` is default when no offer entries exist.
3. `Compare` page:
   - If navigated from dashboard compare action, selection context is pre-populated.
   - If opened directly, user can choose offers by company name.
   - If saved comparisons exist, they are listed.

## Add Entry Page

1. Displays large primary prompt to add a job.
2. Provides two input modes:
   - Audio input
   - Text input
3. Audio input is transcribed to text.
4. AI extracts structured offer data.
5. System asks clarifying follow-up questions for missing fields.
6. User can confirm omitted fields as "not part of offer."

## Edit Offer Flow

1. Existing offers are editable.
2. Editing uses a pre-filled structured form.
3. Editing does not route user through the initial open-ended AI intake flow.

## Dashboard Page

1. Shows offer cards in horizontal side-scroll layout.
2. Cards can be sorted by changeable option.
3. Card vertical display order:
   - Salary
   - Monetary benefits
   - Non-monetary benefits (AI bullet-point summary, generated once then stored)
   - Date created (`mm-dd-yyyy`)
4. Compare selection rules:
   - Maximum two selected cards
   - On selecting a third card, earliest selected card is automatically deselected

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
3. Audio intake endpoint accepts multipart upload at `POST /api/v1/offers/intake/audio` with:
   - `audio_file` upload (`.wav`, `.mp3`, `.m4a`, `.mp4`, `.mpeg`, `.mpga`, `.webm`)
   - optional `omission_confirmations_json` object text
   - optional `extracted_offer_overrides_json` object text
4. Return missing-field prompts when required for completion decisions.
5. Save accepted blanks as omitted fields.
6. Retrieve offer list and single offer details.
7. Update offer by ID via structured form payload.
8. Audio transcription failures are returned as observable intake status `transcription_failed`.

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
4. `agents.text_parser` must be configured for AI text-intake parsing behavior.

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
