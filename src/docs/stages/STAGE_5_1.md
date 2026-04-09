# STAGE 5.1 - Main Page + Conversational Offer Intake

## Metadata
- Stage ID: `5.1`
- Status: `Implemented (Pending Manual QA + User Sign-off)`
- Completed: `false`
- Started On: `2026-04-09`
- Completed On: ``
- Branch: `stage-5.1`
- Depends On: `Stage 5`
- Primary Docs: `src/docs/application_interface.md`, `end-goal.md`

## Goal
Implement the Main Page UX for creating an offer and replace one-shot text intake with a server-side conversational flow that supports iterative user input.

## Scope
- Build frontend scaffold (`Vite + React + TypeScript`) in `src/frontend`
- Main page UX:
  - Large, centered header text: `Create a Job Entry` across a mostly empty page
  - Two large, centered round buttons: `Text` and `Audio`
  - Text button fades out button group and fades in text input UI
  - Assistant message fades in above text box
  - Submit button with notice underneath: user can edit this info later
  - Conversation-first UX where the user can continue adding information turn-by-turn
- Styling and motion (build directly from `end-goal.md`):
  - Custom CSS styling (no default browser-like appearance)
  - Clean, minimal visual style with large centered content hierarchy
  - Soft blue glow hover effect on selectable controls (buttons and interactive elements)
  - Smooth loading/reveal choreography with fade-in sequencing top-to-bottom and left-to-right
  - Use one shared reusable fade animation system (project-wide), not per-page custom fade keyframes
  - Elegant navbar shell consistent with product navigation direction in `end-goal.md`
- Replace `POST /api/v1/offers/intake/text` one-shot behavior with conversational behavior
- In-memory backend conversation session state for text intake
- Required fields asked together first
- Then one prompt for additional monetary benefits (with 2-3 examples)
- Then one prompt for additional non-monetary benefits (with 2-3 examples)
- Then ask: `is there anything else?`
- Finish action blocked until required fields are complete
- If user attempts finish too early, return natural-language assistant message listing remaining required info
- Mixed omission handling:
  - explicit skip action for current prompt
  - typed omission intent in user text
- Parse each follow-up reply and merge into existing session payload
- Preserve existing normalization/validation/persistence rules for final save
- Audio button currently does nothing when clicked (no UI warning required)

## Out of Scope
- Audio recording or audio upload UX in this stage
- Changes to `POST /api/v1/offers/intake/audio`
- Persistence of conversation sessions beyond process lifetime (no DB-backed sessions yet)
- Dashboard/compare/edit page behavior changes

## Entry Criteria
- Stage 5 completed and approved
- Existing text/audio intake tests are passing before contract migration
- User approval to break old one-shot text intake contract

## API/Contract Changes
- `POST /api/v1/offers/intake/text` becomes conversational (breaking change)
- Request supports conversation actions: `submit`, `skip_current`, `finish`
- Response includes:
  - assistant message text
  - conversation state
  - missing-required summary
  - `can_finish` flag
  - save outcome when complete

## Implementation Checklist
- [x] Update `src/docs/application_interface.md` to conversational text-intake contract
- [x] Add in-memory intake session store
- [x] Add/modify service orchestration for conversation step machine
- [x] Replace old one-shot text-intake response shape on `/offers/intake/text`
- [x] Add mixed omission handling (`skip_current` + typed omission)
- [x] Build `src/frontend` scaffold with Vite React TypeScript
- [x] Implement main page layout with large centered heading and large centered round mode buttons
- [x] Implement custom CSS styling for a clean, minimal, mostly empty first screen
- [x] Implement soft blue glow hover treatment for selectable interactive elements
- [x] Implement loading/reveal animation sequence (top-to-bottom and left-to-right fade choreography)
- [x] Create shared animation tokens/utilities for fade enter/exit and reuse them for all Stage 5.1 motion
- [x] Implement elegant navbar shell aligned with end-goal navigation expectations
- [x] Wire frontend conversation UI to new text-intake contract
- [x] Keep audio button visually present and non-functional (no state change on click)

## Deliverables
- Runnable frontend main page for end-to-end "create offer" UX testing
- Stateful conversational text intake from first prompt through final save
- Updated interface documentation reflecting the new text intake contract

