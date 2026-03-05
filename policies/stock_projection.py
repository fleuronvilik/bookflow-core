from typing import Dict
from domain.delivery_request import (
    Status as DRStatus,
)
from app.repositories import InMemoryDeliveryRequestRepo, InMemorySalesReportRepo


def compute_partner_stock(
    partner_id: str,
    dr_repo: InMemoryDeliveryRequestRepo,
    sr_repo: InMemorySalesReportRepo,
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
        if sr.partner_id != partner_id or sr.voided:
            continue
        for it in sr.items:
            outbound_existing[it.book_id] = (
                outbound_existing.get(it.book_id, 0) + it.quantity
            )

    stock: Dict[str, int] = {}
    for book_id in inbound:
        print(book_id)
        stock[book_id] = inbound.get(book_id, 0) - outbound_existing.get(book_id, 0)
    return stock
