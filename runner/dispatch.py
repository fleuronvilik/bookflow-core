from __future__ import annotations

from dataclasses import dataclass, field

from app.context import Context
from app.helpers import get_dr_or_raise
from app.use_cases import (
    approve_delivery_request,
    create_delivery_request,
    mark_delivered,
    submit_delivery_request,
    submit_sales_report,
    void_sales_report,
    get_sales_report,
    get_delivery_request,
)
from domain.delivery_request import RequestItem
from domain.sales_report import ReportItem
from policies.identity import Actor
from policies.stock_projection import compute_partner_stock
from runner.parser import ParsedLine


RunnerResult = dict[str, bool | int | None | str]


@dataclass(frozen=True)
class RunnerRuntime:
    ctx: Context
    partner_id: str
    partner_actor: Actor
    admin_actor: Actor
    vars: dict[str, str] = field(default_factory=dict)


def _parse_items(items: str, item_type: type[RequestItem] | type[ReportItem]):
    parsed_items = []
    for raw_item in items.split(";"):
        book_id, quantity = raw_item.split("*", 1)
        parsed_items.append(item_type(book_id=book_id, quantity=int(quantity)))
    return parsed_items


def _ok(id: int | None, msg: str) -> RunnerResult:
    return {"ok": True, "id": id, "msg": msg}


def run_create(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    payload = _parse_items(parsed.args["items"], RequestItem)
    dr_id, _ = create_delivery_request(runtime.ctx, runtime.partner_actor, payload)
    return _ok(dr_id, f"created dr {dr_id}")


def run_submit(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    dr_id, _ = submit_delivery_request(
        runtime.ctx, runtime.partner_actor, int(parsed.args["dr"])
    )
    return _ok(dr_id, f"submitted dr {dr_id}")


def run_approve(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    dr_id, _ = approve_delivery_request(
        runtime.ctx, runtime.admin_actor, int(parsed.args["dr"])
    )
    return _ok(dr_id, f"approved dr {dr_id}")


def run_deliver(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    dr_id, _ = mark_delivered(runtime.ctx, runtime.admin_actor, int(parsed.args["dr"]))
    return _ok(dr_id, f"delivered dr {dr_id}")


def run_report(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    payload = _parse_items(parsed.args["items"], ReportItem)
    sr_id, _ = submit_sales_report(runtime.ctx, runtime.partner_actor, payload)
    return _ok(sr_id, f"reported sr {sr_id}")


def run_void(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    sr_id, _ = void_sales_report(
        runtime.ctx,
        runtime.admin_actor,
        int(parsed.args["sr"]),
        parsed.args["reason"],
    )
    return _ok(sr_id, f"voided sr {sr_id}")


def run_show(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    if "dr" in parsed.args:
        dr_id = int(parsed.args["dr"])
        # dr = runtime.ctx.dr_repo.get(dr_id)
        dr = get_delivery_request(runtime.ctx, runtime.admin_actor, dr_id)
        return _ok(dr_id, f"DR#{dr_id} status={dr.status.value}")

    sr_id = int(parsed.args["sr"])
    # sr = runtime.ctx.sr_repo.get(sr_id)
    sr = get_sales_report(runtime.ctx, runtime.admin_actor, sr_id)
    return _ok(sr_id, f"SR#{sr_id} voided={sr.voided}")


def run_stock(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    stock = compute_partner_stock(
        runtime.partner_id,
        runtime.ctx.dr_repo,
        runtime.ctx.sr_repo,
    )
    if not stock:
        return _ok(None, f"stock {runtime.partner_id}: empty")

    rendered = ", ".join(
        f"{book_id}={quantity}" for book_id, quantity in sorted(stock.items())
    )
    return _ok(None, f"stock {runtime.partner_id}: {rendered}")


COMMANDS = {
    "create": run_create,
    "submit": run_submit,
    "approve": run_approve,
    "deliver": run_deliver,
    "report": run_report,
    "void": run_void,
}


QUERIES = {
    "show": run_show,
    "stock": run_stock,
}


def dispatch_parsed(runtime: RunnerRuntime, parsed: ParsedLine) -> RunnerResult:
    if parsed.actor is not None:
        return COMMANDS[parsed.command](runtime, parsed)
    return QUERIES[parsed.command](runtime, parsed)
