"""SQLite offer repository implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import uuid4

from ...domain.models import OfferRecord
from ..db import SQLiteDatabase


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _payload_to_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)


def _json_to_payload(payload_json: str) -> dict[str, Any]:
    decoded = json.loads(payload_json)
    if not isinstance(decoded, dict):
        raise ValueError("Offer payload must be a JSON object.")
    return decoded


@dataclass(frozen=True)
class SQLiteOfferRepository:
    database: SQLiteDatabase

    def create(
        self,
        *,
        company_name: str,
        role_title: str,
        payload: Mapping[str, Any],
        offer_id: str | None = None,
    ) -> OfferRecord:
        self.database.initialize()
        record_id = offer_id or str(uuid4())
        now = _utc_now_iso()
        payload_json = _payload_to_json(payload)

        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO offers (
                    id,
                    company_name,
                    role_title,
                    payload_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (record_id, company_name, role_title, payload_json, now, now),
            )

        return OfferRecord(
            id=record_id,
            company_name=company_name,
            role_title=role_title,
            payload=_json_to_payload(payload_json),
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, offer_id: str) -> OfferRecord | None:
        self.database.initialize()
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT id, company_name, role_title, payload_json, created_at, updated_at
                FROM offers
                WHERE id = ?
                """,
                (offer_id,),
            ).fetchone()
        if row is None:
            return None
        return OfferRecord(
            id=row["id"],
            company_name=row["company_name"],
            role_title=row["role_title"],
            payload=_json_to_payload(row["payload_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_all(self) -> list[OfferRecord]:
        self.database.initialize()
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, company_name, role_title, payload_json, created_at, updated_at
                FROM offers
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            OfferRecord(
                id=row["id"],
                company_name=row["company_name"],
                role_title=row["role_title"],
                payload=_json_to_payload(row["payload_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update(
        self,
        *,
        offer_id: str,
        payload: Mapping[str, Any],
        company_name: str | None = None,
        role_title: str | None = None,
    ) -> OfferRecord | None:
        self.database.initialize()
        existing = self.get_by_id(offer_id)
        if existing is None:
            return None

        resolved_company_name = company_name or str(payload.get("company_name") or existing.company_name)
        resolved_role_title = role_title or str(payload.get("role_title") or existing.role_title)
        now = _utc_now_iso()
        payload_json = _payload_to_json(payload)

        with self.database.connection() as conn:
            conn.execute(
                """
                UPDATE offers
                SET company_name = ?, role_title = ?, payload_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    resolved_company_name,
                    resolved_role_title,
                    payload_json,
                    now,
                    offer_id,
                ),
            )

        return OfferRecord(
            id=offer_id,
            company_name=resolved_company_name,
            role_title=resolved_role_title,
            payload=_json_to_payload(payload_json),
            created_at=existing.created_at,
            updated_at=now,
        )

    def delete(self, offer_id: str) -> bool:
        self.database.initialize()
        with self.database.connection() as conn:
            result = conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        return result.rowcount > 0

    def ping(self) -> bool:
        try:
            self.database.initialize()
            with self.database.connection() as conn:
                conn.execute("SELECT 1").fetchone()
        except Exception:
            return False
        return True
