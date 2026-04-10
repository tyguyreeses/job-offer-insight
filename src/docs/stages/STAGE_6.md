# STAGE 6 - Dashboard + Selection Rules + Card Presentation

## Metadata
- Stage ID: `6`
- Status: `Not Started`
- Completed: `false`
- Started On: ``
- Completed On: ``
- Branch: ``
- Depends On: `Stage 5.1`
- Primary Docs: `src/docs/application_interface.md`, `end-goal.md`

## Goal
Implement dashboard presentation, post-intake dashboard routing, and enforce the two-selection comparison rule.

## Scope
- Post-intake navigation: when intake is saved via `Finish` button or chat-agent submit tool, route user to Dashboard
- Horizontal side-scroll offer card layout
- Card field display ordering
- Sorting behavior with explicit defaults and controls
  - Default: entries shown left-to-right by date (newest first unless contract says otherwise)
  - User control: `Sort by` dropdown to change ordering
- Card display omission rule: optional fields with blank/omitted values are hidden (no `None`/`null`/`N/A` placeholders)
- Max-two selection behavior with oldest deselection on third selection
- Non-monetary AI bullet-point summary display (stored summary)

## Out of Scope
- Comparison scoring logic
- Saved comparison persistence behavior

## Entry Criteria
- Stage 5.1 completed and approved
- Offer retrieval APIs available

## Implementation Checklist
- [ ] Route to Dashboard automatically after successful intake save (`Finish` or chat-agent tool submit)
- [ ] Implement dashboard page shell and card grid/scroll behavior
- [ ] Implement card display fields in specified order
- [ ] Implement `Sort by` dropdown and backend/frontend sort integration
- [ ] Set and test default sort order (left-to-right by date)
- [ ] Ensure optional blank fields are not rendered on cards
- [ ] Implement card selection state with oldest-deselect rule
- [ ] Render non-monetary stored bullet summary on cards

## Deliverables
- Dashboard with browse/sort/select behavior per contract
- Successful intake save transitions user directly to Dashboard to view new + prior entries

## Test Gate
- [ ] Successful save via `Finish` button redirects to Dashboard
- [ ] Successful save via chat-agent submit tool redirects to Dashboard
- [ ] Card display ordering test
- [ ] Default date sort (left-to-right) test
- [ ] `Sort by` dropdown behavior test
- [ ] Optional blank fields hidden test (no `None`/`null`/`N/A` rendering)
- [ ] Selection cap test (third selection deselects first)

## Exit Criteria
- Dashboard behavior is contract-complete
- Selection behavior is deterministic and tested
- User approves stage outputs before Stage 7

## Feedback and Revisions

### User Feedback


### Requested Revisions


### Final Decisions for This Stage
