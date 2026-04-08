"""SQLite comparison repository implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Sequence
from uuid import uuid4

from ...domain.models import ComparisonRecord
from ..db import SQLiteDatabase


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _ids_to_json(selected_offer_ids: Sequence[str]) -> str:
    if not selected_offer_ids:
        raise ValueError("selected_offer_ids must include at least one offer id.")
    return json.dumps(list(selected_offer_ids), separators=(",", ":"), sort_keys=False)


def _json_to_ids(selected_offer_ids_json: str) -> list[str]:
    decoded = json.loads(selected_offer_ids_json)
    if not isinstance(decoded, list):
        raise ValueError("selected_offer_ids must decode to a list.")
    return [str(item) for item in decoded]


@dataclass(frozen=True)
class SQLiteComparisonRepository:
    database: SQLiteDatabase

    def create(
        self,
        *,
        selected_offer_ids: Sequence[str],
        summary_text: str,
        note: str | None = None,
        comparison_id: str | None = None,
    ) -> ComparisonRecord:
        self.database.initialize()
        record_id = comparison_id or str(uuid4())
        now = _utc_now_iso()
        selected_offer_ids_json = _ids_to_json(selected_offer_ids)

        with self.database.connection() as conn:
            conn.execute(
                """
                INSERT INTO comparisons (
                    id,
                    selected_offer_ids_json,
                    summary_text,
                    note,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (record_id, selected_offer_ids_json, summary_text, note, now, now),
            )

        return ComparisonRecord(
            id=record_id,
            selected_offer_ids=_json_to_ids(selected_offer_ids_json),
            summary_text=summary_text,
            note=note,
            created_at=now,
            updated_at=now,
        )

    def get_by_id(self, comparison_id: str) -> ComparisonRecord | None:
        self.database.initialize()
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT id, selected_offer_ids_json, summary_text, note, created_at, updated_at
                FROM comparisons
                WHERE id = ?
                """,
                (comparison_id,),
            ).fetchone()
        if row is None:
            return None
        return ComparisonRecord(
            id=row["id"],
            selected_offer_ids=_json_to_ids(row["selected_offer_ids_json"]),
            summary_text=row["summary_text"],
            note=row["note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_all(self) -> list[ComparisonRecord]:
        self.database.initialize()
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, selected_offer_ids_json, summary_text, note, created_at, updated_at
                FROM comparisons
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            ComparisonRecord(
                id=row["id"],
                selected_offer_ids=_json_to_ids(row["selected_offer_ids_json"]),
                summary_text=row["summary_text"],
                note=row["note"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update(
        self,
        *,
        comparison_id: str,
        selected_offer_ids: Sequence[str] | None = None,
        summary_text: str | None = None,
        note: str | None = None,
    ) -> ComparisonRecord | None:
        self.database.initialize()
        existing = self.get_by_id(comparison_id)
        if existing is None:
            return None

        resolved_selected_offer_ids = list(selected_offer_ids or existing.selected_offer_ids)
        resolved_summary_text = summary_text if summary_text is not None else existing.summary_text
        resolved_note = note if note is not None else existing.note
        now = _utc_now_iso()
        selected_offer_ids_json = _ids_to_json(resolved_selected_offer_ids)

        with self.database.connection() as conn:
            conn.execute(
                """
                UPDATE comparisons
                SET selected_offer_ids_json = ?, summary_text = ?, note = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    selected_offer_ids_json,
                    resolved_summary_text,
                    resolved_note,
                    now,
                    comparison_id,
                ),
            )

        return ComparisonRecord(
            id=comparison_id,
            selected_offer_ids=resolved_selected_offer_ids,
            summary_text=resolved_summary_text,
            note=resolved_note,
            created_at=existing.created_at,
            updated_at=now,
        )

    def delete(self, comparison_id: str) -> bool:
        self.database.initialize()
        with self.database.connection() as conn:
            result = conn.execute("DELETE FROM comparisons WHERE id = ?", (comparison_id,))
        return result.rowcount > 0

    def ping(self) -> bool:
        try:
            self.database.initialize()
            with self.database.connection() as conn:
                conn.execute("SELECT 1").fetchone()
        except Exception:
            return False
        return True
