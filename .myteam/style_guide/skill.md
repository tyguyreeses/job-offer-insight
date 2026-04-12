---
name: Style Guide
description: |
  Reusable-first frontend style guidance. Use this skill when adding or changing frontend styles.
---

## Goal

Keep styling high-quality, give the user a cohesive experience, and minimize duplication.

### Core rules

1. Reuse before creating:
   inspect the project for existing tokens, shared classes, and repeated patterns
   before adding new styles.
2. Keep styles generic first:
   define non-object-specific reusable styles, then layer local overrides only when
   needed.
3. Use a shared global stylesheet for reusable style primitives:
   tokens, utilities, common card/button/state patterns belong in global shared CSS.
4. Keep object/page/component-specific styles in separate local files.
5. Minimize duplicated code:
   do not copy similar style blocks across files unless there is a documented,
   intentional difference.
6. Define color values exactly once as shared tokens:
   every color (including alpha variants used in gradients, borders, shadows, and overlays)
   must be declared in the shared token file and referenced via `var(...)`.
   Do not introduce raw hex/rgb/rgba/hsl literals in component or page styles.

### Routine duplication check

For every style change, do a quick pass to find duplicate or near-duplicate rules.
Consolidate repeated values and patterns into shared reusable styles.

### Cohesion rule

Tell future agents to look for existing project patterns and reuse them to keep
the UI consistent across pages.

### Override rule

Follow these defaults unless the user explicitly asks for a different style
direction.
