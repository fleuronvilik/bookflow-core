from domain.errors import InsufficientStock
from domain.partner_inventory import PartnerInventory
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
)
from .context import Context
from .helpers import get_dr_or_raise, get_sr_or_raise
from .errors import ValidationError


def create_delivery_request(
    ctx: Context, actor: Actor, payload: list[RequestItem]
) -> tuple[int, DeliveryRequest]:
    if actor.role is not Role.PARTNER:
        raise Forbidden("only PARTNER can create a delivery request")

    ensure_no_active_delivery_request_for_partner(
        partner_id=actor.partner_id, dr_repo=ctx.dr_repo
    )

    dr = DeliveryRequest.save_draft(partner_id=actor.partner_id, items=payload)

    # DR validated against global catalog (policy)
    validate_request_items_in_catalog(dr.items, ctx.catalog)

    dr_id = ctx.dr_repo.create(dr)
    dr = get_dr_or_raise(ctx, dr_id)
    return dr_id, dr


def submit_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> tuple[int, DeliveryRequest]:
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

    dr = dr.submit()
    ctx.dr_repo.save(dr)
    return dr_id, dr


def approve_delivery_request(
    ctx: Context, actor: Actor, dr_id: int
) -> tuple[int, DeliveryRequest]:
    # AuthZ minimale (comme pour submit SR)
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can approve a delivery request")

    dr = get_dr_or_raise(ctx, dr_id)
    dr = dr.approve()
    ctx.dr_repo.save(dr)
    return dr_id, dr


def reject_delivery_request(
    ctx: Context, actor: Actor, dr_id: int, reason: str
) -> tuple[int, DeliveryRequest]:
    if actor.role != Role.ADMIN:
        raise Forbidden("only an ADMIN can reject a deliery request")

    # reason obligatoire
    if reason is None or not str(reason).strip():
        raise ValidationError("reject reason is required")

    try:
        dr = get_dr_or_raise(ctx, dr_id)

        # Audit requis (si audit absent/KO -> on échoue)
        ctx.audit.record(
            {
                "type": "DR_REJECTED",
                "target_type": "delivery_request",
                "target_id": dr_id,
                "reason": reason,
            },
            autocommit=False,
        )

        # Transition métier (idéalement: l'entité refuse si state != SUBMITTED)
        dr = dr.reject()
        ctx.dr_repo.save(dr, autocommit=False)
        ctx.dr_repo.conn.commit()
    except Exception:
        ctx.dr_repo.conn.rollback()
        raise

    return dr_id, dr


def mark_delivered(
    ctx: Context, actor: Actor, dr_id: int
) -> tuple[int, DeliveryRequest]:
    if actor.role is not Role.ADMIN:
        raise Forbidden("only ADMIN can mark a delivery request delivered")

    try:
        dr = get_dr_or_raise(ctx, dr_id)
        dr = dr.mark_delivered()
        for items in dr.items:
            pi = ctx.pi_repo.get(dr.partner_id, items.book_id)
            if pi is None:
                pi = PartnerInventory(
                    partner_id=dr.partner_id, book_sku=items.book_id, current_quantity=0
                )
            pi = pi.deliver(items.quantity)
            ctx.pi_repo.save(pi, autocommit=False)
        ctx.dr_repo.save(dr, autocommit=False)
        ctx.dr_repo.conn.commit()
    except Exception:
        ctx.dr_repo.conn.rollback()
        raise
    return dr_id, dr


def submit_sales_report(
    ctx: Context, actor: Actor, payload: list[ReportItem]
) -> tuple[int, SalesReport]:
    # AuthZ minimale (rôles) : hors SR
    if actor.role != Role.PARTNER:
        raise Forbidden("only PARTNER can submit a sales report")

    report = SalesReport(
        id=None, partner_id=actor.partner_id, items=payload
    )  # invariants SR
    validate_report_items_in_catalog(report, ctx.catalog)  # policy externe

    working = {}
    for it in report.items:
        key = (report.partner_id, it.book_id)
        if key not in working:
            pi = ctx.pi_repo.get(report.partner_id, it.book_id)
            if pi is None:
                raise InsufficientStock(
                    f"Cannot report sale of {it.quantity} for {it.book_id}, no copy available"
                )
            pi = pi.reportSale(it.quantity)
            working[key] = pi  # .clone()

    try:
        sr_id = ctx.sr_repo.create(report, autocommit=False)  # persistance mémoire
        for pi in working.values():
            ctx.pi_repo.save(pi, autocommit=False)
        ctx.sr_repo.conn.commit()
        report = get_sr_or_raise(ctx, sr_id)
    except Exception:
        ctx.sr_repo.conn.rollback()
        raise
    return sr_id, report


def void_sales_report(
    ctx: Context, actor: Actor, sr_id: int, reason: str
) -> tuple[int, SalesReport]:
    if actor.role != Role.ADMIN:
        raise Forbidden("only an ADMIN can void a sales report")

    if reason is None or not str(reason).strip():
        raise ValidationError("void reason is required")

    sr = get_sr_or_raise(ctx, sr_id)
    if sr.voided:
        raise AlreadyVoided(f"sales report with id {sr_id} is already voided")

    try:
        for it in sr.items:
            pi = ctx.pi_repo.get(sr.partner_id, it.book_id)
            pi = pi.restoreSales(it.quantity)
            ctx.pi_repo.save(pi, autocommit=False)

        ctx.sr_repo.mark_void(sr_id, autocommit=False)
        ctx.audit.record(
            {
                "type": "SR_VOIDED",
                "target_type": "sales_report",
                "target_id": sr_id,
                "reason": reason,
            },
            autocommit=False,
        )
        ctx.sr_repo.conn.commit()
        report = get_sr_or_raise(ctx, sr_id)
    except Exception:
        ctx.sr_repo.conn.rollback()
        raise

    return sr_id, report


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
