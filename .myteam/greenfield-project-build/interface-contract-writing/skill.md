---
name: Interface Contract Writing
description: |
  Converts end-goal product intent into a black-box application interface
  contract for API behavior, UI behavior, and persistence observables.
---

## Interface Contract Writing

Translate end-goal requirements into externally observable behavior.

### Contract sections

1. Product scope and out-of-scope
2. Data contract (required fields, types, constraints)
3. Validation contract (blocking vs warnings)
4. UI contract (per page and interaction)
5. API contract (behavior-focused, endpoint-path agnostic if needed)
6. Persistence contract (what must be stored and retrieved)
7. Observability contract (health/logging behavior)

### Rules

1. Describe outcomes users/operators can observe
2. Avoid prescribing internal helper implementation details
3. Preserve explicit deferred logic from end-goal doc
4. Ensure every rule is testable

### Completion criteria

Every significant user-facing behavior has an unambiguous, black-box statement.
