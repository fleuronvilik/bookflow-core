from typing import List
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
    return ctx.dr_repo.add(dr)


def given_dr(ctx, partner_id: str, status: DRStatus, items=None) -> int:
    dr_id = given_draft_dr(ctx, partner_id, items)
    dr = ctx.dr_repo.get(dr_id)

    if status == DRStatus.SUBMITTED:
        dr.submit()

    elif status == DRStatus.APPROVED:
        dr.submit()
        dr.approve()

    elif status == DRStatus.REJECTED:
        dr.submit()
        dr.reject()

    elif status == DRStatus.DELIVERED:
        dr.submit()
        dr.approve()
        dr.mark_delivered()

    return dr_id


def given_sr(
    ctx, partner_id: str, items=[ReportItem(book_id="b2", quantity=2)], voided=False
) -> int:
    sr = SalesReport(partner_id=partner_id, items=items, voided=voided)
    return ctx.sr_repo.add(sr)
