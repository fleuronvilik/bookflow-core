import sqlite3
from pathlib import Path
from typing import Iterable

from app.audit import InMemoryAudit
from app.context import Context
from infra.sql.sql_audit_repo import SqlAuditRepo
from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo
from infra.sql.sql_sales_report_repo import SqlSalesReportRepo
from policies.identity import Actor, Role


def partner(partner_id: str) -> Actor:
    return Actor(role=Role.PARTNER, partner_id=partner_id)


def admin() -> Actor:
    return Actor(role=Role.ADMIN, partner_id=None)


def default_catalog() -> tuple[str, ...]:
    return ("b1", "b2", "b3")


def make_ctx(
    testing: bool = False,
    catalog: Iterable[str] | None = None,
) -> Context:
    if catalog is None or not all(isinstance(book_id, str) for book_id in catalog):
        catalog = default_catalog()

    if testing:
        conn = sqlite3.connect(":memory:")
    else:
        db_path = Path(__file__).resolve().parent.parent / "bookflow.db"
        conn = sqlite3.connect(db_path)

    conn.execute("PRAGMA foreign_keys = ON")

    already_initialized = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'delivery_requests'
        """
    ).fetchone()
    if not already_initialized:
        schema_path = (
            Path(__file__).resolve().parent.parent / "infra" / "sql" / "schema.sql"
        )
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()

    return Context(
        catalog=catalog,
        dr_repo=SqlDeliveryRequestRepo(conn),
        sr_repo=SqlSalesReportRepo(conn),
        audit=SqlAuditRepo(conn),
    )


def show_dr(id, dr) -> str:
    return f"DR(id={id}, partner={dr.partner_id}, status={dr.status.name})"


def show_sr(id, sr) -> str:
    return f"SR(id={id}, partner={sr.partner_id}, voided={sr.voided})"


def step(title: str):
    print(f"\n== {title} ==")
