# STAGE 6 - Dashboard + Selection Rules + Card Presentation

## Metadata
- Stage ID: `6`
- Status: `Not Started`
- Completed: `false`
- Started On: ``
- Completed On: ``
- Branch: ``
- Depends On: `Stage 5`
- Primary Docs: `src/docs/application_interface.md`, `end-goal.md`

## Goal
Implement dashboard presentation and enforce the two-selection comparison rule.

## Scope
- Horizontal side-scroll offer card layout
- Card field display ordering
- Changeable sorting behavior
- Max-two selection behavior with oldest deselection on third selection
- Non-monetary AI bullet-point summary display (stored summary)

## Out of Scope
- Comparison scoring logic
- Saved comparison persistence behavior

## Entry Criteria
- Stage 5 completed and approved
- Offer retrieval APIs available

## Implementation Checklist
- [ ] Implement dashboard page shell and card grid/scroll behavior
- [ ] Implement card display fields in specified order
- [ ] Implement sort controls and backend/frontend integration
- [ ] Implement card selection state with oldest-deselect rule
- [ ] Render non-monetary stored bullet summary on cards

## Deliverables
- Dashboard with browse/sort/select behavior per contract

## Test Gate
- [ ] Card display ordering test
- [ ] Sort behavior test
- [ ] Selection cap test (third selection deselects first)

## Exit Criteria
- Dashboard behavior is contract-complete
- Selection behavior is deterministic and tested
- User approves stage outputs before Stage 7

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage


