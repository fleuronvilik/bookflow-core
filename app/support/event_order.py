# event_order.py
from __future__ import annotations

class EventOrder:
    """Global monotonic counter used to order events across multiple repos."""
    def __init__(self) -> None:
        self._seq = 0

    def next(self) -> int:
        self._seq += 1
        return self._seq
