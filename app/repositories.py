# repositories.py
from typing import List, Tuple

from domain.sales_report import SalesReport
from domain.delivery_request import DeliveryRequest
from app.support.event_order import EventOrder


class InMemorySalesReportRepo:
    def __init__(self, order: EventOrder | None = None) -> None:
        self._order = order or EventOrder()
        self._entries: List[Tuple[int, SalesReport]] = []

    def add(self, report: SalesReport) -> int:
        count = self._order.next()
        self._entries.append((count, report))
        return count

    def list_all(self) -> list[SalesReport]:
        return [r for _, r in self._entries]

    def list_entries(self) -> list[Tuple[int, SalesReport]]:
        return list(self._entries)

    def get(self, id: int) -> SalesReport:
        [sr] = [e for k, e in self._entries if k == id]
        return sr


class InMemoryDeliveryRequestRepo:
    def __init__(self, order: EventOrder) -> None:
        self._order = order
        self._entries: List[Tuple[int, DeliveryRequest]] = []

    def add(self, dr: DeliveryRequest) -> int:
        count = self._order.next()
        self._entries.append((count, dr))
        return count

    def list_all(self) -> list[DeliveryRequest]:
        return [d for _, d in self._entries]

    def list_entries(self) -> list[Tuple[int, DeliveryRequest]]:
        return list(self._entries)

    def get(self, id: int) -> DeliveryRequest:
        [dr] = [e for k, e in self._entries if k == id]
        return dr
