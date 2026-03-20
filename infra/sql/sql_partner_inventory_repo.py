from domain.partner_inventory import PartnerInventory


class SqlPartnerInventoryRepo:
    def __init__(self, conn):
        self.conn = conn

    def save(self, partner_inventory, autocommit=True):
        cur = self.conn.cursor()
        # pi = self.get(partner_inventory.partner_id, partner_inventory.book_sku)

        cur.execute(
            """
            INSERT INTO partner_inventories (partner_id, book_sku, current_quantity, version)
            VALUES (?, ?, ?, ?) ON CONFLICT (partner_id, book_sku) DO UPDATE
            SET current_quantity = excluded.current_quantity, version = excluded.version
        """,
            (
                partner_inventory.partner_id,
                partner_inventory.book_sku,
                partner_inventory.current_quantity,
                partner_inventory.version,
            ),
        )
        if autocommit:
            self.conn.commit()

    def get(self, partner_id, book_sku):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT partner_id, book_sku, current_quantity, version
            FROM partner_inventories
            WHERE partner_id = ? AND book_sku = ?
        """,
            (partner_id, book_sku),
        )
        row = cur.fetchone()
        if row:
            return PartnerInventory(
                partner_id=row[0],
                book_sku=row[1],
                current_quantity=row[2],
                version=row[3],
            )
        else:
            return None
