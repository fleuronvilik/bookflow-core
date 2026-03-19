CREATE TABLE delivery_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (partner_id IN ('p1', 'p2', 'luigi', 'mario', 'peach', 'yoshi')),
    CHECK (status IN ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'DELIVERED'))
);

CREATE TABLE delivery_request_items (
    dr_id INTEGER NOT NULL,
    book_sku TEXT NOT NULL,
    qty INTEGER NOT NULL,
    PRIMARY KEY (dr_id, book_sku),
    FOREIGN KEY (dr_id) REFERENCES delivery_requests(id) ON DELETE CASCADE,
    CHECK (qty > 0)
);

CREATE TABLE sales_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id TEXT NOT NULL,
    is_voided INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    CHECK (partner_id IN ('p1', 'p2', 'luigi', 'mario', 'peach', 'yoshi')),
    CHECK (is_voided IN (0, 1))
);

CREATE TABLE sales_report_items (
    sr_id INTEGER NOT NULL,
    book_sku TEXT NOT NULL,
    qty INTEGER NOT NULL,
    PRIMARY KEY (sr_id, book_sku),
    FOREIGN KEY (sr_id) REFERENCES sales_reports(id) ON DELETE CASCADE,
    CHECK (qty > 0)
);

CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE partner_inventories (
    book_sku TEXT NOT NULL,
    partner_id TEXT NOT NULL,
    current_quantity INTEGER NOT NULL,
    version INTEGER NOT NULL,
    PRIMARY KEY (book_sku, partner_id),
    CHECK (current_quantity >= 0),
    CHECK (version >= 0),
    CHECK (partner_id IN ('p1', 'p2', 'luigi', 'mario', 'peach', 'yoshi'))
)