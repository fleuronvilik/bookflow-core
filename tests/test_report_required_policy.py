import pytest
from domain.delivery_request import DeliveryRequest, RequestItem, Status as DRStatus
from domain.sales_report import SalesReport, ReportItem
from app import use_cases as uc
from policies.report_required import ReportRequired


def test_submit_dr_allowed_if_no_delivered_dr_exists(ctx, partner_actor):
    rk, _ = uc.create_delivery_request(
        ctx=ctx, actor=partner_actor, payload=[RequestItem(book_id="b1", quantity=2)]
    )
    _, dr = uc.submit_delivery_request(ctx=ctx, actor=partner_actor, dr_id=rk)
    assert dr.status is DRStatus.SUBMITTED


def test_submit_dr_blocked_if_last_delivery_has_no_sr_after(ctx, partner_actor):
    # Last delivered DR for p1 exists
    ctx.dr_repo.create(
        DeliveryRequest(
            partner_id="p1",
            status=DRStatus.DELIVERED,
            items=[RequestItem(book_id="b1", quantity=2)],
        )
    )

    with pytest.raises(ReportRequired):
        rk, _ = uc.create_delivery_request(
            ctx=ctx,
            actor=partner_actor,
            payload=[RequestItem(book_id="b1", quantity=3)],
        )
        uc.submit_delivery_request(ctx=ctx, actor=partner_actor, dr_id=rk)


def test_submit_dr_allowed_if_sr_exists_after_last_delivery(ctx, partner_actor):
    items = [RequestItem(book_id="b1", quantity=2)]
    ctx.dr_repo.create(
        DeliveryRequest(partner_id="p1", status=DRStatus.DELIVERED, items=items)
    )

    # SR submitted after delivery (order is shared)
    ctx.sr_repo.create(
        SalesReport(partner_id="p1", items=[ReportItem(book_id="b1", quantity=2)])
    )

    rk, _ = uc.create_delivery_request(
        ctx=ctx, actor=partner_actor, payload=[RequestItem(book_id="b2", quantity=4)]
    )
    _, dr = uc.submit_delivery_request(
        ctx=ctx,
        actor=partner_actor,
        dr_id=rk,
    )

    assert dr.status is DRStatus.SUBMITTED
