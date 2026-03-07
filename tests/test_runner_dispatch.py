from domain.delivery_request import Status
from runner.dispatch import COMMANDS, QUERIES, RunnerRuntime, dispatch_parsed
from runner.parser import ParsedLine
from scripts.common import admin, make_ctx, partner
from app.support.event_order import EventOrder


def make_runtime() -> RunnerRuntime:
    return RunnerRuntime(
        ctx=make_ctx(EventOrder()),
        partner_id="p1",
        partner_actor=partner("p1"),
        admin_actor=admin(),
    )


def test_commands_and_queries_registry():
    assert set(COMMANDS) == {
        "create",
        "submit",
        "approve",
        "deliver",
        "report",
        "void",
    }
    assert set(QUERIES) == {"show", "stock"}


def test_dispatch_create():
    runtime = make_runtime()

    result = dispatch_parsed(
        runtime,
        ParsedLine(
            actor="P",
            command="create",
            args={"items": "b1*1;b2*1"},
            assign="dr1",
        ),
    )

    assert result == {"ok": True, "id": 1, "msg": "created dr 1"}
    dr = runtime.ctx.dr_repo.get(1)
    assert dr.partner_id == "p1"
    assert dr.status is Status.DRAFT
    assert [(it.book_id, it.quantity) for it in dr.items] == [("b1", 1), ("b2", 1)]


def test_dispatch_submit():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*1;b2*1"}, assign="dr1"),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )

    assert result == {"ok": True, "id": 1, "msg": "submitted dr 1"}
    assert runtime.ctx.dr_repo.get(1).status is Status.SUBMITTED


def test_dispatch_approve():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*1;b2*1"}, assign="dr1"),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="approve", args={"dr": "1"}, assign=None),
    )

    assert result == {"ok": True, "id": 1, "msg": "approved dr 1"}
    assert runtime.ctx.dr_repo.get(1).status is Status.APPROVED


def test_dispatch_deliver():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*1;b2*1"}, assign="dr1"),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="approve", args={"dr": "1"}, assign=None),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="deliver", args={"dr": "1"}, assign=None),
    )

    assert result == {"ok": True, "id": 1, "msg": "delivered dr 1"}
    assert runtime.ctx.dr_repo.get(1).status is Status.DELIVERED


def test_dispatch_report():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*2"}, assign="dr1"),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="approve", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="deliver", args={"dr": "1"}, assign=None),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="report", args={"items": "b1*2"}, assign="sr1"),
    )

    assert result == {"ok": True, "id": 2, "msg": "reported sr 2"}
    sr = runtime.ctx.sr_repo.get(2)
    assert sr.partner_id == "p1"
    assert sr.voided is False
    assert [(it.book_id, it.quantity) for it in sr.items] == [("b1", 2)]


def test_dispatch_void():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*2"}, assign="dr1"),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="approve", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="deliver", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="report", args={"items": "b1*2"}, assign="sr1"),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="void", args={"sr": "2", "reason": "mistake"}, assign=None),
    )

    assert result == {"ok": True, "id": 2, "msg": "voided sr 2"}
    assert runtime.ctx.sr_repo.get(2).voided is True


def test_dispatch_show_dr():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*1;b2*1"}, assign="dr1"),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor=None, command="show", args={"dr": "1"}, assign=None),
    )

    assert result == {"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"}


def test_dispatch_show_sr():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*2"}, assign="dr1"),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="approve", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="deliver", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="report", args={"items": "b1*2"}, assign="sr1"),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor=None, command="show", args={"sr": "2"}, assign=None),
    )

    assert result == {"ok": True, "id": 2, "msg": "SR#2 voided=False"}


def test_dispatch_stock_uses_runner_partner():
    runtime = make_runtime()
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="create", args={"items": "b1*2;b2*1"}, assign="dr1"),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="submit", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="approve", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="A", command="deliver", args={"dr": "1"}, assign=None),
    )
    dispatch_parsed(
        runtime,
        ParsedLine(actor="P", command="report", args={"items": "b1*2"}, assign="sr1"),
    )

    result = dispatch_parsed(
        runtime,
        ParsedLine(actor=None, command="stock", args={"partner": "P"}, assign=None),
    )

    assert result == {"ok": True, "id": None, "msg": "stock p1: b1=0, b2=1"}
