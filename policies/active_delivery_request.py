from __future__ import annotations

from app.repositories import InMemoryDeliveryRequestRepo
from domain.delivery_request import Status


class ActiveDeliveryRequestExists(Exception):
    pass


ACTIVE_STATUSES = {Status.SUBMITTED, Status.APPROVED}


def ensure_no_active_delivery_request_for_partner(
    *, partner_id: str, dr_repo: InMemoryDeliveryRequestRepo
) -> None:
    for dr in dr_repo.list_all():
        if dr.partner_id == partner_id and dr.status in ACTIVE_STATUSES:
            print(dr)
            raise ActiveDeliveryRequestExists(
                f"active delivery request already exists for partner {partner_id}"
            )
