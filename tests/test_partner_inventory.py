import pytest

from app.use_cases import submit_sales_report, void_sales_report
from domain.partner_inventory import PartnerInventory
from domain.errors import InsufficientStock
from domain.sales_report import ReportItem


def test_report_decreases_inventory_and_raises_if_insufficient(ctx):
    pi = PartnerInventory(partner_id="p1", book_sku="b1", current_quantity=10)
    ctx.pi_repo.save(pi)

    pi = pi.report_sale(4)
    ctx.pi_repo.save(pi)

    updated_pi = ctx.pi_repo.get("p1", "b1")
    assert updated_pi.current_quantity == 6

    # reporting more than available should raise
    with pytest.raises(InsufficientStock):
        pi = pi.report_sale(7)


def test_multiple_lines_atomicity(ctx, partner_actor):
    pi = PartnerInventory(
        partner_id=partner_actor.partner_id, book_sku="b1", current_quantity=10
    )
    ctx.pi_repo.save(pi)
    pi = PartnerInventory(
        partner_id=partner_actor.partner_id, book_sku="b2", current_quantity=5
    )
    ctx.pi_repo.save(pi)

    items = [ReportItem(book_id="b1", quantity=4), ReportItem(book_id="b2", quantity=6)]
    with pytest.raises(InsufficientStock):
        submit_sales_report(ctx, partner_actor, items)

    updated_pi = ctx.pi_repo.get(partner_actor.partner_id, "b1")
    assert updated_pi.current_quantity == 10  # inventory should remain unchanged
    updated_pi = ctx.pi_repo.get(partner_actor.partner_id, "b2")
    assert updated_pi.current_quantity == 5  # inventory should remain unchanged


def test_void_sales_report_restores_inventory(ctx, partner_actor, admin_actor):
    pi = PartnerInventory(partner_id="p1", book_sku="b1", current_quantity=10)
    ctx.pi_repo.save(pi)

    report_id, report = submit_sales_report(
        ctx, partner_actor, [ReportItem(book_id="b1", quantity=4)]
    )

    assert (
        ctx.pi_repo.get("p1", "b1").current_quantity == 6
    )  # inventory should be decreased

    # Simulate reporting the sale (without actually updating inventory in this test)
    # and then voiding the sales report
    void_sales_report(ctx, admin_actor, report_id, reason="test void")

    # After voiding, the inventory should be restored
    updated_pi = ctx.pi_repo.get("p1", "b1")
    assert updated_pi.current_quantity == 10  # inventory should be restored
