from __future__ import annotations

from app.queries import get_partner_current_state
from domain.delivery_request import RequestItem, Status as DRStatus
from domain.sales_report import ReportItem
from tests.helpers import given_dr, given_sr


def test_get_partner_current_state_reads_delivery_requests_sales_reports_and_stock(ctx):
    given_dr(
        ctx,
        "p1",
        DRStatus.DELIVERED,
        items=[
            RequestItem(book_id="b1", quantity=2),
            RequestItem(book_id="b2", quantity=1),
        ],
    )
    given_dr(
        ctx,
        "p2",
        DRStatus.DELIVERED,
        items=[RequestItem(book_id="b3", quantity=4)],
    )
    given_sr(
        ctx,
        "p1",
        items=[ReportItem(book_id="b1", quantity=1), ReportItem(book_id="b2", quantity=1)],
    )

    state = get_partner_current_state(ctx, "p1")

    assert len(state["delivery_requests"]) == 1
    assert state["delivery_requests"][0]["status"] == "DELIVERED"
    assert state["delivery_requests"][0]["items"] == "b1*2;b2*1"

    assert len(state["sales_reports"]) == 1
    assert state["sales_reports"][0]["voided"] is False
    assert state["sales_reports"][0]["items"] == "b1*1;b2*1"

    assert state["stock"] == [
        {"book_id": "b1", "quantity": 1},
        {"book_id": "b2", "quantity": 0},
    ]
