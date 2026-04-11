# .myteam Migration Note (2026-04-11, Stage 7)

## Scope

Audit of project-local `.myteam` role/skill instructions for path, command,
and workflow alignment after Stage 7 completion work.

## Outdated assumptions found

No stale assumptions requiring `.myteam` instruction edits were found.

Validated checks:

1. Referenced core paths still exist and match current structure:
   - `src/docs/application_interface.md`
   - `src/docs/plans/`
   - `tests/`
   - `src/frontend/src/`
   - `README.md`
2. Testing commands documented in `.myteam/testing/skill.md` remain valid:
   - `python -m pytest -q`
   - `cd src/frontend && npm test` (matches `src/frontend/package.json`)
3. Feature pipeline conclusion fallback is still correct in this environment:
   `spawn-agent` is unavailable, so direct-review fallback remains necessary and
   appropriate.

## Changes made

1. No `.myteam` role or skill files required updates in this migration pass.
2. Added this migration note to document the audit outcome.

## Forward alignment guidance

1. Re-run this migration audit when repo paths, test commands, or docs entry
   points change.
2. Keep `.myteam/testing/skill.md` synchronized with backend/frontend test
   entrypoints.
3. Keep delegation fallbacks in `.myteam` instructions for environments without
   role-delegation tooling.
