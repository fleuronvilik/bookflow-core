from domain.sales_report import SalesReport, ReportItem


def test_create_and_get_sr(ctx, partner_actor):
    sr = SalesReport(
        id=None, partner_id=partner_actor.partner_id, items=[ReportItem("b1", 3)]
    )

    sr_id = ctx.sr_repo.create(sr)

    loaded = ctx.sr_repo.get(sr_id)

    assert loaded.items == [ReportItem("b1", 3)]
    assert loaded.voided is False


# def test_get_non_existent_sr(ctx):


def test_mark_sr_as_voided(ctx, partner_actor):
    sr = SalesReport(
        id=None, partner_id=partner_actor.partner_id, items=[ReportItem("b1", 3)]
    )

    sr_id = ctx.sr_repo.create(sr)

    loaded = ctx.sr_repo.get(sr_id)
    assert not loaded.voided

    ctx.sr_repo.mark_void(sr_id)
    loaded = ctx.sr_repo.get(sr_id)
    assert loaded.voided
