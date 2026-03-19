from typing import Iterable, List, Set
from domain.delivery_request import (
    RequestItem,
    InvalidDeliveryRequest,
)
from domain.sales_report import SalesReport
from domain.errors import InvalidReport


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
