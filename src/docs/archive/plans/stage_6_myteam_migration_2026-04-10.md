# .myteam Migration Note (2026-04-10, Stage 6)

## Scope

Re-audit of project-local `.myteam` role/skill instructions for path, command,
and workflow alignment with the current repository state.

## Outdated assumptions found

No stale assumptions requiring `.myteam` content edits were found in this
audit.

Validated areas:

1. Path references still match the repo layout:
   - `src/docs/application_interface.md`
   - `src/docs/plans/`
   - `tests/`
   - `src/frontend/src/`
   - `README.md`
2. Testing commands in `.myteam/testing/skill.md` remain valid:
   - backend: `python -m pytest -q`
   - frontend: `cd src/frontend && npm test` (confirmed by `package.json` script)
3. Delegation-fallback guidance in
   `.myteam/feature-pipeline/conclusion/skill.md` remains actionable when
   role-delegation tooling is unavailable.
4. Optional file references remain conditional (for example `CHANGELOG.md`,
   `src/docs/getting-started.md`), so they do not impose broken hard-path
   requirements.

## Changes made

1. No `.myteam` role/skill file changes were required.
2. Added this Stage 6 migration note to record the completed audit.

## Forward alignment guidance

1. Re-run `.myteam` migration audits whenever test scripts or docs paths change.
2. Keep frontend and backend test command guidance synchronized with actual
   scripts in `src/frontend/package.json` and repo test entrypoints.
3. Preserve fallback instructions for environments without role-delegation
   tooling.
