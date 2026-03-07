from __future__ import annotations

import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from app.support.event_order import EventOrder
from runner import RunnerRuntime, run_file
from scripts.common import admin, make_ctx, partner


SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"


def resolve_scenario_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.exists():
        return candidate

    scenario_path = SCENARIOS_DIR / raw_path
    if scenario_path.exists():
        return scenario_path

    if candidate.suffix != ".txt":
        txt_candidate = SCENARIOS_DIR / f"{raw_path}.txt"
        if txt_candidate.exists():
            return txt_candidate

    raise FileNotFoundError(f"scenario not found: {raw_path}")


def make_runtime() -> RunnerRuntime:
    return RunnerRuntime(
        ctx=make_ctx(EventOrder()),
        partner_id="p1",
        partner_actor=partner("p1"),
        admin_actor=admin(),
    )


def render_result(result: dict[str, bool | int | None | str]) -> str:
    status = "OK" if result["ok"] else "ERR"
    return f"{status:<4} {result['msg']}"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python run_scenario.py <scenario-path-or-name>")
        return 2

    try:
        scenario_path = resolve_scenario_path(args[0])
        with redirect_stdout(StringIO()):
            results = run_file(make_runtime(), scenario_path)
    except Exception as exc:
        print(f"ERR  {exc}")
        return 1

    for result in results:
        print(render_result(result))

    if results and results[-1]["ok"] is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