## Test Gate
- [x] Backend test: conversation start returns required-fields prompt bundle
- [x] Backend test: finish blocked until required fields complete with natural-language missing-required message
- [x] Backend test: incremental parse/merge across turns saves correct payload
- [x] Backend test: `skip_current` omission behavior is applied correctly
- [x] Backend test: prompt sequence order is deterministic
- [x] Frontend test: initial page renders title + two large round buttons
- [x] Frontend test: text click triggers fade transition and input reveal
- [x] Frontend test: assistant message region appears/updates above input
- [x] Frontend test: finish behavior follows backend state (`can_finish` / blocked)
- [x] Frontend test: audio button click causes no state change
- [x] Frontend test: selectable controls apply blue-glow hover style
- [x] Frontend test: staged fade/reveal sequence order is deterministic (header -> controls -> conversation region)
- [x] Frontend test: Stage 5.1 fade transitions consume shared motion utilities/tokens (no page-specific fade keyframes)
- [ ] Manual QA: first screen visually matches end-goal styling constraints (large centered text, clean minimal layout, elegant navbar)
- [ ] Manual QA: full conversational flow to saved offer

## Progress Snapshot (2026-04-09)

- Implemented conversational backend contract and state machine on `/api/v1/offers/intake/text`.
- Implemented frontend scaffold and Add Entry page UX/styling/motion for Stage 5.1.
- Added automated backend and frontend tests for Stage 5.1 behavior.
- Applied follow-up fixes from code-linter review:
  - hardened typed omission detection to avoid substring false positives
  - refreshed `README.md` stage status
  - removed tracked `tsbuildinfo` artifact and ignored `*.tsbuildinfo`
- Ran second-pass parallel agent review:
  - `Code Linter`: no actionable findings remain
  - `Project-scope .myteam update`: no additional migrations required

Validation results:
- `PYTHONPATH=. pytest -q tests/backend` -> pass
- `PYTHONPATH=. pytest -q tests/backend/test_offer_intake_stage4.py tests/backend/test_offer_intake_stage5_audio.py` -> pass
- `cd src/frontend && npm test` -> pass
- `cd src/frontend && npm run build` -> pass

## Exit Criteria
- Main Page matches intended UX behavior for creating an offer
- Main Page styling and animation behavior matches `end-goal.md` direction
- Text intake is conversational and stateful across turns
- Required-field gating and final-save behavior are enforced
- Automated backend and frontend tests for Stage 5.1 pass
- User approves stage outputs before Stage 6 continuation

## Feedback and Revisions

### User Feedback
- Stage 5.1 should prioritize full Main Page UX testing for offer creation.
- Existing one-shot intake should be replaced by a real conversational backend flow.
- Required information should be asked together first.
- Optional prompts should be grouped (monetary, non-monetary) rather than exhaustive per-field interrogation.
- Audio button should remain on the page but do nothing for now.
- Styling/animation are critical and must build directly from `end-goal.md`.
- Main page should be mostly empty with large centered title and large round input-mode buttons.
- Conversation transitions should animate: controls fade out, input and assistant message fade in.

### Requested Revisions
- Replace old text intake contract instead of adding parallel endpoints.
- Use template-based natural-language assistant messages (no extra LLM phrasing call).
- Use in-memory conversation state in this stage.
- Add backend + frontend automated tests in Stage 5.1.

### Final Decisions for This Stage
- `/offers/intake/text` is now conversational and breaking-change by design.
- Session state is backend in-memory only for Stage 5.1.
- Conversation sequence:
  1. Required fields bundle
  2. Additional monetary benefits prompt
  3. Additional non-monetary benefits prompt
  4. "Is there anything else?"
  5. Save
- Audio button remains inert (no-op) in this stage.
- UI styling baseline is mandatory in this stage: custom CSS, centered minimal composition, blue hover glow, and smooth staged fades.

## Implementation Contract Addendum (Decision Lock)

This addendum freezes implementation details so a new Codex session can execute Stage 5.1 without making product decisions.

### API Schema Lock (`POST /api/v1/offers/intake/text`)

Request JSON:
- `session_id: string | null`  
  - `null` starts a new conversation
  - non-null continues an existing in-memory conversation
- `action: "submit" | "skip_current" | "finish"`  
  - `submit` parses and merges `message_text`
  - `skip_current` confirms omission for the current prompt target
  - `finish` attempts final save
