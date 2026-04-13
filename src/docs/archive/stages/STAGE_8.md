# STAGE 8 - Edit Offer Form + Full Test Suite + Hardening

## Metadata
- Stage ID: `8`
- Status: `Not Started`
- Completed: `false`
- Started On: ``
- Completed On: ``
- Branch: ``
- Depends On: `Stage 7`
- Primary Docs: `src/docs/application_interface.md`, `PLAN.md`, `.myteam/testing/skill.md`

## Goal
Complete edit flow requirements and finalize black-box test coverage and release hardening.

## Scope
- Edit existing offer via pre-filled structured form
- Ensure edit flow bypasses open-ended initial AI intake page
- Complete backend/frontend/e2e tests aligned with interface contract
- Final pass on logging/config errors/docs run instructions

## Out of Scope
- New product features not already in `end-goal.md`
- Comparison ranking/scoring logic

## Entry Criteria
- Stage 7 completed and approved
- Core intake/dashboard/compare flows implemented

## Implementation Checklist
- [ ] Implement offer edit form + update submission flow
- [ ] Verify edit route does not use initial AI intake screen
- [ ] Complete missing black-box tests across backend and frontend
- [ ] Add/confirm end-to-end critical path tests
- [ ] Run full test suite from repo root
- [ ] Update README run/test notes

## Deliverables
- Contract-complete feature set for this version
- Passing test suite and release-ready docs

## Test Gate
- [ ] Run `poetry run pytest -q` (or `python -m pytest -q` in active env)
- [ ] Verify black-box test coverage maps to interface sections
- [ ] Verify no tests rely on unstable internal implementation details

## Exit Criteria
- All contract requirements from `application_interface.md` are met
- Test suite passes and demonstrates observable behavior guarantees
- User signs off on readiness for merge/release

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage


