from domain.delivery_request import DeliveryRequest, RequestItem, Status as DRStatus
from tests.helpers import given_dr


def test_create_and_get_dr(ctx, partner_actor):
    dr = DeliveryRequest.save_draft(
        partner_id=partner_actor.partner_id, items=[RequestItem("b1", 3)]
    )

    dr_id = ctx.dr_repo.create(dr)

    loaded = ctx.dr_repo.get(dr_id)

    assert loaded.items == [RequestItem("b1", 3)]


def test_save(ctx, partner_actor):
    dr_id = given_dr(ctx, partner_actor.partner_id, DRStatus.DRAFT)

    loaded = ctx.dr_repo.get(dr_id)
    assert loaded.status == DRStatus.DRAFT
