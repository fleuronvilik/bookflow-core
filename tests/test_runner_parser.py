import pytest

from runner.parser import (
    ParsedLine,
    UnknownVariableError,
    parse_line,
    resolve_arg_variables,
)


def test_parse_ignores_empty_line():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_parse_ignores_comment_line():
    assert parse_line("# comment") is None
    assert parse_line("   # comment") is None


def test_parse_create_command():
    assert parse_line("P create items=gb*1;cs*2 -> dr1") == ParsedLine(
        actor="P",
        command="create",
        args={"items": "gb*1;cs*2"},
        assign="dr1",
    )


def test_parse_submit_command():
    assert parse_line("P submit dr=$dr1") == ParsedLine(
        actor="P",
        command="submit",
        args={"dr": "$dr1"},
        assign=None,
    )


def test_parse_approve_command():
    assert parse_line("A approve dr=$dr1") == ParsedLine(
        actor="A",
        command="approve",
        args={"dr": "$dr1"},
        assign=None,
    )


def test_parse_deliver_command():
    assert parse_line("A deliver dr=$dr1") == ParsedLine(
        actor="A",
        command="deliver",
        args={"dr": "$dr1"},
        assign=None,
    )


def test_parse_report_command():
    assert parse_line("P report items=gb*1 -> sr1") == ParsedLine(
        actor="P",
        command="report",
        args={"items": "gb*1"},
        assign="sr1",
    )


def test_parse_void_command():
    assert parse_line("A void sr=$sr1 reason=mistake") == ParsedLine(
        actor="A",
        command="void",
        args={"sr": "$sr1", "reason": "mistake"},
        assign=None,
    )


def test_parse_show_dr_query():
    assert parse_line("show dr=$dr1") == ParsedLine(
        actor=None,
        command="show",
        args={"dr": "$dr1"},
        assign=None,
    )


def test_parse_show_sr_query():
    assert parse_line("show sr=$sr1") == ParsedLine(
        actor=None,
        command="show",
        args={"sr": "$sr1"},
        assign=None,
    )


def test_parse_stock_query():
    assert parse_line("stock partner=P") == ParsedLine(
        actor=None,
        command="stock",
        args={"partner": "P"},
        assign=None,
    )


def test_resolve_arg_variables_replaces_dr_reference():
    parsed = ParsedLine(
        actor="P",
        command="submit",
        args={"dr": "$dr1"},
        assign=None,
    )

    assert resolve_arg_variables(parsed, {"dr1": "1"}) == ParsedLine(
        actor="P",
        command="submit",
        args={"dr": "1"},
        assign=None,
    )


def test_resolve_arg_variables_replaces_sr_reference():
    parsed = ParsedLine(
        actor="A",
        command="void",
        args={"sr": "$sr1", "reason": "mistake"},
        assign=None,
    )

    assert resolve_arg_variables(parsed, {"sr1": "2"}) == ParsedLine(
        actor="A",
        command="void",
        args={"sr": "2", "reason": "mistake"},
        assign=None,
    )


def test_resolve_arg_variables_replaces_query_reference():
    parsed = ParsedLine(
        actor=None,
        command="show",
        args={"dr": "$dr1"},
        assign=None,
    )

    assert resolve_arg_variables(parsed, {"dr1": "1"}) == ParsedLine(
        actor=None,
        command="show",
        args={"dr": "1"},
        assign=None,
    )


def test_resolve_arg_variables_keeps_items_unchanged():
    parsed = ParsedLine(
        actor="P",
        command="create",
        args={"items": "gb*1;cs*2"},
        assign="dr1",
    )

    assert resolve_arg_variables(parsed, {"dr1": "1"}) == parsed


def test_resolve_arg_variables_keeps_reason_unchanged():
    parsed = ParsedLine(
        actor="A",
        command="void",
        args={"sr": "$sr1", "reason": "mistake"},
        assign=None,
    )

    assert resolve_arg_variables(parsed, {"sr1": "2"}).args["reason"] == "mistake"


def test_resolve_arg_variables_keeps_partner_unchanged():
    parsed = ParsedLine(
        actor=None,
        command="stock",
        args={"partner": "P"},
        assign=None,
    )

    assert resolve_arg_variables(parsed, {}) == parsed


def test_resolve_arg_variables_raises_on_unknown_variable():
    parsed = ParsedLine(
        actor=None,
        command="show",
        args={"dr": "$dr1"},
        assign=None,
    )

    with pytest.raises(UnknownVariableError, match="unknown variable: dr1"):
        resolve_arg_variables(parsed, {})
