import pytest
from app.use_cases import create_delivery_request, submit_delivery_request
from domain.delivery_request import DeliveryRequest, RequestItem, Status as DRStatus
from policies.report_required import ReportRequired
from tests.helpers import given_dr, given_sr


def test_submit_dr_allowed_if_no_delivered_dr_exists(ctx, partner_actor):
    rk, _ = create_delivery_request(
        ctx=ctx, actor=partner_actor, payload=[RequestItem(book_id="b1", quantity=2)]
    )
    _, dr = submit_delivery_request(ctx=ctx, actor=partner_actor, dr_id=rk)
    assert dr.status is DRStatus.SUBMITTED


def test_submit_dr_blocked_if_last_delivery_has_no_sr_after(ctx, partner_actor):
    # Last delivered DR for p1 exists
    _ = given_dr(ctx, partner_actor.partner_id, DRStatus.DELIVERED)

    with pytest.raises(ReportRequired):
        rk, _ = create_delivery_request(
            ctx=ctx,
            actor=partner_actor,
            payload=[RequestItem(book_id="b1", quantity=3)],
        )
        submit_delivery_request(ctx=ctx, actor=partner_actor, dr_id=rk)


def test_submit_dr_allowed_if_sr_exists_after_last_delivery(ctx, partner_actor):
    _ = given_dr(ctx, partner_actor.partner_id, DRStatus.DELIVERED)
    _ = given_sr(ctx, partner_actor.partner_id)
    dr_id = given_dr(ctx, partner_actor.partner_id, DRStatus.DRAFT)
    _, dr = submit_delivery_request(
        ctx=ctx,
        actor=partner_actor,
        dr_id=dr_id,
    )

    assert dr.status is DRStatus.SUBMITTED
