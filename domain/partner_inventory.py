from domain.errors import InsufficientStock


class PartnerInventory:
    def __init__(
        self, partner_id: str, book_sku: str, current_quantity: int, version: int = 0
    ):
        self.partner_id = partner_id
        self.book_sku = book_sku
        self.current_quantity = current_quantity
        self.version = version

    def deliver(self, quantity: int):
        self.current_quantity += quantity
        self.version += 1

    def reportSale(self, quantity: int):
        if self.current_quantity < quantity:
            raise InsufficientStock(
                f"Cannot report sale of {quantity} for {self.book_sku}, only {self.current_quantity} available"
            )
        self.current_quantity -= quantity
        self.version += 1

    def restoreSales(self, quantity: int):
        self.current_quantity += quantity
        self.version += 1

    def clone(self):
        return PartnerInventory(
            partner_id=self.partner_id,
            book_sku=self.book_sku,
            current_quantity=self.current_quantity,
            version=self.version,
        )
