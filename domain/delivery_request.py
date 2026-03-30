from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class DeliveryRequest:
    id: int
    address: str
    items: Dict[str, int]

    def replace(self, **kwargs: Any) -> 'DeliveryRequest':
        return self.__class__(**{**self.__dict__, **kwargs})
