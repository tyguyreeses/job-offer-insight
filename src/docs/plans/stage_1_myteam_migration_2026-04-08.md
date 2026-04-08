# .myteam Migration Note (2026-04-08)

## Scope

Audit and migration of project-local `.myteam` instructions to align with
the current repository layout and workflow.

## Outdated assumptions found

1. Multiple `.myteam` files referenced `docs/...` paths, but this repo keeps
   these docs under `src/docs/...`.
2. The project-myteam-update role required migration notes in `docs/plans/`,
   while the actual location is `src/docs/plans/`.
3. Testing skill required `poetry run pytest -q`, but this repository does not
   include Poetry config (`pyproject.toml`) and should use a tool-agnostic
   pytest invocation.
4. Conclusion skill assumed `pyproject.toml`, `CHANGELOG.md`, and
   `docs/getting-started.md` always exist.

## Changes made

1. Updated `.myteam/feature-pipeline/project-myteam-update/role.md`:
   - `docs/plans/` -> `src/docs/plans/`
2. Updated `.myteam/feature-pipeline/skill.md`:
   - `docs/application_interface.md` -> `src/docs/application_interface.md`
   - `docs/plans/<branch_name>.md` -> `src/docs/plans/<branch_name>.md`
3. Updated `.myteam/testing/skill.md`:
   - `docs/application_interface.md` -> `src/docs/application_interface.md`
   - standardized test command to `python -m pytest -q`
4. Updated `.myteam/feature-pipeline/conclusion/skill.md`:
   - made version-bump guidance conditional on package-versioning usage
   - made changelog update conditional on `CHANGELOG.md` existing
   - `docs/application_interface.md` -> `src/docs/application_interface.md`
   - made `docs/getting-started.md` update conditional on file existing

## Forward alignment guidance

1. Keep all `.myteam` doc references aligned with `src/docs/...` unless the
   repository structure changes.
2. Treat optional project artifacts (version files, changelog, setup docs) as
   conditional steps in instructions unless they are guaranteed to exist.
3. Prefer environment-agnostic commands in shared instructions unless the
   repository explicitly standardizes on a tool (for example, Poetry).
