# .myteam Migration Note (2026-04-08, Stage 3)

## Scope

Audit of project-local `.myteam` roles/skills and loader content to verify
alignment with current repository paths, branch workflow, and test execution.

## Outdated assumptions found

No stale assumptions were found in this audit. Specifically:

1. Referenced documentation paths remain valid under `src/docs/...`.
2. The testing command in `.myteam/testing/skill.md` is still valid for this
   repository (`python -m pytest -q`), verified by successful local execution.
3. Delegation-related guidance in `.myteam/feature-pipeline/conclusion/skill.md`
   still includes direct-execution fallback when delegation tooling is absent.

## Changes made

1. No `.myteam` role/skill files required migration edits in Stage 3.
2. Added this migration note to record verification status and prevent
   redundant migration churn.

## Forward alignment guidance

1. Re-run `.myteam` migration audit whenever docs are relocated, test commands
   change, or role delegation tooling availability changes.
2. Keep test-command guidance tool-agnostic unless the repository formally
   standardizes on a dependency manager command wrapper.
