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
from domain.errors import InvalidReport
from app.errors import NotFound, ValidationError
from domain.sales_report import ReportItem, SalesReport, AlreadyVoided
from domain.delivery_request import (
    InvalidDeliveryRequest,
    Status,
    RequestItem,
    DeliveryRequest,
)
from policies.identity import Forbidden, Role, Actor
from policies.validations import InsufficientStock, compute_partner_stock
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
    # Stock entrant: 1 exemplaire de b1 livré au partenaire
    dr = DeliveryRequest.save_draft(
        partner_id=partner_actor.partner_id,
        items=[RequestItem(book_id="b1", quantity=2)],
    )
    dr.submit()
    dr.approve()
    dr.mark_delivered()
    ctx.dr_repo.create(dr)

    # Ventes déclarées: 2 exemplaires => dépasse le stock entrant (1)
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


# def test_list_reports_by_partner_filters_for_admin(admin_actor, sr_repo):
#     r1 = SalesReport(partner_id="p1", items=[ReportItem(book_id="b1", quantity=3)])
#     r2 = SalesReport(partner_id="p1", items=[ReportItem(book_id="b2", quantity=2)])
#     r3 = SalesReport(partner_id="p2", items=[ReportItem(book_id="b1", quantity=4)])

#     sr_repo.add(r1)
#     sr_repo.add(r2)
#     sr_repo.add(r3)

#     result = list_reports_by_partner(
#         actor=admin_actor, partner_id="p1", sr_repo=sr_repo
#     )

#     assert result == [r1, r2]


# def test_list_reports_by_partner_returns_empty_list_if_none(admin_actor, sr_repo):
#     result = list_reports_by_partner(
#         actor=admin_actor, partner_id="p1", sr_repo=sr_repo
#     )
#     assert result == []


# def test_list_reports_by_partner_rejects_partner(partner_actor, sr_repo):
#     with pytest.raises(Forbidden):
#         list_reports_by_partner(
#             actor=partner_actor, partner_id=partner_actor.partner_id, sr_repo=sr_repo
#         )


# def test_list_my_reports_rejects_admin(admin_actor, sr_repo):
#     with pytest.raises(Forbidden):
#         list_my_reports(actor=admin_actor, sr_repo=sr_repo)


# def test_list_my_reports_happy_path(partner_actor, sr_repo):
#     r1 = SalesReport(
#         partner_id=partner_actor.partner_id,
#         items=[ReportItem(book_id="b1", quantity=3)],
#     )
#     r2 = SalesReport(
#         partner_id=partner_actor.partner_id,
#         items=[ReportItem(book_id="b2", quantity=2)],
#     )
#     r3 = SalesReport(partner_id="p2", items=[ReportItem(book_id="b1", quantity=4)])

#     sr_repo.add(r1)
#     sr_repo.add(r2)
#     sr_repo.add(r3)

#     a3 = Actor(role=Role.PARTNER, partner_id="p3")

#     result = list_my_reports(actor=partner_actor, sr_repo=sr_repo)
#     assert result == [r1, r2]
#     result = list_my_reports(actor=a3, sr_repo=sr_repo)
#     assert result == []


def test_create_delivery_request_requires_known_book_ids(ctx, partner_actor):
    with pytest.raises(InvalidDeliveryRequest):
        create_delivery_request(
            ctx=ctx,
            actor=partner_actor,
            payload=[RequestItem(book_id="b5", quantity=2)],
        )


def test_submit_allowed_when_no_previous_delivery_exists(ctx, partner_actor):
    dr_id, dr = create_delivery_request(
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
    sr_id = given_sr(ctx, partner_actor.partner_id)
    with pytest.raises(Forbidden):
        void_sales_report(ctx, partner_actor, sr_id, "invalid report")

    assert ctx.sr_repo.get(sr_id).voided is False
    assert ctx.audit.list_all() == []


def test_void_sales_report_requires_reason(ctx, admin_actor):
    sr_id = given_sr(ctx, "p1")
    with pytest.raises(ValidationError):
        void_sales_report(ctx, admin_actor, sr_id, "")

    assert ctx.sr_repo.get(sr_id).voided is False
    assert ctx.audit.list_all() == []


def test_void_sales_report_not_found(ctx, admin_actor):
    with pytest.raises(NotFound):
        void_sales_report(ctx, admin_actor, 999, "invalid report")


def test_void_sales_report_happy_path(ctx, admin_actor):
    """voids_report_and_records_audit"""
    sr_id = given_sr(ctx, "p1")
    _, report = void_sales_report(ctx, admin_actor, sr_id, "invalid report")

    audit_event = ctx.audit.get(1)
    assert report.voided is True
    assert len(ctx.audit.list_all()) == 1
    assert audit_event["type"] == "SR_VOIDED"
    assert audit_event["target_type"] == "sales_report"
    assert audit_event["target_id"] == sr_id
    assert audit_event["reason"] == "invalid report"


def test_void_sales_report_already_voided_raises(ctx, admin_actor):
    sr_id = given_sr(ctx, "p1")
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
