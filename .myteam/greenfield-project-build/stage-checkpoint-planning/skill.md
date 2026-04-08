---
name: Stage Checkpoint Planning
description: |
  Splits implementation into STAGE_x checkpoint documents with strict entry
  criteria, checklists, test gates, exit criteria, and feedback sections.
---

## Stage Checkpoint Planning

Create reviewable, branch-friendly implementation checkpoints.

### Stage doc template requirements

Each `STAGE_x.md` must include:

1. Metadata (`Status`, `Completed`, dates, branch, dependencies)
2. Goal
3. Scope
4. Out of Scope
5. Entry Criteria
6. Implementation Checklist
7. Deliverables
8. Test Gate
9. Exit Criteria
10. Feedback and Revisions (empty user-edit section)

### Rules

1. Keep stages dependency-ordered
2. Avoid mixing too many unrelated risks in one stage
3. Ensure each stage can be reviewed independently
4. Include explicit user approval gate before next stage

### Completion criteria

Stages form a complete end-to-end path with no missing critical checkpoint.
