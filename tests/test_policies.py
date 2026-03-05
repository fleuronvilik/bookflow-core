import pytest

from domain.delivery_request import RequestItem, Status as DRStatus
from app.use_cases import submit_delivery_request
from domain.sales_report import ReportItem
from policies.active_delivery_request import ActiveDeliveryRequestExists
from policies.identity import Actor, Role
from policies.stock_projection import compute_partner_stock
from tests.helpers import given_dr, given_sr

""" ARD: ActiveRequestDelivery policy """


def test_submit_blocked_if_existing_submitted(ctx, partner_actor):
    """bloque SUBMITTED"""
    _ = given_dr(ctx, partner_actor.partner_id, DRStatus.SUBMITTED)
    dr2 = given_dr(ctx, partner_actor.partner_id, DRStatus.DRAFT)

    with pytest.raises(ActiveDeliveryRequestExists):
        submit_delivery_request(ctx, partner_actor, dr2)


def test_submit_blocked_if_existing_approved(ctx, partner_actor):
    """bloque APPROVED"""
    _ = given_dr(ctx, partner_id=partner_actor.partner_id, status=DRStatus.APPROVED)
    dr2 = given_dr(ctx, partner_id=partner_actor.partner_id, status=DRStatus.DRAFT)

    with pytest.raises(ActiveDeliveryRequestExists):
        submit_delivery_request(ctx, partner_actor, dr2)


def test_submit_allowed_if_only_delivered_exists(ctx, partner_actor):
    """autorise DELIVERED"""
    _ = given_dr(ctx, partner_id=partner_actor.partner_id, status=DRStatus.DELIVERED)
    _ = given_sr(ctx, partner_id=partner_actor.partner_id)
    dr2 = given_dr(ctx, partner_id=partner_actor.partner_id, status=DRStatus.DRAFT)

    _, dr = submit_delivery_request(ctx, partner_actor, dr2)
    assert dr.status == DRStatus.SUBMITTED


def test_submit_allowed_if_only_rejected_exists(ctx, partner_actor):
    """autorise REJECTED"""
    _ = given_dr(ctx, partner_id=partner_actor.partner_id, status=DRStatus.REJECTED)
    dr2 = given_dr(ctx, partner_id=partner_actor.partner_id, status=DRStatus.DRAFT)

    _, dr = submit_delivery_request(ctx, partner_actor, dr2)
    assert dr.status == DRStatus.SUBMITTED


def test_submit_allowed_when_other_partner_has_active_request(ctx):
    "autorise si DR active d’un autre partenaire"
    # P1 a déjà une DR engagée
    _ = given_dr(ctx, "p1", DRStatus.SUBMITTED)

    # P2 prépare une DR
    dr2 = given_dr(ctx, "p2", DRStatus.DRAFT)

    # P2 doit pouvoir soumettre malgré la DR active de P1
    _, dr = submit_delivery_request(ctx, Actor(Role.PARTNER, "p2"), dr2)

    assert dr.status == DRStatus.SUBMITTED


""" StockProjection policy is tested in test_use_cases.py, via the submit_sales_report use case, which calls the validation that uses the stock projection. """


def test_compute_partner_stock_empty(ctx):
    stock = compute_partner_stock("p1", ctx.dr_repo, ctx.sr_repo)
    assert stock == {}


def test_compute_partner_stock_with_deliveries_only(ctx):
    _ = given_dr(
        ctx, "p1", DRStatus.DELIVERED, items=[RequestItem(book_id="b1", quantity=3)]
    )
    _ = given_dr(
        ctx,
        "p1",
        DRStatus.DELIVERED,
        items=[
            RequestItem(book_id="b1", quantity=2),
            RequestItem(book_id="b2", quantity=5),
        ],
    )
    stock = compute_partner_stock("p1", ctx.dr_repo, ctx.sr_repo)
    assert stock == {"b1": 5, "b2": 5}


def test_compute_partner_stock_with_deliveries_and_sales(ctx):
    _ = given_dr(
        ctx, "p1", DRStatus.DELIVERED, items=[RequestItem(book_id="b1", quantity=3)]
    )
    _ = given_dr(
        ctx,
        "p1",
        DRStatus.DELIVERED,
        items=[
            RequestItem(book_id="b1", quantity=2),
            RequestItem(book_id="b2", quantity=5),
        ],
    )
    _ = given_sr(
        ctx,
        "p1",
        items=[
            ReportItem(book_id="b1", quantity=4),
            ReportItem(book_id="b2", quantity=1),
        ],
    )
    stock = compute_partner_stock("p1", ctx.dr_repo, ctx.sr_repo)
    assert stock == {"b1": 1, "b2": 4}


def test_compute_partner_stock_ignores_other_partners(ctx):
    _ = given_dr(
        ctx, "p1", DRStatus.DELIVERED, items=[RequestItem(book_id="b1", quantity=3)]
    )
    _ = given_dr(
        ctx,
        "p2",
        DRStatus.DELIVERED,
        items=[
            RequestItem(book_id="b1", quantity=2),
            RequestItem(book_id="b2", quantity=5),
        ],
    )
    _ = given_sr(
        ctx,
        "p2",
        items=[
            ReportItem(book_id="b1", quantity=4),
            ReportItem(book_id="b2", quantity=1),
        ],
    )
    stock = compute_partner_stock("p1", ctx.dr_repo, ctx.sr_repo)
    assert stock == {"b1": 3}


def test_compute_partner_stock_ignores_voided_sales(ctx):
    _ = given_dr(
        ctx, "p1", DRStatus.DELIVERED, items=[RequestItem(book_id="b1", quantity=3)]
    )
    _ = given_sr(
        ctx,
        "p1",
        items=[
            ReportItem(book_id="b1", quantity=4),
        ],
        voided=True,
    )
    stock = compute_partner_stock("p1", ctx.dr_repo, ctx.sr_repo)
    assert stock == {"b1": 3}
