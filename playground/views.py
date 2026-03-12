from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Iterable

from app.queries import PartnerCurrentState


PARTNERS = ("luigi", "mario", "peach")
CATALOG = (
    "ghetto-barreau",
    "reussir-mariage",
    "bien-penser",
    "connaissance-succes",
    "creer-richesse",
    "perception-divine",
    "maitriser-epargne",
    "aider-enfants",
    "servir-dieu",
)
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def catalog_entries() -> tuple[dict[str, str], ...]:
    return tuple({"slug": slug, "title": slug} for slug in CATALOG)


def list_scenarios() -> tuple[str, ...]:
    return tuple(sorted(path.name for path in SCENARIOS_DIR.glob("*.txt")))


def load_scenario(name: str) -> str:
    if name not in set(list_scenarios()):
        return ""
    return (SCENARIOS_DIR / name).read_text(encoding="utf-8")


def _empty_current_state() -> PartnerCurrentState:
    return {
        "delivery_requests": [],
        "sales_reports": [],
        "stock": [],
    }


def _render_template(template_name: str, context: dict[str, str]) -> str:
    html = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    for key, value in context.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html


def render_page(
    *,
    selected_partner: str = PARTNERS[0],
    selected_scenario: str = "",
    script: str = "",
    results: Iterable[dict[str, bool | int | None | str]] | None = None,
    current_state: PartnerCurrentState | None = None,
) -> str:
    if current_state is None:
        current_state = _empty_current_state()

    partner_options = "\n".join(
        f'<option value="{escape(partner_id)}"'
        f"{' selected' if partner_id == selected_partner else ''}>"
        f"{escape(partner_id)}</option>"
        for partner_id in PARTNERS
    )
    scenario_options = "\n".join(
        f'<option value="{escape(name)}"'
        f"{' selected' if name == selected_scenario else ''}>"
        f"{escape(name)}</option>"
        for name in list_scenarios()
    )
    catalog_html = "\n".join(
        (
            '<li class="catalog-item">'
            f'<button type="button" class="catalog-insert" data-slug="{escape(item["slug"])}">'
            f'{escape(item["slug"])}'
            "</button>"
            "</li>"
        )
        for item in catalog_entries()
    )

    results_html = ""
    if results is not None:
        lines = "\n".join(
            f"{'OK' if result['ok'] else 'ERR'} {escape(str(result['msg']))}"
            for result in results
        )
        results_html = f"<h2>Results</h2><pre>{lines or 'No output'}</pre>"

    dr_rows = "\n".join(
        (
            "<tr>"
            f"<td>{entry['id']}</td>"
            f"<td>{escape(entry['status'])}</td>"
            f"<td><code>{escape(entry['items'])}</code></td>"
            "</tr>"
        )
        for entry in current_state["delivery_requests"]
    )
    if not dr_rows:
        dr_rows = '<tr><td colspan="3" class="empty-state">No delivery requests</td></tr>'

    sr_rows = "\n".join(
        (
            "<tr>"
            f"<td>{entry['id']}</td>"
            f"<td>{'yes' if entry['voided'] else 'no'}</td>"
            f"<td><code>{escape(entry['items'])}</code></td>"
            "</tr>"
        )
        for entry in current_state["sales_reports"]
    )
    if not sr_rows:
        sr_rows = '<tr><td colspan="3" class="empty-state">No sales reports</td></tr>'

    stock_rows = "\n".join(
        (
            "<tr>"
            f"<td><code>{escape(entry['book_id'])}</code></td>"
            f"<td>{entry['quantity']}</td>"
            "</tr>"
        )
        for entry in current_state["stock"]
    )
    if not stock_rows:
        stock_rows = '<tr><td colspan="2" class="empty-state">No stock</td></tr>'

    return _render_template(
        "index.html",
        {
            "partner_options": partner_options,
            "scenario_options": scenario_options,
            "catalog_html": catalog_html,
            "script": escape(script),
            "results_html": results_html,
            "dr_rows": dr_rows,
            "sr_rows": sr_rows,
            "stock_rows": stock_rows,
            "catalog_data_json": escape(json.dumps(catalog_entries())),
        },
    )
