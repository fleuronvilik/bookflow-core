# report_required.py
from __future__ import annotations


from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo
from infra.sql.sql_sales_report_repo import SqlSalesReportRepo


class ReportRequired(Exception):
    pass


def ensure_report_submitted_since_last_delivery(
    *,
    partner_id: str,
    dr_repo: SqlDeliveryRequestRepo,
    sr_repo: SqlSalesReportRepo,
) -> None:
    """
    Rule:
      - If no delivered DR exists for partner -> allow
      - Else require at least one SR for partner with seq > last_delivered_seq
    """
    cur = dr_repo.conn.cursor()
    cur.execute(
        """
        SELECT created_at
        FROM delivery_requests
        WHERE partner_id = ?
        AND status = 'DELIVERED'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (partner_id,),
    )
    last_delivered_row = cur.fetchone()
    last_delivered_seq: int | None = None
    if last_delivered_row:
        last_delivered_seq = last_delivered_row[0]

    if last_delivered_seq is None:
        return  # first delivery cycle: no report required

    cur.execute(
        """
        SELECT created_at
        FROM sales_reports
        WHERE partner_id = ?
        AND created_at > ?
        AND is_voided = 0
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (partner_id, last_delivered_seq),
    )
    last_sales_report_row = cur.fetchone()

    if not last_sales_report_row:
        raise ReportRequired(
            "sales report required since last delivered delivery request"
        )
