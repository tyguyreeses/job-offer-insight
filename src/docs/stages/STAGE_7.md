# STAGE 7 - Compare Modes + Saved Comparisons

## Metadata
- Stage ID: `7`
- Status: `Completed`
- Completed: `true`
- Started On: `2026-04-11`
- Completed On: `2026-04-11`
- Branch: `stage_7`
- Depends On: `Stage 6`
- Primary Docs: `src/docs/application_interface.md`, `end-goal.md`

## Goal
Implement one-to-one and one-to-all compare layouts with placeholder sections and saved comparison records.

## Scope
- Compare page layout behavior by mode
- One-to-one: left + placeholder middle + right
- One-to-all: left + placeholder middle + placeholder right
- Save comparison (offer IDs + placeholder summary + optional user note persistence)
- Retrieve/display saved comparisons
- Optional note is saved but not rendered on compare page in this stage

## Out of Scope
- Comparison scoring/ranking logic

## Entry Criteria
- Stage 6 completed and approved
- Dashboard selection state can provide valid compare inputs

## Implementation Checklist
- [x] Implement compare mode selection and routing behavior
- [x] Implement one-to-one layout rendering contract
- [x] Implement one-to-all layout rendering contract
- [x] Implement save comparison endpoint/service
- [x] Implement saved comparison list/detail retrieval
- [x] Persist optional note with saved comparison records

## Deliverables
- Working compare flows for one-to-one and one-to-all with placeholders
- Saved comparison lifecycle (create/list/view)

## Test Gate
- [x] One-to-one layout test (left+middle placeholder+right)
- [x] One-to-all layout test (left+placeholder middle+placeholder right)
- [x] Saved comparison persistence test (IDs + placeholder summary + optional note)
- [x] Compare page does not render optional note text

## Exit Criteria
- Compare flows match contract exactly with no scoring logic
- Saved comparison behavior is stable and reviewable
- User approves stage outputs before Stage 8

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage
