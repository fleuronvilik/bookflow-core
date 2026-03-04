# from app.errors import NotFound
from .context import Context
from .errors import NotFound


def get_dr_or_raise(ctx: Context, dr_id: int):
    try:
        return ctx.dr_repo.get(dr_id)
    except Exception:
        raise NotFound(f"delivery request not found: {dr_id}")


def get_sr_or_raise(ctx: Context, sr_id: int):
    try:
        return ctx.sr_repo.get(sr_id)
    except Exception:
        raise NotFound(f"sales report not found: {sr_id}")
