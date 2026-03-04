# report_required.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from domain.delivery_request import DeliveryRequest, Status as DRStatus
from domain.sales_report import SalesReport


class ReportRequired(Exception):
    pass


def ensure_report_submitted_since_last_delivery(
    *,
    partner_id: str,
    dr_entries: Iterable[Tuple[int, DeliveryRequest]],
    sr_entries: Iterable[Tuple[int, SalesReport]],
) -> None:
    """
    Rule:
      - If no delivered DR exists for partner -> allow
      - Else require at least one SR for partner with seq > last_delivered_seq
    """
    last_delivered_seq: Optional[int] = None
    for seq, dr in dr_entries:
        if getattr(dr, "partner_id", None) == partner_id and dr.status is DRStatus.DELIVERED:
            last_delivered_seq = seq

    if last_delivered_seq is None:
        return  # first delivery cycle: no report required

    for seq, sr in sr_entries:
        if sr.partner_id == partner_id and seq > last_delivered_seq:
            return

    raise ReportRequired("sales report required since last delivered delivery request")