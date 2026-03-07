from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "run_scenario.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_run_scenario_cli_runs_named_scenario():
    proc = run_cli("basic")

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
    proc = run_cli("active_dr")

    assert proc.returncode == 1
    assert proc.stdout.splitlines() == [
        "OK   created dr 1",
        "OK   created dr 2",
        "OK   submitted dr 1",
        "ERR  line 9: active delivery request already exists for partner p1",
    ]


def test_run_scenario_cli_returns_usage_without_argument():
    proc = subprocess.run(
        [sys.executable, "run_scenario.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 2
    assert proc.stdout.strip() == "usage: python run_scenario.py <scenario-path-or-name>"
