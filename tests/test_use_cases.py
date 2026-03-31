import pytest

from app.use_cases import (
    approve_delivery_request,
    create_delivery_request,
    get_sales_report,
    mark_delivered,
    reject_delivery_request,
    submit_delivery_request,
    submit_sales_report,
    void_sales_report,
)
from domain.errors import InvalidReport, InsufficientStock
from app.errors import NotFound, ValidationError
from domain.sales_report import ReportItem, AlreadyVoided
from domain.delivery_request import (
    InvalidDeliveryRequest,
    Status,
    RequestItem,
)
from infra.errors import DataIntegrityError
from policies.identity import Forbidden, Role, Actor
from policies.stock_projection import compute_partner_stock
from tests.helpers import given_dr, given_sr


def test_submit_sales_report_happy_path_persists(ctx, partner_actor):
    dr_id, dr = create_delivery_request(
        ctx, partner_actor, payload=[RequestItem(book_id="b1", quantity=3)]
    )
    dr_id, dr = submit_delivery_request(ctx, partner_actor, dr_id)
    _, dr = approve_delivery_request(ctx, Actor(role=Role.ADMIN), dr_id)
    _, dr = mark_delivered(ctx, Actor(role=Role.ADMIN), dr_id)

    assert ctx.dr_repo.get(dr_id) == dr

    sr_id, report = submit_sales_report(
        ctx=ctx,
        actor=partner_actor,
        payload=[ReportItem(book_id="b1", quantity=2)],
    )

    stock = compute_partner_stock(partner_actor.partner_id, ctx.dr_repo, ctx.sr_repo)

    assert ctx.sr_repo.get(sr_id) == report
    assert stock["b1"] == 1


def test_submit_sales_report_requires_known_book_ids(ctx, partner_actor):
    with pytest.raises(InvalidReport):
        submit_sales_report(
            ctx=ctx,
            actor=partner_actor,
            payload=[ReportItem(book_id="b5", quantity=2)],
        )


def test_submit_sales_report_rejects_quantities_gt_stock(ctx, partner_actor):
    # Stock entrant: 2 examplaires de b1 et 3 de b2 livrés au partenaire
    _ = given_dr(ctx, partner_actor.partner_id, Status.DELIVERED)

    # Ventes déclarées: 3 exemplaires de b1 => dépasse le stock entrant (2)
    with pytest.raises(InsufficientStock):
        submit_sales_report(
            ctx=ctx,
            actor=partner_actor,
            payload=[ReportItem(book_id="b1", quantity=3)],
        )

    assert ctx.sr_repo.list_entries() == []


def test_submit_sales_report_rejects_invalid_sr_before_catalog_policy(
    ctx, partner_actor
):
    with pytest.raises(InvalidReport):
        submit_sales_report(
            ctx=ctx,
            actor=partner_actor,
            payload=[ReportItem(book_id="b1", quantity=1)],  # total_quantity=1 < 2
        )

    assert ctx.sr_repo.list_all() == []


def test_admin_cannot_submit_sales_report(ctx, admin_actor):
    with pytest.raises(Forbidden):
        submit_sales_report(
            ctx=ctx,
            actor=admin_actor,
            payload=[ReportItem(book_id="b1", quantity=2)],
        )

    assert ctx.sr_repo.list_all() == []


def test_partner_cannot_submit_another_partner_delivery_request(ctx):
    p1 = Actor(role=Role.PARTNER, partner_id="p1")
    p2 = Actor(role=Role.PARTNER, partner_id="p2")

    dr_id, _ = create_delivery_request(
        ctx,
        p1,
        payload=[RequestItem(book_id="b1", quantity=2)],
    )

    with pytest.raises(Forbidden):
        submit_delivery_request(ctx, p2, dr_id)


def test_create_delivery_request_requires_known_book_ids(ctx, partner_actor):
    with pytest.raises(InvalidDeliveryRequest):
        create_delivery_request(
            ctx=ctx,
            actor=partner_actor,
            payload=[RequestItem(book_id="b5", quantity=2)],
        )


def test_submit_allowed_when_no_previous_delivery_exists(ctx, partner_actor):
    dr_id, _ = create_delivery_request(
        ctx=ctx,
        actor=partner_actor,
        payload=[RequestItem(book_id="b1", quantity=2)],
    )
    _, submitted = submit_delivery_request(ctx=ctx, actor=partner_actor, dr_id=dr_id)

    assert submitted.status is Status.SUBMITTED
    assert submitted.partner_id == partner_actor.partner_id
    assert submitted.items == [RequestItem(book_id="b1", quantity=2)]
    assert ctx.dr_repo.list_all() == [submitted]


def test_admin_cannot_submit_delivery_request(ctx, admin_actor):
    with pytest.raises(Forbidden):
        submit_delivery_request(
            ctx=ctx,
            actor=admin_actor,
            dr_id=1,
        )
    assert ctx.dr_repo.list_entries() == []


def test_reject_delivery_request_requires_admin(ctx, partner_actor):
    dr1 = given_dr(ctx, partner_actor.partner_id, Status.SUBMITTED)
    with pytest.raises(Forbidden):
        reject_delivery_request(ctx, partner_actor, dr1, "test")


def test_reject_delivery_request_requires_reason(ctx, admin_actor):
    dr1 = given_dr(ctx, "p1", Status.SUBMITTED)
    with pytest.raises(ValidationError):
        reject_delivery_request(ctx, admin_actor, dr1, "")


def test_reject_delivery_request_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        reject_delivery_request(ctx, admin_actor, 999, "test")


