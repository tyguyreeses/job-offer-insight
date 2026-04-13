# .myteam Migration Note (2026-04-10, Stage 5.2)

## Scope

Re-audit of project-local `.myteam` role/skill content against the current
repository structure and workflow.

## Outdated assumptions found

No stale assumptions requiring `.myteam` edits were found in this audit.

Validated areas:

1. Referenced core paths remain present:
   - `src/docs/application_interface.md`
   - `src/docs/plans/`
   - `tests/`
   - `README.md`
2. Testing guidance in `.myteam/testing/skill.md` remains aligned to repo usage
   (`python -m pytest -q` from repository root).
3. Delegation fallback guidance in
   `.myteam/feature-pipeline/conclusion/skill.md` remains valid when
   role-delegation tooling is unavailable.
4. Optional-file references (for example `CHANGELOG.md`,
   `src/docs/getting-started.md`) are conditionally phrased and do not create
   hard path assumptions.

## Changes made

1. No `.myteam` role/skill file content changes were required.
2. Updated this migration note to record the completed re-audit.
3. Confirmed current environment does not expose `spawn-agent`; direct audit
   execution was used for this task.

## Forward alignment guidance

1. Re-run `.myteam` migration audit when directory layout changes under `src/`
   or `tests/`.
2. Update `.myteam/testing/skill.md` immediately if the project standard test
   command changes.
3. Keep optional docs references conditional unless those docs become required.
4. Continue including delegation-tooling fallback guidance in `.myteam`
   conclusion/update flows.
