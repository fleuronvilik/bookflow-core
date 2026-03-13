from datetime import datetime, timezone
from domain.sales_report import SalesReport, ReportItem


class SqlSalesReportRepo:
    def __init__(self, conn):
        self.conn = conn

    def create(self, report: SalesReport) -> int:
        cur = self.conn.cursor()
        is_voided = 1 if report.voided else 0

        cur.execute(
            """
            INSERT INTO sales_reports (partner_id, created_at, is_voided)
            VALUES (?, ?, ?)
            """,
            (report.partner_id, datetime.now(timezone.utc).isoformat(), is_voided),
        )

        report_id = cur.lastrowid

        for item in report.items:
            cur.execute(
                """
                INSERT INTO sales_report_items (sr_id, book_sku, qty)
                VALUES (?, ?, ?)
                """,
                (report_id, item.book_id, item.quantity),
            )

        self.conn.commit()
        return report_id

    def get(self, report_id: int) -> SalesReport | None:
        cur = self.conn.cursor()

        row = cur.execute(
            """
            SELECT id, partner_id, is_voided, created_at
            FROM sales_reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

        if row is None:
            return None

        items_rows = cur.execute(
            """
            SELECT book_sku, qty
            FROM sales_report_items
            WHERE sr_id = ?
            """,
            (report_id,),
        ).fetchall()

        items = [ReportItem(book_id=r[0], quantity=r[1]) for r in items_rows]

        return SalesReport(
            partner_id=row[1],
            voided=bool(row[2]),
            items=items,
        )

    def mark_void(self, report_id: int) -> int | None:
        cur = self.conn.cursor()

        cur.execute(
            """
            UPDATE sales_reports
            SET is_voided = 1
            WHERE id = ?
            """,
            (report_id,),
        )

        self.conn.commit()
        return report_id
