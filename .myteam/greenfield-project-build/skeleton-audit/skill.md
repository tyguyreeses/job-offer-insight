---
name: Skeleton Audit
description: |
  Audits the current repository skeleton and reports what exists, how it will
  be used, and what is missing before implementation planning.
---

## Skeleton Audit

Inspect current repo state before planning execution.

### Audit output format

1. Existing structure (files/directories actually present)
2. Intended usage of existing pieces
3. Missing components required to satisfy contract
4. Risks or mismatches between docs and skeleton

### Rules

1. Verify by reading file tree and key docs; do not assume
2. Distinguish empty placeholders from implemented modules
3. Flag missing tests/doc/runtime entrypoints explicitly
4. Keep reference/resource folders separate from runtime code analysis

### Completion criteria

The team has a verified baseline of what can be reused vs what must be built.
