"""Runtime helpers for config-driven offer schema behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, create_model

from ..utils.config_types import OfferSchemaField, OfferSchemaSection
from ..utils.logging import get_logger

logger = get_logger(__name__)


def get_path(payload: dict[str, Any], path: str) -> Any:
    cursor: Any = payload
    for part in path.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


def set_path(payload: dict[str, Any], path: str, value: Any) -> None:
    cursor = payload
    parts = path.split(".")
    for part in parts[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[parts[-1]] = value


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    return True


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned == "":
            return None
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _coerce_int(value: Any) -> int | None:
    as_float = _coerce_float(value)
    if as_float is None:
        return None
    return int(as_float)


@dataclass(frozen=True)
class ConfiguredOfferSchema:
    raw: OfferSchemaSection
    _parser_model_cache: type[BaseModel] | None = field(
        default=None, init=False, repr=False, compare=False
    )

    @property
    def version(self) -> int:
        return self.raw.version

    @property
    def fields(self) -> list[OfferSchemaField]:
        return self.raw.fields

    @property
    def company_name_path(self) -> str:
        return self.raw.identity.company_name_path

    @property
    def role_title_path(self) -> str:
        return self.raw.identity.role_title_path

    @property
    def field_by_id(self) -> dict[str, OfferSchemaField]:
        return {field.id: field for field in self.raw.fields}

    @property
    def field_by_path(self) -> dict[str, OfferSchemaField]:
        return {field.storage_path: field for field in self.raw.fields}

    @property
    def required_all_paths(self) -> list[str]:
        by_id = self.field_by_id
        return [by_id[field_id].storage_path for field_id in self.raw.required.all_of]

    @property
    def required_one_of_paths(self) -> list[list[str]]:
        by_id = self.field_by_id
        return [[by_id[field_id].storage_path for field_id in group] for group in self.raw.required.one_of]

    @property
    def optional_default_paths(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {}
        required_ids = set(self.raw.required.all_of)
        for group in self.raw.required.one_of:
            required_ids.update(group)
        for field in self.raw.fields:
            if field.id in required_ids:
                continue
            if field.default_when_omitted is None:
                continue
            defaults[field.storage_path] = field.default_when_omitted
        return defaults

    @property
    def monetary_default_paths(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {}
        for field in self.raw.fields:
            if field.group != "monetary":
                continue
            if field.default_when_omitted is None:
                continue
            defaults[field.storage_path] = field.default_when_omitted
        return defaults

    @property
    def non_monetary_default_paths(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {}
        for field in self.raw.fields:
            if field.group != "non_monetary":
                continue
            if field.default_when_omitted is None:
                continue
            defaults[field.storage_path] = field.default_when_omitted
        return defaults

    def apply_migrations(self, payload: dict[str, Any]) -> dict[str, Any]:
        source_version = get_path(payload, "offer_meta.schema_version")
        if not isinstance(source_version, int) or source_version >= self.version:
            return payload

        migrated = dict(payload)
        migration_lookup = {migration.from_version: migration for migration in self.raw.migrations}
        current_version = source_version
        while current_version < self.version:
            migration = migration_lookup.get(current_version)
            if migration is None:
                break
            for rule in migration.rules:
                value = get_path(migrated, rule.from_path)
                if value is None:
                    continue
                set_path(migrated, rule.to_path, value)
            current_version += 1

        set_path(migrated, "offer_meta.schema_version", self.version)
        return migrated

    def normalize_payload(self, payload: dict[str, Any]) -> None:
        for field in self.raw.fields:
            value = get_path(payload, field.storage_path)
            if value is None:
                continue
            if field.data_type == "number":
                parsed = _coerce_float(value)
                if parsed is not None:
                    set_path(payload, field.storage_path, parsed)
            elif field.data_type == "integer":
                parsed = _coerce_int(value)
                if parsed is not None:
                    set_path(payload, field.storage_path, parsed)
            elif field.data_type == "list_string":
                if isinstance(value, list):
                    cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip() != ""]
                    set_path(payload, field.storage_path, cleaned)

        # Preserve existing annualization behavior if configured fields exist.
        annual_path = "compensation.annual_base_salary_usd"
        hourly_path = "compensation.hourly_rate_usd"
        hours_path = "compensation.hours_per_week"
        annual_base = _coerce_float(get_path(payload, annual_path))
        hourly_rate = _coerce_float(get_path(payload, hourly_path))
        hours_per_week = _coerce_float(get_path(payload, hours_path))
        if annual_base is None and hourly_rate is not None and hours_per_week is not None:
            set_path(payload, annual_path, hourly_rate * hours_per_week * 52)

    def missing_required_paths(self, payload: dict[str, Any]) -> list[str]:
        missing: list[str] = []
        for path in self.required_all_paths:
            if not is_present(get_path(payload, path)):
                missing.append(path)

        one_of_groups = self.required_one_of_paths
        if one_of_groups:
            has_satisfied_group = any(
                all(is_present(get_path(payload, path)) for path in group)
                for group in one_of_groups
            )
            if not has_satisfied_group:
                for group in one_of_groups:
                    missing.extend(group)

        # Preserve order and dedupe.
        deduped: list[str] = []
        for path in missing:
            if path not in deduped:
                deduped.append(path)
        return deduped

    def fill_optional_defaults(self, payload: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        for path, default_value in self.optional_default_paths.items():
            if is_present(get_path(payload, path)):
                continue
            set_path(payload, path, default_value)
            warnings.append(f"Stored blank value for omitted field: {path}")
        return warnings

    def apply_group_defaults(self, payload: dict[str, Any], *, group: str) -> list[str]:
        defaults = self.monetary_default_paths if group == "monetary" else self.non_monetary_default_paths
        warnings: list[str] = []
        for path, default_value in defaults.items():
            if is_present(get_path(payload, path)):
                continue
            set_path(payload, path, default_value)
            warnings.append(f"Stored blank value for omitted field: {path}")
        return warnings

    def as_public_payload(self) -> dict[str, Any]:
        return self.raw.model_dump(mode="json")

    def build_parser_model(self) -> type[BaseModel]:
        """Build a strict runtime pydantic model matching configured storage paths."""
        cached = self._parser_model_cache
        if cached is not None:
            return cached
        logger.debug("Building offer schema parser model.")

        type_by_path: dict[str, Any] = {}
        for field in self.raw.fields:
            if field.data_type == "string":
                annotation = str | None
            elif field.data_type == "number":
                annotation = float | None
            elif field.data_type == "integer":
                annotation = int | None
            elif field.data_type == "list_string":
                annotation = list[str] | None
            else:
                annotation = Any
            type_by_path[field.storage_path] = annotation

        tree: dict[str, Any] = {}
        for path, annotation in type_by_path.items():
            cursor = tree
            parts = path.split(".")
            for part in parts[:-1]:
                child = cursor.get(part)
                if not isinstance(child, dict):
                    child = {}
                    cursor[part] = child
                cursor = child
            cursor[parts[-1]] = {"__annotation__": annotation}

        def build_node_model(node_name: str, node_tree: dict[str, Any]) -> type[BaseModel]:
            model_fields: dict[str, tuple[Any, Any]] = {}
            for key, value in node_tree.items():
                if not isinstance(value, dict):
                    continue
                leaf_annotation = value.get("__annotation__")
                nested_keys = [nested_key for nested_key in value.keys() if nested_key != "__annotation__"]
                if leaf_annotation is not None and not nested_keys:
                    model_fields[key] = (leaf_annotation, None)
                    continue
                nested_tree = {k: value[k] for k in nested_keys}
                nested_model = build_node_model(f"{node_name}_{key}", nested_tree)
                model_fields[key] = (nested_model | None, None)

            created = create_model(
                node_name,
                __config__=ConfigDict(extra="forbid"),
                **model_fields,
            )
            return created

        created = build_node_model("ExtractedOfferPayload", tree)
        object.__setattr__(self, "_parser_model_cache", created)
        return created


def build_configured_offer_schema(schema: OfferSchemaSection) -> ConfiguredOfferSchema:
    return ConfiguredOfferSchema(raw=schema)