- `message_text: string`  
  - required for `submit`
  - ignored for `skip_current`
  - optional for `finish` (if present, parse/merge before finish validation)

Response JSON:
- `session_id: string`
- `status: "in_progress" | "blocked_required_fields" | "saved" | "extraction_failed"`
- `assistant_message: string`
- `step: "collect_required" | "collect_monetary_extras" | "collect_non_monetary_extras" | "anything_else" | "completed"`
- `can_finish: bool`
- `missing_required_fields: list[string]`
- `current_prompt_key: string | null`
- `offer: object | null`
- `errors: list[string]`
- `warnings: list[string]`

Behavior:
- Keep HTTP `200` for successful conversational turns and save attempts.
- Use HTTP `422` only for malformed request shape/types.
- Use HTTP `404` when a provided `session_id` does not exist.

### Conversation State Machine Lock

1. `collect_required`
- First assistant turn asks for all currently missing required fields in one message.
- On each `submit`, parse user message, merge extracted fields, recompute required gaps.
- If required gaps remain, stay in `collect_required`.
- If required fields complete, advance to `collect_monetary_extras`.

2. `collect_monetary_extras`
- Assistant asks once for additional monetary benefits with 2-3 examples.
- On `submit`, parse/merge and advance to `collect_non_monetary_extras`.
- On `skip_current`, advance to `collect_non_monetary_extras`.

3. `collect_non_monetary_extras`
- Assistant asks once for additional non-monetary benefits with 2-3 examples.
- On `submit`, parse/merge and advance to `anything_else`.
- On `skip_current`, advance to `anything_else`.

4. `anything_else`
- Assistant asks: "Is there anything else?"
- On `submit`, parse/merge and remain in `anything_else` with `can_finish=true`.
- On `finish`, attempt save.

5. `finish` rules
- If required fields missing, do not save; return `blocked_required_fields`, remain `collect_required`, and return natural-language missing-required message.
- If required fields complete, apply existing normalization/validation/persistence flow and return `saved` with persisted offer payload; mark step `completed`.

### Omission Detection Lock

- Explicit omission: `action="skip_current"` always marks omission for the current prompt target.
- Typed omission intent (for `submit`) is recognized when `message_text` contains any of:
  - `no`
  - `none`
  - `n/a`
  - `not applicable`
  - `don't have`
  - `do not have`
  - `not part of this offer`
- Typed omission applies only to `current_prompt_key` and does not globally omit unrelated fields.

### Assistant Message Templates Lock

- Required bundle:
  - `"Please share the remaining required information: {required_list}. You can provide it in one message."`
- Required blocked on premature finish:
  - `"I still need required information before saving: {required_list}."`
- Monetary extras:
  - `"Any additional monetary benefits to include (for example retirement match, signing bonus, equity grant)? If none, you can skip."`
- Non-monetary extras:
  - `"Any additional non-monetary benefits to include (for example culture, mission alignment, wellness/perks)? If none, you can skip."`
- Anything else:
  - `"Is there anything else you want to add before saving?"`
- Saved:
  - `"Great, your offer has been saved. You can edit details later."`

### Frontend Motion Spec Lock

- Motion architecture:
  - Define a single shared fade animation system to be reused across the project.
  - Shared system includes enter and exit variants; pages may only customize delay/stagger and not redefine keyframes.
  - Place motion tokens and reusable classes/utilities in shared frontend styling layer (for example `styles/tokens.css` + `styles/global.css`).
- Entry reveal on initial load:
  - heading fade-in: `220ms`, delay `0ms`
  - button group fade-in: `220ms`, delay `80ms`
- Text-mode transition:
  - button group fade-out: `180ms`
  - text input container fade-in: `220ms`, delay `80ms`
- Assistant message appearance:
  - fade-in + slight upward transform (`translateY(6px -> 0)`): `200ms`
- Easing:
  - use `ease-out` for fade-in transitions
  - use `ease-in` for fade-out transitions

### Navbar Scope Lock

- Stage 5.1 implements a minimal elegant navbar shell with three labels:
  - `Dashboard`
  - `Add Entry`
  - `Compare`
- In this stage, navbar links may be non-functional placeholders except `Add Entry` (current page).
- Visual styling must still meet the clean/minimal/elegant baseline from `end-goal.md`.
