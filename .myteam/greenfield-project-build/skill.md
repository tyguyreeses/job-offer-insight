---
name: Greenfield Project Build
description: |
  Orchestrates how to plan and scaffold a new project from scratch before
  implementation. Use this skill to produce end-goal docs, interface contracts,
  implementation plans, stage checkpoints, and test strategy.
---

## Greenfield Project Build

Use this as the parent orchestration skill for scratch-project planning.

### Inputs to collect up front

Require these before planning implementation:

1. End-goal product description (pages, flows, desired behavior)
2. Required vs optional data fields
3. Validation rules (hard-blocking vs soft warnings)
4. Persistence rules (`null`/blank semantics)
5. Deferred/out-of-scope features
6. Tech stack and architecture constraints
7. UX interaction rules (selection limits, defaults, placeholders)
8. Reference resources/folders (if available)

If any are missing, ask the user to provide them before moving forward.

### Execution order

Load and apply subskills in this order:

1. `end-goal-authoring`
2. `interface-contract-writing`
3. `skeleton-audit`
4. `directory-tree-design`
5. `implementation-planning`
6. `stage-checkpoint-planning`
7. `test-strategy-contract-first`
8. `scope-control`
9. `decision-log-maintenance`
10. `handoff-readiness`

`reference-integration` is optional but should be suggested whenever a
reference folder, prototype, or external architecture resource is present.

### Quality gates

Do not start implementation planning until:

1. End-goal doc is concrete enough to eliminate major ambiguities
2. Interface contract is black-box and testable
3. Skeleton audit identifies what exists vs missing
4. Stage checkpoints are approved by user

### Deliverables expected from this skill family

1. End-goal document
2. Application interface contract document
3. Implementation plan with dependency-aware sequence
4. Stage-by-stage checkpoint docs with review gates
5. Contract-first test strategy
6. Decision log entries for key tradeoffs
