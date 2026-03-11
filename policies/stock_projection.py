from typing import Dict

from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo
from infra.sql.sql_sales_report_repo import SqlSalesReportRepo


def compute_partner_stock(
    partner_id: str,
    dr_repo: SqlDeliveryRequestRepo,
    sr_repo: SqlSalesReportRepo,
) -> Dict[str, int]:
    cur = dr_repo.conn.cursor()

    delivered_rows = cur.execute(
        """
        SELECT it.book_sku, SUM(it.qty)
        FROM delivery_requests AS dr
        JOIN delivery_request_items AS it ON dr.id = it.dr_id
        WHERE dr.partner_id = ?
          AND dr.status = 'DELIVERED'
        GROUP BY it.book_sku
        """,
        (partner_id,),
    ).fetchall()

    sold_rows = cur.execute(
        """
        SELECT it.book_sku, SUM(it.qty)
        FROM sales_reports AS sr
        JOIN sales_report_items AS it ON sr.id = it.sr_id
        WHERE sr.partner_id = ?
        AND sr.is_voided = 0
        GROUP BY it.book_sku
        """,
        (partner_id,),
    ).fetchall()

    delivered = {sku: qty for sku, qty in delivered_rows}
    sold = {sku: qty for sku, qty in sold_rows}

    all_books = set(delivered) | set(sold)

    return {sku: delivered.get(sku, 0) - sold.get(sku, 0) for sku in all_books}
