import pytest
from domain.delivery_request import DeliveryRequest, RequestItem
from app.helpers import get_dr_or_raise


def test_create_and_get_dr(ctx):
    dr = DeliveryRequest.save_draft(partner_id="luigi", items=[RequestItem("b1", 3)])

    dr_id = ctx.dr_repo.create(dr)

    loaded = ctx.dr_repo.get(dr_id)

    assert loaded.items == [RequestItem("b1", 3)]


def test_save(ctx):
    dr = DeliveryRequest.save_draft(partner_id="luigi", items=[RequestItem("b1", 3)])

    dr_id = ctx.dr_repo.create(dr)

    loaded = ctx.dr_repo.get(dr_id)
    loaded = loaded.submit()
    ctx.dr_repo.save(loaded)

    loaded = ctx.dr_repo.get(dr_id)
    assert loaded.status == "SUBMITTED"

    loaded = ctx.dr_repo.get(dr_id)
    loaded = loaded.approve()
    ctx.dr_repo.save(loaded)

    loaded = ctx.dr_repo.get(dr_id)
    assert loaded.status == "APPROVED"
