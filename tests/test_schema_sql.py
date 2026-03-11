import pytest


def test_schema_loads(ctx):
    cur = ctx.dr_repo.conn.cursor()

    tables = cur.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        """
    ).fetchall()

    table_names = {t[0] for t in tables}

    assert "delivery_requests" in table_names
    assert "delivery_request_items" in table_names
    assert "sales_reports" in table_names
    assert "sales_report_items" in table_names
    assert "audit_events" in table_names


def test_fk_enforced(ctx):
    cur = ctx.dr_repo.conn.cursor()

    with pytest.raises(Exception):
        cur.execute(
            """
            INSERT INTO delivery_request_items (dr_id, book_sku, qty)
            VALUES (999, 'bookA', 2)
            """
        )


def test_no_duplicate_items(ctx):
    cur = ctx.dr_repo.conn.cursor()

    cur.execute(
        """
        INSERT INTO delivery_requests (partner_id, status, created_at)
        VALUES ('luigi', 'DRAFT', '2026-01-01T00:00:00Z')
        """
    )

    dr_id = cur.lastrowid

    cur.execute(
        """
        INSERT INTO delivery_request_items (dr_id, book_sku, qty)
        VALUES (?, 'bookA', 2)
        """,
        (dr_id,),
    )

    with pytest.raises(Exception):
        cur.execute(
            """
            INSERT INTO delivery_request_items (dr_id, book_sku, qty)
            VALUES (?, 'bookA', 5)
            """,
            (dr_id,),
        )
