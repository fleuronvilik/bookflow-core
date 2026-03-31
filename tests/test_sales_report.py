import pytest

from domain.sales_report import SalesReport, ReportItem
from domain.errors import InvalidReport
from policies.validations import validate_report_items_in_catalog
from tests.helpers import default_sales


def test_sales_report_rejects_non_positive_quantities():
    with pytest.raises(InvalidReport):
        SalesReport(
            id=None, partner_id="p1", items=[ReportItem(book_id="b1", quantity=0)]
        )


def test_sales_report_rejects_empty_items_list():
    with pytest.raises(InvalidReport):
        SalesReport(id=None, partner_id="p1", items=[])


def test_sales_report_rejects_empty_partner_id():
    with pytest.raises(InvalidReport):
        SalesReport(id=None, partner_id="", items=default_sales())


def test_sales_report_total_quantity_lt_min_fails():
    with pytest.raises(InvalidReport):
        SalesReport(
            id=None, partner_id="p1", items=[ReportItem(book_id="b1", quantity=1)]
        )


def test_sales_report_total_quantity_ge_min_succeeds():
    r1 = SalesReport(
        id=None,
        partner_id="p1",
        items=[
            ReportItem(book_id="b1", quantity=1),
            ReportItem(book_id="b2", quantity=3),
        ],
    )
    assert r1.partner_id == "p1"


def test_sales_report_rejects_duplicate():
    with pytest.raises(InvalidReport):
        SalesReport(
            id=None,
            partner_id="p1",
            items=[
                ReportItem(book_id="b1", quantity=1),
                ReportItem(book_id="b1", quantity=3),
            ],
        )


def test_validate_report_items_in_catalog():
    r1 = SalesReport(
        id=None,
        partner_id="p1",
        items=[
            ReportItem(book_id="b1", quantity=1),
            ReportItem(book_id="b5", quantity=3),
        ],
    )
    with pytest.raises(InvalidReport):
        validate_report_items_in_catalog(r1, {"b1"})
