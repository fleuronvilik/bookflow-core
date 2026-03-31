# from collections import defaultdict
from typing import Dict, List

from domain.sales_report import SalesReport
from infra.sql.sql_partner_inventory_repo import SqlPartnerInventoryRepo


def reports_by_partner(
    reports: List[SalesReport], partner_id: str
) -> List[SalesReport]:
    return [r for r in reports if r.partner_id == partner_id]


def get_partner_inventory(
    partner_id: str, pi_repo: SqlPartnerInventoryRepo
) -> Dict[str, int]:
    rows = (
        pi_repo.conn.cursor()
        .execute(
            """
        SELECT book_sku, current_quantity
        FROM partner_inventories
        WHERE partner_id = ?
        """,
            (partner_id,),
        )
        .fetchall()
    )
    return {sku: qty for sku, qty in rows}
