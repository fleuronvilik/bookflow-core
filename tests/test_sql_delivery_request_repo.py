import pytest
from domain.delivery_request import DeliveryRequest, RequestItem


def test_create_and_get_dr(ctx):
    dr = DeliveryRequest.save_draft(partner_id="luigi", items=[RequestItem("b1", 3)])

    dr_id = ctx.dr_repo.create(dr)

    loaded = ctx.dr_repo.get(dr_id)

    assert loaded.items == [RequestItem("b1", 3)]


def test_save_status(ctx):
    dr = DeliveryRequest.save_draft(partner_id="luigi", items=[RequestItem("b1", 3)])

    dr_id = ctx.dr_repo.create(dr)

    loaded = ctx.dr_repo.get(dr_id)
    loaded.submit()
    ctx.dr_repo.save_status(dr_id, loaded.status)

    loaded = ctx.dr_repo.get(dr_id)
    assert loaded.status == "SUBMITTED"

    loaded = ctx.dr_repo.get(dr_id)
    loaded.approve()
    ctx.dr_repo.save_status(dr_id, loaded.status)

    loaded = ctx.dr_repo.get(dr_id)
    assert loaded.status == "APPROVED"
