from typing import Iterable, List, Set
from domain.delivery_request import (
    RequestItem,
    InvalidDeliveryRequest,
)
from domain.sales_report import SalesReport
from domain.errors import InvalidReport
from app.repositories import InMemoryDeliveryRequestRepo, InMemorySalesReportRepo
from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo
from infra.sql.sql_sales_report_repo import SqlSalesReportRepo
from .stock_projection import compute_partner_stock


class InsufficientStock(Exception):
    pass


def validate_report_items_in_catalog(report: SalesReport, catalog: Iterable[str]):
    invalid_ids = set()
    for it in report.items:
        if it.book_id not in catalog:
            invalid_ids.add(it.book_id)
    if invalid_ids:
        raise InvalidReport(f"Unknown book_id(s): {', '.join(invalid_ids)}")


def validate_request_items_in_catalog(
    items: List[RequestItem],
    catalog: Iterable[str],
) -> None:
    catalog_set: Set[str] = set(catalog)
    unknown = [it.book_id for it in items if it.book_id not in catalog_set]
    if unknown:
        raise InvalidDeliveryRequest(f"Unknown book_id(s): {', '.join(unknown)}")


def validate_sales_report_against_stock(
    *,
    report: SalesReport,
    dr_repo: SqlDeliveryRequestRepo,
    sr_repo: SqlSalesReportRepo,
) -> None:
    """
    Stock entrant (par book_id) = somme des DR DELIVERED pour ce partner.
    Stock sortant = somme des SR déjà soumis (persistés) pour ce partner.
    Règle: sortant_existant + sortant_nouveau <= entrant, pour chaque book_id du report.
    """
    stock = compute_partner_stock(report.partner_id, dr_repo=dr_repo, sr_repo=sr_repo)
    violations = []
    for it in report.items:
        available = stock.get(it.book_id, 0)
        if it.quantity > available:
            violations.append(
                f"{it.book_id} (reported {it.quantity}, available {available})"
            )

    if violations:
        raise InsufficientStock("Insufficient stock for: " + ", ".join(violations))
