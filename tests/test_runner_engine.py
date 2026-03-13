from runner.dispatch import RunnerRuntime
from runner.engine import run_file, run_lines
from app.bootstrap import admin, make_ctx, partner


def make_runtime() -> RunnerRuntime:
    return RunnerRuntime(
        ctx=make_ctx(testing=True),
        partner_id="p1",
        partner_actor=partner("p1"),
        admin_actor=admin(),
    )


def test_run_lines_simple_scenario_with_assignment():
    runtime = make_runtime()

    results = run_lines(runtime, ["P create items=b1*1;b2*1 -> dr1"])

    assert results == [{"ok": True, "id": 1, "msg": "created dr 1"}]
    assert runtime.vars == {"dr1": "1"}


def test_run_lines_ignores_comments():
    runtime = make_runtime()

    results = run_lines(
        runtime,
        [
            "# create a request",
            "P create items=b1*1;b2*1 -> dr1",
            "# inspect it",
            "show dr=$dr1",
        ],
    )

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"},
    ]


def test_run_lines_ignores_empty_lines():
    runtime = make_runtime()

    results = run_lines(
        runtime,
        [
            "",
            "   ",
            "P create items=b1*1;b2*1 -> dr1",
            "",
            "show dr=$dr1",
            "   ",
        ],
    )

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"},
    ]


def test_run_lines_stops_on_first_error():
    runtime = make_runtime()

    results = run_lines(
        runtime,
        [
            "P create items=b1*1;b2*1 -> dr1",
            "P submit dr=$missing",
            "P submit dr=$dr1",
        ],
    )

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": False, "id": None, "msg": "line 2: unknown variable: missing"},
    ]
    assert runtime.ctx.dr_repo.get(1).status.value == "DRAFT"


def test_run_lines_stores_variable_then_reuses_it():
    runtime = make_runtime()

    results = run_lines(
        runtime,
        [
            "P create items=b1*1;b2*1 -> dr1",
            "P submit dr=$dr1",
        ],
    )

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "submitted dr 1"},
    ]
    assert runtime.vars == {"dr1": "1"}
    assert runtime.ctx.dr_repo.get(1).status.value == "SUBMITTED"


def test_run_file_runs_scenario_from_path(tmp_path):
    runtime = make_runtime()
    scenario = tmp_path / "scenario.txt"
    scenario.write_text(
        "\n".join(
            [
                "# scenario",
                "",
                "P create items=b1*1;b2*1 -> dr1",
                "show dr=$dr1",
            ]
        )
    )

    results = run_file(runtime, scenario)

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"},
    ]


def test_run_lines_rejects_invalid_actor_for_command():
    runtime = make_runtime()

    results = run_lines(runtime, ["A submit dr=1"])

    assert results == [
        {"ok": False, "id": None, "msg": "line 1: command submit requires actor P"}
    ]


def test_run_lines_rejects_unsupported_command_arg():
    runtime = make_runtime()

    results = run_lines(runtime, ["P submit items=b1*2"])

    assert results == [
        {
            "ok": False,
            "id": None,
            "msg": "line 1: command submit missing args: dr",
        }
    ]


def test_run_lines_allows_assignment_on_submit():
    runtime = make_runtime()

    results = run_lines(
        runtime,
        [
            "P create items=b1*1;b2*1 -> dr1",
            "P submit dr=$dr1 -> submitted",
        ],
    )

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "submitted dr 1"},
    ]
    assert runtime.vars == {"dr1": "1", "submitted": "1"}


def test_run_lines_allows_future_show_partner_arg():
    runtime = make_runtime()

    results = run_lines(
        runtime,
        [
            "P create items=b1*1;b2*1 -> dr1",
            "show dr=$dr1 partner=P",
        ],
    )

    assert results == [
        {"ok": True, "id": 1, "msg": "created dr 1"},
        {"ok": True, "id": 1, "msg": "DR#1 status=DRAFT"},
    ]


def test_run_lines_rejects_unknown_command():
    runtime = make_runtime()

    results = run_lines(runtime, ["P reject dr=1"])

    assert results == [
        {"ok": False, "id": None, "msg": "line 1: unknown command: reject"}
    ]


def test_run_lines_rejects_query_assignment():
    runtime = make_runtime()

    results = run_lines(runtime, ["show dr=1 -> x"])

    assert results == [
        {
            "ok": False,
            "id": None,
            "msg": "line 1: query show does not support assignment",
        }
    ]
