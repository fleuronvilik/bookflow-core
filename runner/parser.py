from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedLine:
    actor: str | None
    command: str
    args: dict[str, str]
    assign: str | None


class UnknownVariableError(Exception):
    pass


def parse_line(line: str) -> ParsedLine | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("#"):
        return None

    tokens = stripped.split()
    if not tokens:
        return None

    actor: str | None = None
    assign: str | None = None

    if tokens[0] in {"P", "A"}:
        if len(tokens) < 2:
            raise ValueError(f"invalid command line: {line}")
        actor = tokens[0]
        command = tokens[1]
        tail = tokens[2:]
    else:
        command = tokens[0]
        tail = tokens[1:]

    args: dict[str, str] = {}
    i = 0
    while i < len(tail):
        token = tail[i]
        if token == "->":
            if assign is not None or i + 1 >= len(tail):
                raise ValueError(f"invalid assignment syntax: {line}")
            assign = tail[i + 1]
            i += 2
            continue
        if "=" not in token:
            raise ValueError(f"invalid argument syntax: {line}")
        key, value = token.split("=", 1)
        if not key or not value:
            raise ValueError(f"invalid argument syntax: {line}")
        args[key] = value
        i += 1

    return ParsedLine(actor=actor, command=command, args=args, assign=assign)


def resolve_arg_variables(
    parsed: ParsedLine, vars: dict[str, str]
) -> ParsedLine:
    resolved_args: dict[str, str] = {}

    for key, value in parsed.args.items():
        if value.startswith("$"):
            name = value[1:]
            if name not in vars:
                raise UnknownVariableError(f"unknown variable: {name}")
            resolved_args[key] = vars[name]
            continue
        resolved_args[key] = value

    return ParsedLine(
        actor=parsed.actor,
        command=parsed.command,
        args=resolved_args,
        assign=parsed.assign,
    )
