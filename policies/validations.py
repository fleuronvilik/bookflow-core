from typing import Iterable, List, Set, Dict
from domain.delivery_request import RequestItem, InvalidDeliveryRequest, Status as DRStatus
from domain.sales_report import SalesReport
from domain.errors import InvalidReport
from app.repositories import InMemoryDeliveryRequestRepo, InMemorySalesReportRepo

def validate_report_items_in_catalog(report:SalesReport, catalog: Iterable[str]):
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
    dr_repo: InMemoryDeliveryRequestRepo,
    sr_repo: InMemorySalesReportRepo,
) -> None:
    """
    Stock entrant (par book_id) = somme des DR DELIVERED pour ce partner.
    Stock sortant = somme des SR déjà soumis (persistés) pour ce partner.
    Règle: sortant_existant + sortant_nouveau <= entrant, pour chaque book_id du report.
    """
    stock = compute_partner_stock(report.partner_id, dr_repo, sr_repo)
    violations = []
    for it in report.items:
        available = stock[it.book_id]
        if it.quantity > available:
            violations.append(f"{it.book_id} (asked {it.quantity}, available {available})")

    if violations:
        raise InvalidReport("Insufficient stock for: " + ", ".join(violations))

def compute_partner_stock(
      partner_id: str,
      dr_repo: InMemoryDeliveryRequestRepo,
      sr_repo: InMemorySalesReportRepo
) -> Dict[str, int]:
    inbound: Dict[str, int] = {}
    for dr in dr_repo.list_all():
        if dr.partner_id != partner_id:
            continue
        if dr.status is not DRStatus.DELIVERED:
            continue
        for it in dr.items:
            inbound[it.book_id] = inbound.get(it.book_id, 0) + it.quantity

    outbound_existing: Dict[str, int] = {}
    for sr in sr_repo.list_all():
        if sr.partner_id != partner_id:
            continue
        for it in sr.items:
            outbound_existing[it.book_id] = outbound_existing.get(it.book_id, 0) + it.quantity

    stock: Dict[str, int] = {}
    for book_id in inbound:
        print(book_id)
        stock[book_id] = inbound.get(book_id, 0) - outbound_existing.get(book_id, 0)
    return stock

    