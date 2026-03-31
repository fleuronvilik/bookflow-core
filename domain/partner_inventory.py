from dataclasses import dataclass, replace

from domain.errors import InsufficientStock


@dataclass(frozen=True)
class PartnerInventory:
    partner_id: str
    book_sku: str
    current_quantity: int
    version: int = 0

    def deliver(self, quantity: int):
        return replace(
            self,
            current_quantity=self.current_quantity + quantity,
            version=self.version + 1,
        )

    def reportSale(self, quantity: int):
        if self.current_quantity < quantity:
            raise InsufficientStock(
                f"Cannot report sale of {quantity} for {self.book_sku}, only {self.current_quantity} available"
            )
        return replace(
            self,
            current_quantity=self.current_quantity - quantity,
            version=self.version + 1,
        )

    def restoreSales(self, quantity: int):
        return replace(
            self,
            current_quantity=self.current_quantity + quantity,
            version=self.version + 1,
        )

    def clone(self):
        return PartnerInventory(
            partner_id=self.partner_id,
            book_sku=self.book_sku,
            current_quantity=self.current_quantity,
            version=self.version,
        )
