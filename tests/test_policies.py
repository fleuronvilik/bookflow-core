import pytest

from domain.delivery_request import Status as DRStatus
from app.use_cases import submit_delivery_request
from policies.active_delivery_request import ActiveDeliveryRequestExists
from policies.identity import Actor, Role
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
