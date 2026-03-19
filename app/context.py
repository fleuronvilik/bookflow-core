# context.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# from app.repositories import InMemorySalesReportRepo  # , InMemoryDeliveryRequestRepo
# from app.audit import InMemoryAudit
from infra.sql.sql_audit_repo import SqlAuditRepo
from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo
from infra.sql.sql_partner_inventory_repo import SqlPartnerInventoryRepo
from infra.sql.sql_sales_report_repo import SqlSalesReportRepo


@dataclass(frozen=True)
class Context:
    catalog: Iterable[str]
    dr_repo: SqlDeliveryRequestRepo
    sr_repo: SqlSalesReportRepo
    pi_repo: SqlPartnerInventoryRepo
    audit: SqlAuditRepo
