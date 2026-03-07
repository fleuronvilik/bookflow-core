from pathlib import Path

from app.support.event_order import EventOrder
from runner.dispatch import RunnerRuntime
from runner.engine import run_lines
from scripts.common import admin, make_ctx, partner


SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def make_runtime() -> RunnerRuntime:
    return RunnerRuntime(
        ctx=make_ctx(EventOrder()),
        partner_id="p1",
        partner_actor=partner("p1"),
        admin_actor=admin(),
    )


def load_scenario(name: str) -> list[str]:
    return (SCENARIOS_DIR / name).read_text().splitlines()


def test_basic_scenario_runs_without_error_and_reuses_variables():
    runtime = make_runtime()

    results = run_lines(runtime, load_scenario("basic.txt"))

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"},
        {"ok": True, "id": 1, "msg": "submitted dr 1"},
        {"ok": True, "id": 1, "msg": "approved dr 1"},
        {"ok": True, "id": 1, "msg": "delivered dr 1"},
        {"ok": True, "id": 1, "msg": "DR#1 status=DELIVERED"},
        {"ok": True, "id": None, "msg": "stock p1: b1=1, b2=1"},
    ]
    assert runtime.vars == {
        "dr1": "1",
        "submitted": "1",
        "approved": "1",
        "delivered": "1",
    }


def test_basic_scenario_ignores_comments_and_blank_lines():
    runtime = make_runtime()

    results = run_lines(runtime, load_scenario("basic.txt"))

    assert len(results) == 7
    assert all(result["ok"] is True for result in results)


def test_active_dr_scenario_stops_on_policy_violation():
    runtime = make_runtime()

    results = run_lines(runtime, load_scenario("active_dr.txt"))

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 2, "msg": "created dr 2"},
        {"ok": True, "id": 1, "msg": "submitted dr 1"},
        {
            "ok": False,
            "id": None,
            "msg": "line 9: active delivery request already exists for partner p1",
        },
    ]
    assert runtime.vars == {"dr1": "1", "dr2": "2", "active1": "1"}


def test_report_required_scenario_stops_on_policy_violation():
    runtime = make_runtime()

    results = run_lines(runtime, load_scenario("report_required.txt"))

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "submitted dr 1"},
        {"ok": True, "id": 1, "msg": "approved dr 1"},
        {"ok": True, "id": 1, "msg": "delivered dr 1"},
        {"ok": True, "id": 2, "msg": "created dr 2"},
        {
            "ok": False,
            "id": None,
            "msg": "line 11: sales report required since last delivered delivery request",
        },
    ]
    assert runtime.vars == {
        "dr1": "1",
        "submitted1": "1",
        "approved1": "1",
        "delivered1": "1",
        "dr2": "2",
    }


def test_transversal_scenario_runs_without_error():
    runtime = make_runtime()

    results = run_lines(runtime, load_scenario("transversal.txt"))

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "submitted dr 1"},
        {"ok": True, "id": 1, "msg": "approved dr 1"},
        {"ok": True, "id": 1, "msg": "delivered dr 1"},
        {"ok": True, "id": 2, "msg": "reported sr 2"},
        {"ok": True, "id": 2, "msg": "SR#2 voided=False"},
        {"ok": True, "id": None, "msg": "stock p1: b1=0"},
        {"ok": True, "id": 2, "msg": "voided sr 2"},
        {"ok": True, "id": 2, "msg": "SR#2 voided=True"},
        {"ok": True, "id": None, "msg": "stock p1: b1=2"},
    ]
    assert runtime.vars == {
        "dr1": "1",
        "submitted1": "1",
        "approved1": "1",
        "delivered1": "1",
        "sr1": "2",
        "sr1_voided": "2",
    }
