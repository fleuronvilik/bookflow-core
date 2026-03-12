from __future__ import annotations

from typing import TypedDict

from app.context import Context
from policies.stock_projection import compute_partner_stock


class DeliveryRequestView(TypedDict):
    id: int
    partner_id: str
    status: str
    created_at: str
    items: str


class SalesReportView(TypedDict):
    id: int
    partner_id: str
    voided: bool
    created_at: str
    items: str


class StockItemView(TypedDict):
    book_id: str
    quantity: int


class PartnerCurrentState(TypedDict):
    delivery_requests: list[DeliveryRequestView]
    sales_reports: list[SalesReportView]
    stock: list[StockItemView]


def list_delivery_requests_by_partner(
    ctx: Context, partner_id: str
) -> list[DeliveryRequestView]:
    cur = ctx.dr_repo.conn.cursor()
    rows = cur.execute(
        """
        SELECT
            dr.id,
            dr.partner_id,
            dr.status,
            dr.created_at,
            (
                SELECT GROUP_CONCAT(item_value, ';')
                FROM (
                    SELECT dri.book_sku || '*' || dri.qty AS item_value
                    FROM delivery_request_items AS dri
                    WHERE dri.dr_id = dr.id
                    ORDER BY dri.book_sku
                )
            ) AS items
        FROM delivery_requests AS dr
        WHERE dr.partner_id = ?
        ORDER BY dr.created_at DESC, dr.id DESC
        """,
        (partner_id,),
    ).fetchall()

    return [
        {
            "id": row[0],
            "partner_id": row[1],
            "status": row[2],
            "created_at": row[3],
            "items": row[4] or "",
        }
        for row in rows
    ]


def list_sales_reports_by_partner(
    ctx: Context, partner_id: str
) -> list[SalesReportView]:
    cur = ctx.sr_repo.conn.cursor()
    rows = cur.execute(
        """
        SELECT
            sr.id,
            sr.partner_id,
            sr.is_voided,
            sr.created_at,
            (
                SELECT GROUP_CONCAT(item_value, ';')
                FROM (
                    SELECT sri.book_sku || '*' || sri.qty AS item_value
                    FROM sales_report_items AS sri
                    WHERE sri.sr_id = sr.id
                    ORDER BY sri.book_sku
                )
            ) AS items
        FROM sales_reports AS sr
        WHERE sr.partner_id = ?
        ORDER BY sr.created_at DESC, sr.id DESC
        """,
        (partner_id,),
    ).fetchall()

    return [
        {
            "id": row[0],
            "partner_id": row[1],
            "voided": bool(row[2]),
            "created_at": row[3],
            "items": row[4] or "",
        }
        for row in rows
    ]


def get_partner_current_state(ctx: Context, partner_id: str) -> PartnerCurrentState:
    stock = compute_partner_stock(partner_id, ctx.dr_repo, ctx.sr_repo)
    stock_rows = [
        {"book_id": book_id, "quantity": quantity}
        for book_id, quantity in sorted(stock.items())
    ]
    return {
        "delivery_requests": list_delivery_requests_by_partner(ctx, partner_id),
        "sales_reports": list_sales_reports_by_partner(ctx, partner_id),
        "stock": stock_rows,
    }
