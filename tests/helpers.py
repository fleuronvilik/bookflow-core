from typing import List

from app.use_cases import (
    approve_delivery_request,
    mark_delivered,
    reject_delivery_request,
    submit_delivery_request,
    submit_sales_report,
)
from domain.delivery_request import DeliveryRequest, RequestItem, Status as DRStatus
from domain.sales_report import SalesReport, ReportItem
from policies.identity import Actor, Role


def partner_actor(partner_id: str):
    return Actor(role=Role.PARTNER, partner_id=partner_id)


def admin_actor():
    return Actor(role=Role.ADMIN, partner_id=None)


def default_items() -> List[RequestItem]:
    # respecte MinimumCopies = 2
    return [
        RequestItem(book_id="b1", quantity=2),
        RequestItem(book_id="b2", quantity=3),
    ]


def given_draft_dr(ctx, partner_id: str, items=None) -> int:
    if items is None:
        items = default_items()

    dr = DeliveryRequest.save_draft(partner_id=partner_id, items=items)
    return ctx.dr_repo.create(dr)


def given_dr(ctx, partner_id: str, status: DRStatus, items=None) -> int:
    dr_id = given_draft_dr(ctx, partner_id, items)
    dr = ctx.dr_repo.get(dr_id)

    if status == DRStatus.SUBMITTED:
        _, dr = submit_delivery_request(ctx, partner_actor(partner_id), dr_id)

    elif status == DRStatus.APPROVED:
        _, dr = submit_delivery_request(ctx, partner_actor(partner_id), dr_id)
        _, dr = approve_delivery_request(ctx, admin_actor(), dr_id)

    elif status == DRStatus.REJECTED:
        _, dr = submit_delivery_request(ctx, partner_actor(partner_id), dr_id)
        _, dr = reject_delivery_request(ctx, admin_actor(), dr_id, reason="test reason")

    elif status == DRStatus.DELIVERED:
        _, dr = submit_delivery_request(ctx, partner_actor(partner_id), dr_id)
        _, dr = approve_delivery_request(ctx, admin_actor(), dr_id)
        _, dr = mark_delivered(ctx, admin_actor(), dr_id)

    return dr_id


def given_sr(
    ctx, partner_id: str, items=[ReportItem(book_id="b2", quantity=2)], voided=False
) -> int:
    sr_id, _ = submit_sales_report(ctx, partner_actor(partner_id), items)
    if voided:
        ctx.sr_repo.void(sr_id)
    return sr_id
