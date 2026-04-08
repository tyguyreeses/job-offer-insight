---
name: Handoff Readiness
description: |
  Verifies that planning artifacts are ready for execution handoff, including
  contract alignment, stage completeness, and test strategy traceability.
---

## Handoff Readiness

Run this check before beginning implementation stages.

### Handoff checklist

1. End-goal doc reflects latest approved intent
2. Interface contract matches end-goal and is testable
3. Plan sequence is dependency-aware
4. Stage files exist with strict checklists and metadata fields
5. Test strategy maps to interface behavior
6. Out-of-scope items are clearly documented

### Ready/Not-Ready rule

If any checklist item is unresolved, status is Not-Ready and implementation
should pause until resolved.

### Completion criteria

Project planning artifacts support branch-by-branch execution with low ambiguity.
