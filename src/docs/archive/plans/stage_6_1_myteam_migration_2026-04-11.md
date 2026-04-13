# .myteam Migration Note (2026-04-11, Stage 6.1)

## Scope

Re-audit of project-local `.myteam` role/skill instructions for path, command,
and workflow alignment with the current repository state.

## Outdated assumptions found

No stale assumptions requiring `.myteam` content edits were found in this
audit.

Validated areas:

1. Hard-path references still match the repo layout:
   - `src/docs/application_interface.md`
   - `src/docs/plans/`
   - `tests/`
   - `src/frontend/src/`
   - `README.md`
2. Testing commands in `.myteam/testing/skill.md` remain valid:
   - backend: `python -m pytest -q`
   - frontend: `cd src/frontend && npm test` (confirmed by
     `src/frontend/package.json` script)
3. `.myteam/feature-pipeline/conclusion/skill.md` fallback guidance remains
   aligned for environments where role-delegation tooling is unavailable.
4. Optional-file references remain conditional (for example `CHANGELOG.md`,
   `src/docs/getting-started.md`, `pyproject.toml`) and do not impose broken
   required paths.

## Changes made

1. No `.myteam` role/skill file changes were required.
2. Added this Stage 6.1 migration note to record the completed audit.

## Forward alignment guidance

1. Re-run `.myteam` migration audits whenever repo docs paths or frontend test
   scripts change.
2. Keep `.myteam/testing/skill.md` commands synchronized with
   `src/frontend/package.json` and backend test entrypoints.
3. Preserve direct-run fallback instructions in `.myteam` content for
   environments without role-delegation tooling.
