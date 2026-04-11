---
name: Animation Style Guide
description: |
  Use this skill when adding or changing UI animation/motion behavior.
---

## Animation Style Guide

Reusable-first motion guidance for cohesive UI animations with minimal duplication 
and consistent visibility transitions.

### Core rules

1. Reuse before creating:
   inspect existing keyframes, timing/easing tokens, and transition patterns in the
   project before adding new animation code.
2. Define reusable motion primitives first:
   keep animation patterns non-object-specific so they can be reused across
   components.
3. Nothing should appear or disappear abruptly:
   all show/hide behavior must use an enter/exit animation or transition.
   The exact effect can vary, but it must match established project patterns.
4. Keep shared motion in global reusable CSS; keep component-specific motion in
   local style files.
5. Minimize duplicate motion code:
   consolidate near-identical keyframes, timings, and transitions.

### Routine duplication check

For every motion change, scan for duplicate animation logic and merge into shared
reusable primitives whenever possible.

### Cohesion rule

Tell future agents to look for motion patterns already used in the project and
reuse them across features to maintain a cohesive user experience.

### Override rule

Follow these defaults unless the user explicitly asks for a different animation
direction.
