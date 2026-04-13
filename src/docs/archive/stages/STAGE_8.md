# STAGE 8 - Comparison Generation Foundations + Edit Surface Refinement

## Metadata
- Stage ID: `8`
- Status: `Completed`
- Completed: `true`
- Started On: `2026-04-11`
- Completed On: `2026-04-11`
- Branch: `stage_8`
- Depends On: `Stage 7`
- Primary Docs: `src/docs/application_interface.md`, `PLAN.md`, `end-goal.md`

## Goal
Prepare the comparison system for real generated output by refining offer display/edit foundations, locking deterministic monetary summary behavior, and finalizing comparison generation contracts for `one_to_one` and `one_to_all`.

## Scope
- Add derived monetary metrics:
  - `Estimated Total Annual Monetary Benefits`
  - `Monthly Take-Home`
- Place derived monetary summary at top of relevant offer displays.
- Implement deterministic config-driven take-home estimation using:
  - global default tax profile
  - optional per-offer overrides
- Redesign edit form behavior:
  - always show required fields
  - show non-required fields only when populated
  - add `+` control to add optional fields grouped by section
  - include tax-overrides section as an addable optional section
  - clearing an optional value saves it as omitted and hides it on next edit unless re-added
- Add monetary calculation explanation affordance (hover info box / tooltip pattern).
- Finalize and implement comparison generation flow:
  - compare draft canvas includes a `Generate Comparison` button
  - clicking generate starts pending state/animation
  - code-generated comparison section renders first
  - AI-generated comparison section shows pending until complete
  - generated comparison remains draft until explicitly saved
  - navigating away from unsaved generated results prompts discard confirmation
- Finalize one-to-one generation behavior:
  - deterministic code computes per-metric percentage differences between selected offers
  - optional numeric fields are compared only when present in both offers
  - AI compares non-monetary benefits and included non-required field differences
- Finalize one-to-all generation behavior:
  - deterministic code compares base offer vs all other offers
  - per numeric metric, compute percentage difference between base and highest other value
  - per numeric metric, provide most similar other offer (closest-by-value for that metric)
  - AI explains unique strengths, unique weaknesses, and missing-item downsides across all other offers
  - AI section includes a brief bottom summary
- Keep comparison notes space in generated-comparison flow.
- Define comparison AI agents in config with prompts stored under `src/backend/prompts`, with separate prompts/agents for `one_to_one` and `one_to_all`.

## Out of Scope
- Winner selection, ranking, or numeric scoring framework beyond deterministic per-metric percentage comparisons
- Non-deterministic/LLM-only tax estimation

## Entry Criteria
- Stage 7 completed and approved
- Core intake/dashboard/compare placeholder flows implemented
- Stage 8 generation requirements are decision-complete for `one_to_one` and `one_to_all`

## Implementation Checklist
- [x] Update interface docs for new derived monetary metrics and edit-form visibility rules
- [x] Add/validate config shape for global tax defaults and per-offer tax overrides
- [x] Implement backend deterministic calculators for:
  - estimated annual monetary total
  - estimated monthly take-home
- [x] Surface derived metrics in dashboard cards, compare cards, and edit panel summary
- [x] Implement edit form `+` add-field workflow grouped by section
- [x] Implement optional tax-overrides section reveal via add-field workflow
- [x] Add `Generate Comparison` draft workflow with pending states and progressive rendering (code first, AI second)
- [x] Add unsaved generated-result discard confirmation on context switches/navigation
- [x] Implement one-to-one and one-to-all deterministic numeric generation contracts
- [x] Implement one-to-one and one-to-all AI generation contracts
- [x] Add/update config-defined comparison agents and prompt files in `src/backend/prompts`
- [x] Add/update backend and frontend tests for derived metrics, comparison generation flow, and edit visibility behavior

## Deliverables
- Updated contract and implementation base for comparison generation work
- Deterministic derived monetary display behavior with explanation UI
- Edit surface supporting required-always-visible + optional-on-demand fields
- Decision-complete and implemented generation behavior for `one_to_one` and `one_to_all`

## Test Gate
- [x] Run backend tests: `python -m pytest -q`
- [x] Run frontend tests: `cd src/frontend && npm test`
- [ ] Verify derived totals/take-home use deterministic formulas and config defaults
- [ ] Verify per-offer override behavior (state, filing status, pre-tax %) updates take-home output
- [ ] Verify required edit fields are always visible
- [ ] Verify optional fields are hidden unless populated or explicitly added via `+`
- [ ] Verify clearing optional values persists omission/hide behavior on subsequent edit loads
- [ ] Verify `Generate Comparison` shows code results before AI results and shows AI pending state
- [ ] Verify unsaved generated results trigger discard confirmation when leaving/switching context
- [ ] Verify one-to-one numeric percent comparisons and optional-field comparison gating
- [ ] Verify one-to-all per-metric highest-difference and per-metric similarity outputs
- [ ] Verify AI summary sections render expected blocks for one-to-one and one-to-all

## Exit Criteria
- Stage 8 foundation behavior is contract-complete and tested
- Comparison generation contracts for `one_to_one` and `one_to_all` are implemented and verified
- User signs off on Stage 8 scope before implementation moves to next stage

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage
- Derived metrics for v1:
  - monetary score represented as dollar total only
  - year-1 cash emphasis
  - monthly take-home from deterministic config defaults + optional per-offer overrides
- Edit surface rules:
  - required fields always visible
  - optional fields added via `+` and hidden when omitted
- Comparison mode naming:
  - use `one_to_one` and `one_to_all` consistently
  - do not use `one-to-many` naming in Stage 8 contracts
- Generation trigger and progressive rendering:
  - compare draft canvas includes a `Generate Comparison` button
  - clicking it starts generation and shows pending animation/status
  - code-generated comparison section renders first as soon as deterministic calculations complete
  - AI-generated section remains pending until agent output completes
- Draft and save behavior:
  - generated output remains draft/unsaved until user explicitly saves comparison data
  - if user switches away from a view where unsaved generated data would be lost, UI prompts for discard confirmation
- One-to-one generation contract:
  - code-generated output computes percentage differences for numeric metrics between two selected offers
  - optional numeric fields are compared only when included in both offers
  - AI-generated output compares non-monetary benefits and differences in included non-required fields
- One-to-all generation contract:
  - code-generated output compares base-offer numeric metrics against all other offers
  - per numeric metric, return percentage difference between base value and the highest value among other offers
  - per numeric metric, return the most similar other offer (closest-by-value for that specific metric)
  - AI-generated output reviews all other offers and explains what makes the base offer uniquely better, uniquely worse, and weaker due to missing items
  - AI output includes a brief summary block at the bottom
- Notes support:
  - comparison view includes space for user notes in generated-comparison workflow
- Agent/config requirements:
  - comparison AI agents must be config-defined
  - prompts must live in `src/backend/prompts`
  - use separate prompts/agents for `one_to_one` and `one_to_all`
- Ranking/scoring policy:
  - no winner/ranking/scoring framework is introduced in Stage 8
