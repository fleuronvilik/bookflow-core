import sqlite3
from pathlib import Path

import pytest

from app.context import Context
from infra.sql.sql_audit_repo import SqlAuditRepo
from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo
from infra.sql.sql_partner_inventory_repo import SqlPartnerInventoryRepo
from infra.sql.sql_sales_report_repo import SqlSalesReportRepo
from domain.delivery_request import DeliveryRequest, Status as DRStatus
from domain.sales_report import SalesReport
from policies.identity import Actor, Role


class TestSqlDeliveryRequestRepo(SqlDeliveryRequestRepo):
    def add(self, dr: DeliveryRequest) -> int:
        return self.create(dr)

    def list_all(self) -> list[DeliveryRequest]:
        cur = self.conn.cursor()
        ids = [
            row[0]
            for row in cur.execute(
                "SELECT id FROM delivery_requests ORDER BY created_at, id"
            ).fetchall()
        ]
        return [self.get(dr_id) for dr_id in ids]

    def list_entries(self) -> list[tuple[int, DeliveryRequest]]:
        cur = self.conn.cursor()
        ids = [
            row[0]
            for row in cur.execute(
                "SELECT id FROM delivery_requests ORDER BY created_at, id"
            ).fetchall()
        ]
        return [(dr_id, self.get(dr_id)) for dr_id in ids]

    def save(self, dr: DeliveryRequest, autocommit: bool = True) -> int:
        return super().save(dr, autocommit)


class TestSqlSalesReportRepo(SqlSalesReportRepo):
    def add(self, report: SalesReport) -> int:
        report_id = self.create(report)
        if report.voided:
            self.mark_void(report_id)
        return report_id

    def list_all(self) -> list[SalesReport]:
        cur = self.conn.cursor()
        ids = [
            row[0]
            for row in cur.execute(
                "SELECT id FROM sales_reports ORDER BY created_at, id"
            ).fetchall()
        ]
        return [self.get(report_id) for report_id in ids]

    def list_entries(self) -> list[tuple[int, SalesReport]]:
        cur = self.conn.cursor()
        ids = [
            row[0]
            for row in cur.execute(
                "SELECT id FROM sales_reports ORDER BY created_at, id"
            ).fetchall()
        ]
        return [(report_id, self.get(report_id)) for report_id in ids]


@pytest.fixture
def catalog() -> set[str]:
    return {"b1", "b2", "b3", "b4"}


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")

    schema_path = (
        Path(__file__).resolve().parent.parent / "infra" / "sql" / "schema.sql"
    )
    connection.executescript(schema_path.read_text(encoding="utf-8"))

    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def dr_repo(conn) -> TestSqlDeliveryRequestRepo:
    return TestSqlDeliveryRequestRepo(conn)


@pytest.fixture
def sr_repo(conn) -> TestSqlSalesReportRepo:
    return TestSqlSalesReportRepo(conn)


@pytest.fixture
def pi_repo(conn) -> SqlPartnerInventoryRepo:
    return SqlPartnerInventoryRepo(conn)


@pytest.fixture
def audit_repo(conn) -> SqlAuditRepo:
    return SqlAuditRepo(conn)


@pytest.fixture
def ctx(catalog, dr_repo, sr_repo, pi_repo, audit_repo) -> Context:
    return Context(
        catalog,
        dr_repo,
        sr_repo,
        pi_repo,
        audit_repo,
    )


@pytest.fixture
def partner_actor() -> Actor:
    return Actor(role=Role.PARTNER, partner_id="p1")


@pytest.fixture
def admin_actor() -> Actor:
    return Actor(role=Role.ADMIN)
