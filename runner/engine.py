from __future__ import annotations

from pathlib import Path
from typing import Iterable

from runner.dispatch import RunnerResult, RunnerRuntime, dispatch_parsed
from runner.parser import parse_line, resolve_arg_variables
from runner.validate import validate_parsed


def _error(msg: str) -> RunnerResult:
    return {"ok": False, "id": None, "msg": msg}


def run_lines(runtime: RunnerRuntime, lines: Iterable[str]) -> list[RunnerResult]:
    results: list[RunnerResult] = []

    for lineno, raw_line in enumerate(lines, start=1):
        try:
            parsed = parse_line(raw_line)
            if parsed is None:
                continue

            validate_parsed(parsed)
            resolved = resolve_arg_variables(parsed, runtime.vars)
            result = dispatch_parsed(runtime, resolved)

            if parsed.assign is not None:
                result_id = result["id"]
                if result_id is None:
                    raise ValueError(f"cannot assign result without id: {parsed.assign}")
                runtime.vars[parsed.assign] = str(result_id)

            results.append(result)
        except Exception as exc:
            results.append(_error(f"line {lineno}: {exc}"))
            break

    return results


def run_file(runtime: RunnerRuntime, path: str | Path) -> list[RunnerResult]:
    return run_lines(runtime, Path(path).read_text().splitlines())
