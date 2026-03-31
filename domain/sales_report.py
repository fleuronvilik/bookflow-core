from dataclasses import dataclass, replace
from typing import List
from .errors import InvalidReport


class AlreadyVoided(Exception):
    pass


@dataclass
class ReportItem:
    book_id: str
    quantity: int


@dataclass(frozen=True)
class SalesReport:
    id: int | None
    partner_id: str
    items: List[ReportItem]
    voided: bool = False

    MIN_TOTAL_QUANTITY = 2

    def __post_init__(self) -> None:
        if not self.partner_id:
            raise InvalidReport("partner_id is missing")

        if not self.items:
            raise InvalidReport("report must contains at least one title")

        total_quantity = 0
        books = set()

        for it in self.items:
            if not it.book_id:
                raise InvalidReport("book_id is required")

            if it.book_id in books:
                raise InvalidReport(f"duplicate book_id: {it.book_id}")
            else:
                books.add(it.book_id)

            if it.quantity <= 0:
                raise InvalidReport("quantity must be positive")
            total_quantity += it.quantity

        if total_quantity < self.MIN_TOTAL_QUANTITY:
            raise InvalidReport(
                f"report minimum size is {self.MIN_TOTAL_QUANTITY} (current size: {total_quantity})"
            )

    def void(self):
        if self.voided:
            raise AlreadyVoided("report is already voided")
        return replace(self, voided=True)
