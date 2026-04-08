---
name: Test Strategy Contract First
description: |
  Defines testing strategy by mapping tests directly to black-box interface
  behavior rather than internal implementation details.
---

## Test Strategy Contract First

Build tests that prove the documented contract is satisfied.

### Strategy

1. Map interface sections to test modules
2. Prioritize observable outcomes (responses, persisted state, UI behavior)
3. Avoid fragile assertions tied to helper internals
4. Cover happy paths, failure paths, and edge-case behavior

### Required coverage categories

1. Validation behavior (required vs soft warnings)
2. Persistence behavior (including blank/null semantics)
3. Flow behavior (intake, edit, compare modes)
4. Interaction rules (selection limits, placeholder states)
5. Readiness/health observable behavior

### Execution guidance

Run tests using project-standard command for the repo.
If a testing skill already exists in project `.myteam`, defer to it for exact
commands and philosophy.

### Completion criteria

Every core interface behavior has corresponding black-box tests.
