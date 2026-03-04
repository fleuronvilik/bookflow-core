import pytest

from domain.sales_report import SalesReport, ReportItem
from domain.errors import InvalidReport
from app.queries import reports_by_partner
from policies.validations import validate_report_items_in_catalog

def test_sales_report_rejects_non_positive_quantities():
  with pytest.raises(InvalidReport):
    SalesReport(partner_id="p1", items=[ReportItem(book_id="b1", quantity=0)])

def test_sales_report_rejects_empty_items_list():
  with pytest.raises(InvalidReport):
    SalesReport(partner_id="p1", items=[])

def test_sales_report_rejects_empty_partner_id():
  with pytest.raises(InvalidReport):
    SalesReport(partner_id="", items=[ReportItem(book_id="b1", quantity=2)])

def test_sales_report_total_quantity_lt_min_fails():
  with pytest.raises(InvalidReport):
    SalesReport(partner_id="p1", items=[ReportItem(book_id="b1", quantity=1)])

def test_sales_report_total_quantity_ge_min_succeeds():
  r1 = SalesReport(
    partner_id="p1",
    items=[
      ReportItem(book_id="b1", quantity=1),
      ReportItem(book_id="b2", quantity=3)
    ]
  )
  assert r1.partner_id == "p1"

def test_sales_report_rejects_duplicate():
  with pytest.raises(InvalidReport):
    SalesReport(
      partner_id="p1",
      items=[
        ReportItem(book_id="b1", quantity=1),
        ReportItem(book_id="b1", quantity=3)
      ]
   )

def test_validate_report_items_in_catalog():
  r1 = SalesReport(
      partner_id="p1",
      items=[
        ReportItem(book_id="b1", quantity=1),
        ReportItem(book_id="b5", quantity=3)
      ]
   )
  with pytest.raises(InvalidReport):
    validate_report_items_in_catalog(r1, {"b1"})


def test_reports_by_partner_filters():
  r1 = SalesReport(partner_id="p1", items=[ReportItem(book_id="b1", quantity=2)])
  r2 = SalesReport(partner_id="p2", items=[ReportItem(book_id="b1", quantity=2)])
  r3 = SalesReport(partner_id="p1", items=[ReportItem(book_id="b2", quantity=3)])

  got = reports_by_partner([r1, r2, r3], partner_id="p1")

  assert got == [r1, r3]
