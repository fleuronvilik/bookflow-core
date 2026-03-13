# from app.errors import NotFound
from .context import Context
from .errors import NotFound


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
