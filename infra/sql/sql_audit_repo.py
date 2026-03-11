from __future__ import annotations

from datetime import datetime, timezone

from app.errors import NotFound


class SqlAuditRepo:
    def __init__(self, conn):
        self.conn = conn

    def record(self, event: dict) -> int:
        event_type = event["type"]
        reason = event.get("reason")

        target_type = event.get("target_type")
        target_id = event.get("target_id")

        if target_type is None or target_id is None:
            if "dr_id" in event:
                target_type = "delivery_request"
                target_id = event["dr_id"]
            elif "sr_id" in event:
                target_type = "sales_report"
                target_id = event["sr_id"]
            else:
                raise ValueError(
                    "audit event must include target_id/target_type or dr_id/sr_id"
                )

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_events (type, target_type, target_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event_type,
                target_type,
                target_id,
                reason,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def get(self, event_id: int) -> dict | None:
        cur = self.conn.cursor()
        row = cur.execute(
            """
            SELECT id, type, target_type, target_id, reason, created_at
            FROM audit_events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

        if row is None:
            return

        return {
            "id": row[0],
            "type": row[1],
            "target_type": row[2],
            "target_id": row[3],
            "reason": row[4],
            "created_at": row[5],
        }

    def list_all(self) -> list[dict]:
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT id, type, target_type, target_id, reason, created_at
            FROM audit_events
            ORDER BY created_at, id
            """
        ).fetchall()

        return [
            {
                "id": row[0],
                "type": row[1],
                "target_type": row[2],
                "target_id": row[3],
                "reason": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]
