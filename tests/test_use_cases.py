import pytest

from domain.errors import InvalidReport
from app.errors import NotFound
from domain.sales_report import ReportItem, SalesReport
from domain.delivery_request import (
    InvalidDeliveryRequest,
    Status,
    RequestItem,
    DeliveryRequest,
)
from policies.identity import Forbidden, Role, Actor
from policies.validations import compute_partner_stock
from app import use_cases as uc


def test_submit_sales_report_happy_path_persists(ctx, partner_actor):
    dr_id, dr = uc.create_delivery_request(
        ctx, partner_actor, payload=[RequestItem(book_id="b1", quantity=3)]
    )
    dr_id, dr = uc.submit_delivery_request(ctx, partner_actor, dr_id)
    _, dr = uc.approve_delivery_request(ctx, Actor(role=Role.ADMIN), dr_id)
    dr.mark_delivered()

    assert ctx.dr_repo.list_all() == [dr]

    _, report = uc.submit_sales_report(
        ctx=ctx,
        actor=partner_actor,
        payload=[ReportItem(book_id="b1", quantity=2)],
    )

    stock = compute_partner_stock(partner_actor.partner_id, ctx.dr_repo, ctx.sr_repo)

    assert ctx.sr_repo.list_all() == [report]
    assert stock["b1"] == 1


def test_submit_sales_report_requires_known_book_ids(ctx, partner_actor):
    with pytest.raises(InvalidReport):
        uc.submit_sales_report(
            ctx=ctx,
            actor=partner_actor,
            payload=[ReportItem(book_id="b5", quantity=2)],
        )


def test_submit_sales_report_rejects_quantities_gt_stock(ctx, partner_actor):
    # Stock entrant: 1 exemplaire de b1 livré au partenaire
    dr = DeliveryRequest.save_draft(
        partner_id=partner_actor.partner_id,
        items=[RequestItem(book_id="b1", quantity=2)],
    )
    dr.submit()
    dr.approve()
    dr.mark_delivered()
    ctx.dr_repo.add(dr)

    # Ventes déclarées: 2 exemplaires => dépasse le stock entrant (1)
    with pytest.raises(InvalidReport):
        uc.submit_sales_report(
            ctx=ctx,
            actor=partner_actor,
            payload=[ReportItem(book_id="b1", quantity=3)],
        )

    assert ctx.sr_repo.list_entries() == []


def test_submit_sales_report_rejects_invalid_sr_before_catalog_policy(
    ctx, partner_actor
):
    with pytest.raises(InvalidReport):
        uc.submit_sales_report(
            ctx=ctx,
            actor=partner_actor,
            payload=[ReportItem(book_id="b1", quantity=1)],  # total_quantity=1 < 2
        )

    assert ctx.sr_repo.list_all() == []


def test_admin_cannot_submit_sales_report(ctx, admin_actor):
    with pytest.raises(Forbidden):
        uc.submit_sales_report(
            ctx=ctx,
            actor=admin_actor,
            payload=[ReportItem(book_id="b1", quantity=2)],
        )

    assert ctx.sr_repo.list_all() == []


def test_partner_cannot_submit_another_partner_delivery_request(ctx):
    p1 = Actor(role=Role.PARTNER, partner_id="p1")
    p2 = Actor(role=Role.PARTNER, partner_id="p2")

    dr_id, _ = uc.create_delivery_request(
        ctx,
        p1,
        payload=[RequestItem(book_id="b1", quantity=2)],
    )

    with pytest.raises(Forbidden):
        uc.submit_delivery_request(ctx, p2, dr_id)


def test_list_reports_by_partner_filters_for_admin(admin_actor, sr_repo):
    r1 = SalesReport(partner_id="p1", items=[ReportItem(book_id="b1", quantity=3)])
    r2 = SalesReport(partner_id="p1", items=[ReportItem(book_id="b2", quantity=2)])
    r3 = SalesReport(partner_id="p2", items=[ReportItem(book_id="b1", quantity=4)])

    sr_repo.add(r1)
    sr_repo.add(r2)
    sr_repo.add(r3)

    result = uc.list_reports_by_partner(
        actor=admin_actor, partner_id="p1", sr_repo=sr_repo
    )

    assert result == [r1, r2]


def test_list_reports_by_partner_returns_empty_list_if_none(admin_actor, sr_repo):
    result = uc.list_reports_by_partner(
        actor=admin_actor, partner_id="p1", sr_repo=sr_repo
    )
    assert result == []


def test_list_reports_by_partner_rejects_partner(partner_actor, sr_repo):
    with pytest.raises(Forbidden):
        uc.list_reports_by_partner(
            actor=partner_actor, partner_id=partner_actor.partner_id, sr_repo=sr_repo
        )


def test_list_my_reports_rejects_admin(admin_actor, sr_repo):
    with pytest.raises(Forbidden):
        uc.list_my_reports(actor=admin_actor, sr_repo=sr_repo)


def test_list_my_reports_happy_path(partner_actor, sr_repo):
    r1 = SalesReport(
        partner_id=partner_actor.partner_id,
        items=[ReportItem(book_id="b1", quantity=3)],
    )
    r2 = SalesReport(
        partner_id=partner_actor.partner_id,
        items=[ReportItem(book_id="b2", quantity=2)],
    )
    r3 = SalesReport(partner_id="p2", items=[ReportItem(book_id="b1", quantity=4)])

    sr_repo.add(r1)
    sr_repo.add(r2)
    sr_repo.add(r3)

    a3 = Actor(role=Role.PARTNER, partner_id="p3")

    result = uc.list_my_reports(actor=partner_actor, sr_repo=sr_repo)
    assert result == [r1, r2]
    result = uc.list_my_reports(actor=a3, sr_repo=sr_repo)
    assert result == []


def test_create_delivery_request_requires_known_book_ids(ctx, partner_actor):
    with pytest.raises(InvalidDeliveryRequest):
        uc.create_delivery_request(
            ctx=ctx,
            actor=partner_actor,
            payload=[RequestItem(book_id="b5", quantity=2)],
        )


def test_submit_allowed_when_no_previous_delivery_exists(ctx, partner_actor):
    dr_id, dr = uc.create_delivery_request(
        ctx=ctx,
        actor=partner_actor,
        payload=[RequestItem(book_id="b1", quantity=2)],
    )
    _, submitted = uc.submit_delivery_request(ctx=ctx, actor=partner_actor, dr_id=dr_id)

    assert submitted.status is Status.SUBMITTED
    assert submitted.partner_id == partner_actor.partner_id
    assert submitted.items == [RequestItem(book_id="b1", quantity=2)]
    assert ctx.dr_repo.list_all() == [submitted]


def test_admin_cannot_submit_delivery_request(ctx, admin_actor):
    with pytest.raises(Forbidden):
        uc.submit_delivery_request(
            ctx=ctx,
            actor=admin_actor,
            dr_id=1,
        )
    assert ctx.dr_repo.list_entries() == []


def test_submit_delivery_request_not_found(ctx, partner_actor):
    with pytest.raises(NotFound):
        uc.submit_delivery_request(ctx, partner_actor, dr_id=999)


def test_approve_delivery_request_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        uc.approve_delivery_request(ctx, admin_actor, dr_id=999)


def test_mark_delivered_dr_request_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        uc.mark_delivered_delivery_request(ctx, admin_actor, dr_id=999)


def test_get_sales_report_not_found_raises_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        uc.get_sales_report(ctx, admin_actor, 999)
