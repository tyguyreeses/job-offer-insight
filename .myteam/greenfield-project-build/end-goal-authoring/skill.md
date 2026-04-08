---
name: End Goal Authoring
description: |
  Guides the user to create a strong end-goal document for a new project.
  Use this before interface contracts or implementation planning.
---

## End Goal Authoring

Create or refine an end-goal document with clear, concrete behavior.

### Required sections

1. Product identity and purpose
2. User types and top use cases
3. Page-by-page behavior and navigation defaults
4. Data schema expectations
5. Required fields and optional fields
6. Validation behavior (hard failures vs warnings)
7. Missing-information policy and storage semantics
8. Core UI interaction rules
9. Persistence/storage choices
10. Comparison/evaluation logic (or explicit deferment)
11. Edit/update flows
12. Non-goals and deferred features
13. Technology and architecture constraints
14. Acceptance checklist

### Authoring process

1. Start with user-provided intent and constraints
2. Convert vague wording into explicit behavioral rules
3. Propose a sample schema if one is not present
4. Confirm unresolved decisions one-by-one
5. Document explicit placeholders for deferred logic

### Completion criteria

The end-goal doc is complete when a separate engineer can derive API/UI behavior
without guessing on critical flows.
