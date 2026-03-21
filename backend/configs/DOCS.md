# Backend Configs

Configuration-first runtime behavior for the backend.

## Key Files

- `config.yaml`: central runtime settings for DB, CORS, and dev seed offers
- `config_types.py`: typed config schema and validation
- `config_loader.py`: config path resolution, YAML parsing, schema validation, and env precedence

## Runtime Rules

- Config path resolution:
  - uses `APP_CONFIG_PATH` when set
  - otherwise uses this file (`configs/config.yaml`, repo-root path `backend/configs/config.yaml`)
- Database URL precedence:
  - uses `DATABASE_URL` when set
  - otherwise uses `database.url` from YAML
- Startup behavior:
  - config must exist and validate successfully
  - missing/invalid config fails fast at startup

## Current Config Sections

- `database`: DB connection settings (`url`, `echo`)
- `server.cors`: CORS middleware settings
- `dev.seed_offers`: records inserted by `/dev/seed` when DB is empty
