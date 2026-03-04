from dataclasses import dataclass
from typing import List
from .errors import InvalidReport

# class InvalidReport(Exception):
#   pass


@dataclass
class ReportItem:
    book_id: str
    quantity: int


@dataclass
class SalesReport:
    partner_id: str
    items: List[ReportItem]

    def __post_init__(self) -> None:
        if not self.partner_id:
            raise InvalidReport("partner_id is missing")

        if not self.items:
            raise InvalidReport("report must contains at least one title")

        total_quantity, min_size = 0, 2
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

        if total_quantity < min_size:
            raise InvalidReport(
                f"report minimum size is {min_size} (current size: {total_quantity})"
            )
