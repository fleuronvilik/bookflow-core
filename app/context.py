# context.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.repositories import InMemorySalesReportRepo, InMemoryDeliveryRequestRepo


@dataclass(frozen=True)
class Context:
    catalog: Iterable[str]
    dr_repo: InMemoryDeliveryRequestRepo
    sr_repo: InMemorySalesReportRepo