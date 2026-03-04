from typing import List, Tuple

from domain.delivery_request import RequestItem, DeliveryRequest
from domain.sales_report import SalesReport, ReportItem
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
from .repositories import InMemorySalesReportRepo
from .queries import reports_by_partner
from .context import Context
from .helpers import get_dr_or_raise, get_sr_or_raise


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

    # DR créée directement en SUBMITTED (DRAFT hors scope ici)
    dr_id = ctx.dr_repo.add(dr)
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

    # Policy ReportRequired (bloquée au submit)
    ensure_report_submitted_since_last_delivery(
        partner_id=actor.partner_id,
        dr_entries=ctx.dr_repo.list_entries(),
        sr_entries=ctx.sr_repo.list_entries(),
    )

    dr.submit()
    return dr_id, dr


def approve_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> Tuple[int, DeliveryRequest]:
    # AuthZ minimale (comme pour submit SR)
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can approve a delivery request")

    dr = get_dr_or_raise(ctx, dr_id)
    dr.approve()
    return dr_id, dr


def mark_delivered_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> Tuple[int, DeliveryRequest]:
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can mark a delivery request delivered")

    dr = get_dr_or_raise(ctx.dr_repo, dr_id)
    dr.mark_delivered()
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
    sr_id = ctx.sr_repo.add(report)  # persistance mémoire
    return sr_id, report


def list_reports_by_partner(
    *,
    actor: Actor,
    partner_id: str,
    sr_repo: InMemorySalesReportRepo,
) -> List[SalesReport]:
    # Rule: ADMIN must provide a partner_id (no "list all" shortcut in this use-case).
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can list reports for an arbitrary partner")

    if not partner_id:
        raise ValueError("partner_id is required")

    return reports_by_partner(sr_repo.list_all(), partner_id)


def list_my_reports(
    *,
    actor: Actor,
    sr_repo: InMemorySalesReportRepo,
) -> List[SalesReport]:
    # Rule: "my reports" is a PARTNER-only intention.
    if actor.role is not Role.PARTNER:
        raise Forbidden("only PARTNER can list their own reports")

    # Actor invariant guarantees partner_id is present for PARTNER.
    return reports_by_partner(sr_repo.list_all(), actor.partner_id)


def get_sales_report(ctx: Context, actor: Actor, sr_id: int) -> SalesReport:
    if actor.role != Role.ADMIN:
        raise Forbidden("only ADMIN can access a sale report")
    return get_sr_or_raise(ctx=ctx, sr_id=sr_id)
