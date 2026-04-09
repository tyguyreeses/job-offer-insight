# STAGE 4.1 - AI Text Extraction to Offer Schema

## Metadata
- Stage ID: `4.1`
- Status: `Not Started`
- Completed: `false`
- Started On: ``
- Completed On: ``
- Branch: `stage-4.1-gen-ai`
- Depends On: `Stage 4`
- Primary Docs: `end-goal.md`, `src/docs/application_interface.md`

## Goal
Replace Stage 4 heuristic text parsing with AI-assisted extraction that converts open-ended user text into the standardized offer JSON schema required for persistence.

## Scope
- `gen_ai` agent framework for AI task orchestration
- Text parser agent definition and routing for open-ended intake text
- Open-ended text intake to structured JSON extraction using OpenAI client
- Pydantic-enforced extraction output contract before downstream validation/persistence
- Deterministic mapping from model output into the offer schema contract
- Required field and compensation-path validation after extraction
- Missing-info follow-up prompt generation from extracted payload
- Optional-field omission confirmation flow compatibility with Stage 4 behavior
- Runtime config extension with a new top-level `agents` section for agent definitions
- Observability for extraction failures and malformed model output

## Out of Scope
- Audio ingestion/transcription (Stage 5)
- Dashboard, compare, and edit UI behavior
- Comparison scoring/ranking logic

## Entry Criteria
- Stage 4 completed and approved
- Runtime config includes `openai` and workflow toggles
- Runtime config contract update approved for a top-level `agents` section
- Offer persistence path is stable for save/list/get/update

## Text-to-Schema Conversion Contract

### Reference-Informed Framework Decisions
1. Use a config-driven agent declaration pattern inspired by `reference-audio-material/agents.py` and `reference-audio-material/run_agent.py`:
   - one runtime agent registry
   - agent entries resolved from config
   - model/prompt settings attached to each agent definition
2. Adapt the pattern to backend service usage (non-CLI), keeping DI boundaries from this repo.
3. Keep the framework intentionally small for Stage 4.1:
   - one parser-oriented agent execution path (`text_parser`)
   - reusable interface that can support additional agents later (audio and summary stages)
4. Do not copy reference scripts directly; treat them as architectural examples only.

### Input
1. User submits free-form text in `POST /api/v1/offers/intake/text`.
2. Optional client-provided `extracted_offer_overrides` may patch extracted fields before validation.

### Extraction
1. Route intake text through the `text_parser` agent in the new `gen_ai` agent framework.
2. Send intake text to OpenAI with an extraction prompt that requests only schema-aligned JSON output.
3. Validate agent output against a Pydantic extraction model before mapping/persistence.
4. Require strict JSON object response shape (no prose) for extraction output.
5. Reject/repair invalid model output and surface observable extraction errors when unrecoverable.

### Agent Configuration
1. Add a new top-level `agents` section in runtime config for agent declarations.
2. Define a `text_parser` agent entry with provider/model and prompt binding required for intake extraction.
3. Keep existing top-level config sections unchanged in behavior; this stage only extends config shape to support agents.

### Mapping and Normalization
1. Map extracted fields into the standardized offer schema from `end-goal.md`.
2. Normalize numeric/currency fields to USD numeric values where applicable.
3. Apply annualization rule when hourly fields are provided and annual base is missing:
   - `hourly_rate_usd * hours_per_week * 52`
4. Preserve blank representations for omitted optional fields (`null`, `""`, `[]`) by field type.

### Validation and Follow-ups
1. Enforce hard-required save constraints:
   - `company_name`
   - `role_title`
   - base pay path (`annual_base_salary_usd` OR hourly+hours/week)
2. For missing optional fields, return guided prompts so user can either provide values or confirm omission.
3. Persist offer only when required fields pass and omission confirmations are resolved.

### Persistence
1. Save final normalized payload through existing repository path.
2. Preserve `offer_meta` semantics from Stage 4 (`source_input_type`, timestamps, status).

## Implementation Checklist
- [ ] Add backend `gen_ai` agent framework interfaces and runtime wiring
- [ ] Add `agents` top-level config section and typed config models
- [ ] Define `text_parser` agent in config and bind to extraction prompt
- [ ] Add OpenAI client integration in backend `gen_ai` layer
- [ ] Add extraction prompt/template for text-to-offer JSON conversion
- [ ] Add Pydantic model(s) for parser output contract
- [ ] Add mapper/validator from model JSON to persisted schema payload
- [ ] Replace fallback regex extraction with AI-first extraction path
- [ ] Preserve Stage 4 required/optional validation and omission confirmation behavior
- [ ] Add explicit extraction error response behavior for invalid/unusable model output
- [ ] Add tests for open-ended text extraction success and failure paths

## Deliverables
- Reliable AI-assisted text intake that converts unstructured text into schema-ready offer payloads
- Contract-aligned missing-info and save/blocked behavior over extracted output

## Test Gate
- [ ] Happy path: open-ended raw text -> extracted schema payload -> saved offer
- [ ] Required-field block: extraction output missing required fields returns `blocked_required_fields`
- [ ] Missing optional fields: returns `missing_information` prompts and saves after confirmations
- [ ] Annualization: hourly extraction correctly computes annual base salary
- [ ] Invalid model output: observable extraction failure response without corrupt persistence
- [ ] Pydantic contract test: malformed parser output fails validation and does not save
- [ ] Config contract test: startup fails clearly for invalid/missing required `agents.text_parser` configuration

## Exit Criteria
- Raw text intake no longer depends on Stage 4 regex fallback for core extraction behavior
- Text intake extraction is orchestrated through configured `text_parser` agent
- Parser output is Pydantic-validated before schema mapping and persistence
- Extracted payloads conform to documented schema semantics in `end-goal.md`
- Behavior remains consistent with existing Stage 4 validation and omission-confirmation contract
- User approves stage outputs before Stage 5 implementation continues

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage
