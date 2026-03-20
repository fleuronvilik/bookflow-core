from datetime import datetime, timezone
from app.errors import NotFound
from domain.delivery_request import DeliveryRequest, RequestItem, Status as DRStatus


class SqlDeliveryRequestRepo:
    def __init__(self, conn):
        self.conn = conn

    def create(self, dr):
        cur = self.conn.cursor()

        cur.execute(
            """
            INSERT INTO delivery_requests (partner_id, status, created_at)
            VALUES (?, ?, ?)
            """,
            (dr.partner_id, dr.status.value, datetime.now(timezone.utc).isoformat()),
        )

        dr_id = cur.lastrowid
        # dr.id = dr_id

        for item in dr.items:
            book_sku = item.book_id
            qty = item.quantity

            cur.execute(
                """
                INSERT INTO delivery_request_items (dr_id, book_sku, qty)
                VALUES (?, ?, ?)
                """,
                (dr_id, book_sku, qty),
            )

        self.conn.commit()
        return dr_id

    def get(self, dr_id: int) -> DeliveryRequest | None:
        cur = self.conn.cursor()

        row = cur.execute(
            """
            SELECT id, partner_id, status, created_at
            FROM delivery_requests
            WHERE id = ?
            """,
            (dr_id,),
        ).fetchone()

        if row is None:
            return

        items_rows = cur.execute(
            """
            SELECT book_sku, qty
            FROM delivery_request_items
            WHERE dr_id = ?
            """,
            (dr_id,),
        ).fetchall()

        items = [RequestItem(sku, qty) for sku, qty in items_rows]

        return DeliveryRequest(
            # id=row[0],
            partner_id=row[1],
            status=DRStatus(row[2]),
            # created_at=row[3],
            items=items,
        )

    def save_status(
        self, dr_id: int, status: DRStatus, autocommit: bool = True
    ) -> int | None:
        cur = self.conn.cursor()

        # dr = self.get(dr_id)
        # if dr is None:
        #     return None

        cur.execute(
            """
            UPDATE delivery_requests
            SET status = ?
            WHERE id = ?
            """,
            (status, dr_id),
        )

        if autocommit:
            self.conn.commit()
        return dr_id