def test_reject_delivery_request_happy_path(ctx, admin_actor):
    """sets_state_and_records_audit"""
    dr1 = given_dr(ctx, "p1", Status.SUBMITTED)
    _, dr = reject_delivery_request(ctx, admin_actor, dr1, "test")
    audit_event = ctx.audit.get(1)
    assert dr.status == Status.REJECTED
    assert audit_event["type"] == "DR_REJECTED"
    assert audit_event["target_type"] == "delivery_request"
    assert audit_event["target_id"] == dr1
    assert audit_event["reason"] == "test"


# def test_reject_delivery_request_fails_if_audit_unavailable(ctx, admin_actor):
#     dr1 = given_dr(ctx, "p1", Status.SUBMITTED)
#     ctx.audit.fail = True

#     with pytest.raises(RuntimeError, match="audit unavailable"):
#         reject_delivery_request(ctx, admin_actor, dr1, "test")

#     dr = ctx.dr_repo.get(dr1)
#     assert dr.status == Status.SUBMITTED
#     assert ctx.audit.list_all() == []


def test_submit_delivery_request_not_found(ctx, partner_actor):
    with pytest.raises(NotFound):
        submit_delivery_request(ctx, partner_actor, dr_id=999)


def test_approve_delivery_request_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        approve_delivery_request(ctx, admin_actor, dr_id=999)


def test_mark_delivered_dr_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        mark_delivered(ctx, admin_actor, dr_id=999)


def test_void_sales_report_requires_admin(ctx, partner_actor):
    _ = given_dr(ctx, partner_actor.partner_id, Status.DELIVERED)
    sr_id = given_sr(ctx, partner_actor.partner_id)
    with pytest.raises(Forbidden):
        void_sales_report(ctx, partner_actor, sr_id, "invalid report")

    assert ctx.sr_repo.get(sr_id).voided is False
    assert ctx.audit.list_all() == []


def test_void_sales_report_requires_reason(ctx, admin_actor, partner_actor):
    _ = given_dr(ctx, partner_actor.partner_id, Status.DELIVERED)
    sr_id = given_sr(ctx, partner_actor.partner_id)
    with pytest.raises(ValidationError):
        void_sales_report(ctx, admin_actor, sr_id, "")

    assert ctx.sr_repo.get(sr_id).voided is False
    assert ctx.audit.list_all() == []


def test_void_sales_report_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        void_sales_report(ctx, admin_actor, 999, "invalid report")


def test_void_sales_report_happy_path(ctx, admin_actor):
    """voids_report_and_records_audit"""
    _ = given_dr(ctx, "p1", Status.DELIVERED)
    sr_id = given_sr(ctx, "p1")
    _, report = void_sales_report(ctx, admin_actor, sr_id, "invalid report")

    audit_event = ctx.audit.get(1)
    assert report.voided is True
    assert len(ctx.audit.list_all()) == 1
    assert audit_event["type"] == "SR_VOIDED"
    assert audit_event["target_type"] == "sales_report"
    assert audit_event["target_id"] == sr_id
    assert audit_event["reason"] == "invalid report"


def test_void_sales_report_already_voided_raises(ctx, admin_actor, partner_actor):
    _ = given_dr(ctx, partner_actor.partner_id, Status.DELIVERED)
    sr_id = given_sr(ctx, partner_actor.partner_id)
    void_sales_report(ctx, admin_actor, sr_id, "invalid report")
    with pytest.raises(AlreadyVoided):
        void_sales_report(ctx, admin_actor, sr_id, "invalid report")


# def test_void_sales_report_fails_if_audit_unavailable_and_sr_unchanged(
#     ctx, admin_actor
# ):
#     sr_id = given_sr(ctx, "p1")
#     ctx.audit.fail = True

#     with pytest.raises(RuntimeError, match="audit unavailable"):
#         void_sales_report(ctx, admin_actor, sr_id, "invalid report")

#     sr = ctx.sr_repo.get(sr_id)
#     assert sr.voided is False
#     assert ctx.audit.list_all() == []


def test_get_sales_report_not_found_raises_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        get_sales_report(ctx, admin_actor, 999)


def test_void_sales_report_with_missing_inventory_line(ctx, admin_actor, partner_actor):

    _ = given_dr(
        ctx,
        partner_actor.partner_id,
        Status.DELIVERED,
        items=[
            RequestItem(book_id="b1", quantity=4),
            RequestItem(book_id="b2", quantity=4),
            RequestItem(book_id="b3", quantity=4),
        ],
    )  # 4, 4, 4 livrés au partenaire
    sr_id = given_sr(
        ctx,
        partner_actor.partner_id,
        items=[
            ReportItem(book_id="b3", quantity=1),
            ReportItem(book_id="b2", quantity=2),
        ],
    )  # 4, 4, 4 -> 4, 2, 3 (restant en stock)

    pi3 = ctx.pi_repo.get(partner_actor.partner_id, "b3")
    pi2 = ctx.pi_repo.get(partner_actor.partner_id, "b2")
    pi1 = ctx.pi_repo.get(partner_actor.partner_id, "b1")

    assert pi3 and pi3.current_quantity == 3
    assert pi2 and pi2.current_quantity == 2
    assert pi1 and pi1.current_quantity == 4

    # let us delete the inventory line for b3 to simulate the missing inventory line scenario during voiding

    ctx.pi_repo.conn.execute(
        "DELETE FROM partner_inventories WHERE partner_id = ? AND book_sku = ?",
        (partner_actor.partner_id, "b3"),
    )
    ctx.pi_repo.conn.commit()

    pi3 = ctx.pi_repo.get(partner_actor.partner_id, "b3")
    assert pi3 is None

    with pytest.raises(
        DataIntegrityError,
        match="contains following items \\(b3\\), for which no inventory line exists",
        # match="sales report with id .* contains book_id\\(s\\) b3 for which no inventory line exists",
    ):
        void_sales_report(ctx, admin_actor, sr_id, "invalid report")
