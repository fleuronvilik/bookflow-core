# from collections import defaultdict
from typing import List

from domain.sales_report import SalesReport


def reports_by_partner(
    reports: List[SalesReport], partner_id: str
) -> List[SalesReport]:
    return [r for r in reports if r.partner_id == partner_id]
