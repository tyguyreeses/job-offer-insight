# .myteam Migration Note (2026-04-10, Stage 5.3)

## Scope

Audit of project-local `.myteam` instructions to keep role/skill guidance aligned
with the current repository workflow.

## Outdated assumptions found

1. `.myteam/testing/skill.md` treated test execution as backend-only (`python -m pytest -q`).
2. Repository workflow now includes frontend tests in `src/frontend` (`npm test`), so the testing skill was incomplete for full-scope feature work.
3. `.myteam/feature-pipeline/conclusion/skill.md` used package-versioning examples focused on `pyproject.toml` and did not mention the repository's frontend package file.

## Changes made

1. Updated `.myteam/testing/skill.md` process guidance to:
   - retain backend test command (`python -m pytest -q`),
   - add frontend test command (`cd src/frontend && npm test`) when frontend behavior/tests change,
   - require running both when a feature spans backend and frontend behavior,
   - explicitly map backend/frontend test locations.
2. Updated `.myteam/feature-pipeline/conclusion/skill.md` version-bump example to include `src/frontend/package.json` alongside `pyproject.toml`.

## Forward alignment guidance

1. Keep `.myteam/testing/skill.md` synchronized with both backend and frontend test entrypoints whenever scripts change.
2. When new package/version owners are introduced (backend or frontend), update the conclusion skill examples immediately.
3. Continue making optional-file references conditional (for example changelog or setup docs) unless those files become required by policy.
