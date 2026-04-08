---
name: Directory Tree Design
description: |
  Produces a full suggested project directory tree with responsibilities for
  each module before coding begins.
---

## Directory Tree Design

Design a target project tree aligned to the interface contract and plan.

### Required output

1. Full tree structure
2. Purpose/responsibility for each key directory/file
3. Separation between backend, frontend, docs, tests, and migrations
4. Placement for config, DI, services, repositories, schemas, prompts
5. Placement for styling/animations and UI state modules

### Rules

1. Prefer explicit module ownership boundaries
2. Keep framework concerns separated from business logic
3. Include tests and docs paths in the structure
4. Avoid over-fragmenting early-stage projects

### Completion criteria

The tree is specific enough that implementation tasks can be assigned cleanly.
