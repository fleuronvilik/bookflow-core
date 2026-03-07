from __future__ import annotations

from runner.parser import ParsedLine


class RunnerValidationError(Exception):
    pass


COMMAND_SPECS = {
    "create": {"actor": "P", "required": {"items"}, "allowed": {"items"}},
    "submit": {"actor": "P", "required": {"dr"}, "allowed": {"dr"}},
    "approve": {"actor": "A", "required": {"dr"}, "allowed": {"dr"}},
    "deliver": {"actor": "A", "required": {"dr"}, "allowed": {"dr"}},
    "report": {"actor": "P", "required": {"items"}, "allowed": {"items"}},
    "void": {"actor": "A", "required": {"sr", "reason"}, "allowed": {"sr", "reason"}},
}

QUERY_SPECS = {
    "show": {"required_any": {"dr", "sr"}},
    "stock": {"required": {"partner"}},
}


def _unknown_args(args: dict[str, str], allowed: set[str]) -> set[str]:
    return set(args) - allowed


def validate_parsed(parsed: ParsedLine) -> None:
    if parsed.actor is not None:
        _validate_command(parsed)
        return
    _validate_query(parsed)


def _validate_command(parsed: ParsedLine) -> None:
    spec = COMMAND_SPECS.get(parsed.command)
    if spec is None:
        raise RunnerValidationError(f"unknown command: {parsed.command}")

    expected_actor = spec["actor"]
    if parsed.actor != expected_actor:
        raise RunnerValidationError(
            f"command {parsed.command} requires actor {expected_actor}"
        )

    missing = spec["required"] - set(parsed.args)
    if missing:
        raise RunnerValidationError(
            f"command {parsed.command} missing args: {', '.join(sorted(missing))}"
        )

    unknown = _unknown_args(parsed.args, spec["allowed"])
    if unknown:
        raise RunnerValidationError(
            f"command {parsed.command} does not support args: {', '.join(sorted(unknown))}"
        )


def _validate_query(parsed: ParsedLine) -> None:
    spec = QUERY_SPECS.get(parsed.command)
    if spec is None:
        raise RunnerValidationError(f"unknown query: {parsed.command}")

    if parsed.assign is not None:
        raise RunnerValidationError(f"query {parsed.command} does not support assignment")

    if parsed.command == "show":
        has_dr = "dr" in parsed.args
        has_sr = "sr" in parsed.args
        if not has_dr and not has_sr:
            raise RunnerValidationError("query show requires dr or sr")
        if has_dr and has_sr:
            raise RunnerValidationError("query show does not support both dr and sr")
        return

    missing = spec["required"] - set(parsed.args)
    if missing:
        raise RunnerValidationError(
            f"query {parsed.command} missing args: {', '.join(sorted(missing))}"
        )
