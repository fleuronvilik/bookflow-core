# delivery_request.py
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import List


class InvalidDeliveryRequest(Exception):
    pass


class InvalidTransition(Exception):
    pass


class Status(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELIVERED = "DELIVERED"


@dataclass(frozen=True)
class RequestItem:
    book_id: str
    quantity: int


@dataclass(frozen=True)
class DeliveryRequest:
    id: int | None
    partner_id: str
    status: Status
    items: List[RequestItem]

    MIN_TOTAL_QUANTITY = 2

    @classmethod
    def save_draft(
        cls, *, partner_id: str, items: List[RequestItem]
    ) -> "DeliveryRequest":
        # DR non vide dès la création (selon ton choix)
        if not partner_id:
            raise InvalidDeliveryRequest("partner_id is missing")
        if not items:
            raise InvalidDeliveryRequest(
                "delivery request must contain at least one title"
            )

        seen = set()
        total = 0
        for it in items:
            if not it.book_id:
                raise InvalidDeliveryRequest("book_id is required")
            if it.book_id in seen:
                raise InvalidDeliveryRequest(f"duplicate book_id: {it.book_id}")
            seen.add(it.book_id)

            if it.quantity <= 0:
                raise InvalidDeliveryRequest("quantity must be positive")
            total += it.quantity

        if total < cls.MIN_TOTAL_QUANTITY:
            raise InvalidDeliveryRequest(
                f"request minimum size is {cls.MIN_TOTAL_QUANTITY} (current size: {total})"
            )

        return cls(
            id=None, partner_id=partner_id, status=Status.DRAFT, items=list(items)
        )

    def mark_delivered(self) -> DeliveryRequest:
        # Invariant dominant: DELIVERED seulement si APPROVED
        if self.status is not Status.APPROVED:
            raise InvalidTransition("DELIVERED only if APPROVED")
        return replace(self, status=Status.DELIVERED)

    def approve(self) -> DeliveryRequest:
        if self.status is not Status.SUBMITTED:
            raise InvalidTransition("APPROVED only if SUBMITTED")
        return replace(self, status=Status.APPROVED)

    def submit(self) -> DeliveryRequest:
        if self.status is not Status.DRAFT:
            raise InvalidTransition("SUBMITTED only if DRAFT")
        return replace(self, status=Status.SUBMITTED)

    def reject(self) -> DeliveryRequest:
        if self.status != Status.SUBMITTED:
            raise InvalidTransition("REJECTED only if SUBMITTED")
        return replace(self, status=Status.REJECTED)

    def __str__(self):
        return self.status
