from domain.sales_report import SalesReport
from app.context import Context
from app.errors import NotFound
from infra.errors import DataIntegrityError


def get_dr_or_raise(ctx: Context, dr_id: int):
    dr = ctx.dr_repo.get(dr_id)
    if not dr:
        raise NotFound(f"delivery request not found: {dr_id}")
    return dr


def get_sr_or_raise(ctx: Context, sr_id: int):
    sr = ctx.sr_repo.get(sr_id)
    if not sr:
        raise NotFound(f"sales report not found: {sr_id}")
    return sr


def restore_quantities_or_raise(
    ctx: Context, sr: SalesReport, autocommit: bool
) -> None:
    missing_items_ids = []
    for it in sr.items:
        pi = ctx.pi_repo.get(sr.partner_id, it.book_id)
        if pi is None:
            missing_items_ids.append(it.book_id)
            continue
        pi = pi.restore_sale(it.quantity)
        ctx.pi_repo.save(pi, autocommit=False)
    if missing_items_ids:
        raise DataIntegrityError(
            f"Sales report with id {sr.id} contains following items ({', '.join(missing_items_ids)}), for which no inventory line exists"
        )
