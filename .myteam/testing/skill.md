---
name: Testing
description: |
  This skill describes the testing philosophy and commands for this repo.
  Load this skill when you add, remove, or modify tests.
---

## Testing

### Philosophy

- tests should focus on externally observable behavior from the documented interface
- assertions should prove outcomes users/admins/operators can observe (messages, files, command results)
- avoid coupling tests to internal helper implementation details unless unavoidable
- new or changed behavior should trace back to `src/docs/application_interface.md`
- tests should be clear evidence that the documented contract is satisfied

### Process

Choose commands based on the area you changed:

```
python -m pytest -q
```

Run frontend tests when frontend behavior/tests changed:

```
cd src/frontend && npm test
```

If a change spans backend and frontend behavior, run both commands before
concluding the feature.

Backend tests are in `tests/`.
Frontend tests are in `src/frontend/src/`.
