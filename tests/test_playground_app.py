from __future__ import annotations

import asyncio
import json

from playground.app import get_catalog, render_page


def test_render_page_shows_catalog_sidebar_and_insert_help():
    html = render_page(script="P create items=ghetto-barreau*1")

    assert "Catalog" in html
    assert "Click a slug to insert <code>slug*1</code> into the script." in html
    assert 'data-slug="ghetto-barreau"' in html
    assert 'data-slug="connaissance-succes"' in html
    assert 'id="script"' in html


def test_catalog_endpoint_returns_slug_and_title():
    response = asyncio.run(get_catalog())

    assert response.status_code == 200
    assert json.loads(response.body)[0] == {
        "slug": "ghetto-barreau",
        "title": "ghetto-barreau",
    }


def test_render_page_shows_current_state_panels():
    html = render_page(
        current_state={
            "delivery_requests": [
                {
                    "id": 1,
                    "partner_id": "luigi",
                    "status": "DELIVERED",
                    "created_at": "2026-03-12T10:00:00+00:00",
                    "items": "ghetto-barreau*2",
                }
            ],
            "sales_reports": [
                {
                    "id": 2,
                    "partner_id": "luigi",
                    "voided": False,
                    "created_at": "2026-03-12T11:00:00+00:00",
                    "items": "ghetto-barreau*1",
                }
            ],
            "stock": [
                {
                    "book_id": "ghetto-barreau",
                    "quantity": 1,
                }
            ],
        }
    )

    assert "Current State" in html
    assert "Delivery Requests" in html
    assert "Sales Reports" in html
    assert "Stock" in html
    assert "DELIVERED" in html
    assert "ghetto-barreau*2" in html
    assert "ghetto-barreau*1" in html
