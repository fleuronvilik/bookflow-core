from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["BOOK_DEPOT_TESTING"] = "1"
    return subprocess.run(
        [sys.executable, "run_scenario.py", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_run_scenario_cli_runs_named_scenario():
    proc = run_cli("p1", "dr_happy_path")

    assert proc.returncode == 0
    assert proc.stdout.splitlines() == [
        "OK   created dr 1",
        "OK   DR#1 status=DRAFT",
        "OK   submitted dr 1",
        "OK   approved dr 1",
        "OK   delivered dr 1",
        "OK   DR#1 status=DELIVERED",
        "OK   stock p1: b1=1, b2=1",
    ]


def test_run_scenario_cli_returns_error_on_failed_scenario():
    proc = run_cli("p1", "single_active_dr_constraint")

    assert proc.returncode == 1
    assert proc.stdout.splitlines() == [
        "OK   created dr 1",
        "OK   created dr 2",
        "OK   submitted dr 1",
        "ERR  line 9: ActiveDeliveryRequestExists",
    ]


def test_run_scenario_cli_returns_usage_without_argument():
    env = dict(os.environ)
    env["BOOK_DEPOT_TESTING"] = "1"
    proc = subprocess.run(
        [sys.executable, "run_scenario.py"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 2
    assert (
        proc.stdout.strip()
        == "usage: python run_scenario.py <partner-id> <scenario-path-or-name>"
    )
