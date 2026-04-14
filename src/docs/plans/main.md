# Plan: Improve Parse Entry Prompt And Token Budget

## 1. Framework refactor (feature-neutral prep work)

- No framework refactors required.

## 2. Feature addition (behavior implementation)

- Expand `src/backend/prompts/extract_offer.md` with an explicit JSON schema key list and nesting rules.
- Increase `agents.parse_entry.max_output_tokens` in `src/config.yaml` to reduce JSON truncation for large inputs.
- Keep structured-output parsing behavior and validation intact.
