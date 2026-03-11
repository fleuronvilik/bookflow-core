from typing import List, Tuple

from domain.delivery_request import RequestItem, DeliveryRequest
from domain.sales_report import AlreadyVoided, SalesReport, ReportItem
from policies.identity import Forbidden, Role, Actor
from policies.report_required import ensure_report_submitted_since_last_delivery
from policies.active_delivery_request import (
    ensure_no_active_delivery_request_for_partner,
)
from policies.validations import (
    validate_report_items_in_catalog,
    validate_request_items_in_catalog,
    validate_sales_report_against_stock,
)
from .context import Context
from .helpers import get_dr_or_raise, get_sr_or_raise
from .errors import ValidationError


def create_delivery_request(
    ctx: Context, actor: Actor, payload: List[RequestItem]
) -> Tuple[int, DeliveryRequest]:
    if actor.role is not Role.PARTNER:
        raise Forbidden("only PARTNER can create a delivery request")

    ensure_no_active_delivery_request_for_partner(
        partner_id=actor.partner_id, dr_repo=ctx.dr_repo
    )

    dr = DeliveryRequest.save_draft(partner_id=actor.partner_id, items=payload)

    # DR validated against global catalog (policy)
    validate_request_items_in_catalog(dr.items, ctx.catalog)

    dr_id = ctx.dr_repo.create(dr)
    return dr_id, dr


def submit_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> Tuple[int, DeliveryRequest]:
    # AuthZ minimale (comme pour submit SR)
    if actor.role is not Role.PARTNER:
        raise Forbidden("only PARTNER can submit a delivery request")

    dr = get_dr_or_raise(ctx, dr_id)

    if dr.partner_id != actor.partner_id:
        raise Forbidden("partner cannot submit another partner delivery request")

    ensure_no_active_delivery_request_for_partner(
        partner_id=dr.partner_id, dr_repo=ctx.dr_repo
    )

    # Policy ReportRequired (bloquée au submit)
    ensure_report_submitted_since_last_delivery(
        partner_id=dr.partner_id, dr_repo=ctx.dr_repo, sr_repo=ctx.sr_repo
    )

    dr.submit()
    ctx.dr_repo.save_status(dr_id, dr.status)
    return dr_id, dr


def approve_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> Tuple[int, DeliveryRequest]:
    # AuthZ minimale (comme pour submit SR)
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can approve a delivery request")

    dr = get_dr_or_raise(ctx, dr_id)
    dr.approve()
    ctx.dr_repo.save_status(dr_id, dr.status)
    return dr_id, dr


def reject_delivery_request(
    ctx: Context, actor: Actor, dr_id: int, reason: str
) -> Tuple[int, DeliveryRequest]:
    if actor.role != Role.ADMIN:
        raise Forbidden("only an ADMIN can reject a deliery request")

    # reason obligatoire
    if reason is None or not str(reason).strip():
        raise ValidationError("reject reason is required")

    dr = get_dr_or_raise(ctx, dr_id)

    # Audit requis (si audit absent/KO -> on échoue)
    ctx.audit.record(
        {
            "type": "DR_REJECTED",
            "target_type": "delivery_request",
            "target_id": dr_id,
            "reason": reason,
        }
    )

    # Transition métier (idéalement: l'entité refuse si state != SUBMITTED)
    dr.reject()

    return dr_id, dr


def mark_delivered(
    ctx: Context, actor: Actor, dr_id: int
) -> Tuple[int, DeliveryRequest]:
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can mark a delivery request delivered")

    dr = get_dr_or_raise(ctx, dr_id)
    dr.mark_delivered()
    ctx.dr_repo.save_status(dr_id, dr.status)
    return dr_id, dr


def submit_sales_report(
    ctx: Context, actor: Actor, payload: List[ReportItem]
) -> Tuple[int, SalesReport]:
    # AuthZ minimale (rôles) : hors SR
    if actor.role != Role.PARTNER:
        raise Forbidden("only PARTNER can submit a sales report")

    report = SalesReport(partner_id=actor.partner_id, items=payload)  # invariants SR
    validate_report_items_in_catalog(report, ctx.catalog)  # policy externe
    validate_sales_report_against_stock(
        report=report, dr_repo=ctx.dr_repo, sr_repo=ctx.sr_repo
    )
    sr_id = ctx.sr_repo.create(report)  # persistance mémoire
    return sr_id, report


def void_sales_report(
    ctx: Context, actor: Actor, sr_id: int, reason: str
) -> Tuple[int, SalesReport]:
    if actor.role != Role.ADMIN:
        raise Forbidden("only an ADMIN can void a sales report")

    if reason is None or not str(reason).strip():
        raise ValidationError("void reason is required")

    sr = get_sr_or_raise(ctx, sr_id)
    if sr.voided:
        raise AlreadyVoided(f"sales report with id {sr_id} is already voided")
    ctx.sr_repo.mark_void(sr_id)

    ctx.audit.record(
        {
            "type": "SR_VOIDED",
            "target_type": "sales_report",
            "target_id": sr_id,
            "reason": reason,
        }
    )

    # ctx.sr_repo.mark_void(sr_id)
    return sr_id, get_sr_or_raise(ctx, sr_id)


# def list_reports_by_partner(
#     *,
#     actor: Actor,
#     partner_id: str,
#     sr_repo: InMemorySalesReportRepo,
# ) -> List[SalesReport]:
#     # Rule: ADMIN must provide a partner_id (no "list all" shortcut in this use-case).
#     if actor.role is not Role.ADMIN:
#         raise Forbidden("only ADMIN can list reports for an arbitrary partner")

#     if not partner_id:
#         raise ValueError("partner_id is required")

#     return reports_by_partner(sr_repo.list_all(), partner_id)


# def list_my_reports(
#     *,
#     actor: Actor,
#     sr_repo: InMemorySalesReportRepo,
# ) -> List[SalesReport]:
#     # Rule: "my reports" is a PARTNER-only intention.
#     if actor.role is not Role.PARTNER:
#         raise Forbidden("only PARTNER can list their own reports")

#     # Actor invariant guarantees partner_id is present for PARTNER.
#     return reports_by_partner(sr_repo.list_all(), actor.partner_id)


def get_sales_report(ctx: Context, actor: Actor, sr_id: int) -> SalesReport | None:
    if actor.role != Role.ADMIN:
        raise Forbidden("only ADMIN can access a sale report")
    return get_sr_or_raise(ctx, sr_id)


def get_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> DeliveryRequest | None:
    if actor.role != Role.ADMIN:
        raise Forbidden("only ADMIN can access a delivery request")
    return get_dr_or_raise(ctx, dr_id)
