# .myteam Migration Note (2026-04-08, Stage 2)

## Scope

Audit and migration of project-local `.myteam` instructions to keep role/skill
guidance aligned with this repository's current structure and available tools.

## Outdated assumptions found

1. `.myteam/feature-pipeline/conclusion/skill.md` required delegation to
   `code-linter` and `project-myteam-update` roles without fallback guidance
   when role delegation tooling is unavailable.
2. `.myteam/feature-pipeline/conclusion/skill.md` referenced
   `docs/getting-started.md`, while repository docs are under `src/docs/`.

## Changes made

1. Updated `.myteam/feature-pipeline/conclusion/skill.md` to include explicit
   fallback instructions for environments where `spawn-agent` (or equivalent
   delegation tooling) is unavailable.
2. Updated `.myteam/feature-pipeline/conclusion/skill.md` documentation path:
   - `docs/getting-started.md` -> `src/docs/getting-started.md` (conditional on
     file existence).

## Forward alignment guidance

1. For any role-to-role delegation step, include a direct-execution fallback so
   instructions remain actionable across tool-limited environments.
2. Keep documentation paths rooted at `src/docs/` unless the repository
   structure explicitly changes.
