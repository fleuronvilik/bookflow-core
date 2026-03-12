from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.bootstrap import admin, make_ctx, partner
from app.queries import PartnerCurrentState, get_partner_current_state
from runner import RunnerRuntime, run_lines


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

app = FastAPI()


def make_runtime(partner_id: str) -> RunnerRuntime:
    ctx = make_ctx(False, CATALOG)
    return RunnerRuntime(
        ctx=ctx,
        partner_id=partner_id,
        partner_actor=partner(partner_id),
        admin_actor=admin(),
    )


def list_scenarios() -> tuple[str, ...]:
    return tuple(sorted(path.name for path in SCENARIOS_DIR.glob("*.txt")))


def load_scenario(name: str) -> str:
    if name not in set(list_scenarios()):
        return ""
    return (SCENARIOS_DIR / name).read_text(encoding="utf-8")


def catalog_entries() -> tuple[dict[str, str], ...]:
    return tuple({"slug": slug, "title": slug} for slug in CATALOG)


def render_page(
    *,
    selected_partner: str = PARTNERS[0],
    selected_scenario: str = "",
    script: str = "",
    results: Iterable[dict[str, bool | int | None | str]] | None = None,
    current_state: PartnerCurrentState | None = None,
) -> str:
    partner_options = "\n".join(
        f"<option value=\"{escape(partner_id)}\""
        f"{' selected' if partner_id == selected_partner else ''}>"
        f"{escape(partner_id)}</option>"
        for partner_id in PARTNERS
    )
    scenario_options = "\n".join(
        f"<option value=\"{escape(name)}\""
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

    if current_state is None:
        current_state = {
            "delivery_requests": [],
            "sales_reports": [],
            "stock": [],
        }

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

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Book Depot Playground</title>
    <style>
      body {{
        font-family: sans-serif;
        margin: 2rem auto;
        max-width: 960px;
        padding: 0 1rem;
      }}
      form {{
        display: grid;
        gap: 1rem;
      }}
      .toolbar {{
        display: grid;
        gap: 1rem;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        align-items: end;
      }}
      .scenario-controls {{
        display: flex;
        gap: 0.75rem;
        align-items: end;
      }}
      .scenario-controls label {{
        flex: 1;
      }}
      .main-grid {{
        display: grid;
        gap: 1rem;
        grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
        align-items: start;
      }}
      .panel {{
        border: 1px solid #d9d9d9;
        background: #fafafa;
        padding: 1rem;
        border-radius: 0.5rem;
      }}
      .placeholder {{
        color: #666;
      }}
      .catalog-help {{
        color: #666;
        font-size: 0.95rem;
        margin: 0.5rem 0 1rem;
      }}
      .catalog-list {{
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 0.5rem;
      }}
      .catalog-item {{
        margin: 0;
      }}
      .catalog-insert {{
        width: 100%;
        text-align: left;
        padding: 0.6rem 0.75rem;
        border: 1px solid #d9d9d9;
        border-radius: 0.4rem;
        background: #fff;
        cursor: pointer;
      }}
      label {{
        display: grid;
        gap: 0.5rem;
        font-weight: 600;
      }}
      select,
      textarea,
      button {{
        font: inherit;
      }}
      textarea {{
        min-height: 20rem;
        padding: 0.75rem;
      }}
      button {{
        width: fit-content;
        padding: 0.75rem 1.25rem;
      }}
      textarea {{
        width: 100%;
        box-sizing: border-box;
      }}
      pre {{
        background: #f4f4f4;
        padding: 1rem;
        overflow-x: auto;
        white-space: pre-wrap;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
      }}
      th,
      td {{
        border-top: 1px solid #e3e3e3;
        padding: 0.65rem 0.5rem;
        text-align: left;
        vertical-align: top;
      }}
      th {{
        border-top: 0;
      }}
      .state-grid {{
        display: grid;
        gap: 1rem;
      }}
      .state-section h2 {{
        margin: 0 0 0.75rem;
        font-size: 1rem;
      }}
      .empty-state {{
        color: #666;
      }}
      @media (max-width: 800px) {{
        .main-grid {{
          grid-template-columns: 1fr;
        }}
      }}
    </style>
  </head>
  <body>
    <h1>Book Depot Playground</h1>
    <form method="post" action="/run">
      <div class="toolbar">
        <label>
          Partner
          <select name="partner">
            {partner_options}
          </select>
        </label>
        <div class="scenario-controls">
          <label>
            Scenario
            <select name="scenario">
              <option value="">Select a scenario</option>
              {scenario_options}
            </select>
          </label>
          <button type="submit" name="action" value="load">Load</button>
        </div>
      </div>
      <div class="main-grid">
        <aside class="panel">
          <strong>Catalog</strong>
          <p class="catalog-help">Click a slug to insert <code>slug*1</code> into the script.</p>
          <ul class="catalog-list">
            {catalog_html}
          </ul>
        </aside>
        <section>
          <label>
            DSL script
            <textarea id="script" name="script">{escape(script)}</textarea>
          </label>
          <button type="submit" name="action" value="run">Run</button>
        </section>
      </div>
    </form>
    {results_html}
    <section class="panel state-section">
      <strong>Current State</strong>
      <div class="state-grid">
        <section>
          <h2>Delivery Requests</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Status</th>
                <th>Items</th>
              </tr>
            </thead>
            <tbody>
              {dr_rows}
            </tbody>
          </table>
        </section>
        <section>
          <h2>Sales Reports</h2>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Voided</th>
                <th>Items</th>
              </tr>
            </thead>
            <tbody>
              {sr_rows}
            </tbody>
          </table>
        </section>
        <section>
          <h2>Stock</h2>
          <table>
            <thead>
              <tr>
                <th>Book</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {stock_rows}
            </tbody>
          </table>
        </section>
      </div>
    </section>
    <script id="catalog-data" type="application/json">{escape(json.dumps(catalog_entries()))}</script>
    <script>
      const catalogDataNode = document.getElementById("catalog-data");
      const scriptField = document.getElementById("script");

      function insertCatalogSlug(slug) {{
        if (!scriptField) {{
          return;
        }}

        const token = `${{slug}}*1`;
        const currentValue = scriptField.value;
        scriptField.value = currentValue ? `${{currentValue}}\\n${{token}}` : token;
        scriptField.focus();
      }}

      document.querySelectorAll(".catalog-insert").forEach((button) => {{
        button.addEventListener("click", () => {{
          insertCatalogSlug(button.dataset.slug || "");
        }});
      }});
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    ctx = make_ctx(False, CATALOG)
    return HTMLResponse(
        render_page(
            current_state=get_partner_current_state(ctx, PARTNERS[0]),
        )
    )


@app.get("/catalog", response_class=JSONResponse)
async def get_catalog() -> JSONResponse:
    return JSONResponse(catalog_entries())


@app.post("/run", response_class=HTMLResponse)
async def run_script(request: Request) -> HTMLResponse:
    payload = parse_qs((await request.body()).decode("utf-8"))
    selected_partner = payload.get("partner", [PARTNERS[0]])[0] or PARTNERS[0]
    selected_scenario = payload.get("scenario", [""])[0]
    script = payload.get("script", [""])[0]
    action = payload.get("action", ["run"])[0]
    ctx = make_ctx(False, CATALOG)

    if action == "load":
        return HTMLResponse(
            render_page(
                selected_partner=selected_partner,
                selected_scenario=selected_scenario,
                script=load_scenario(selected_scenario),
                current_state=get_partner_current_state(ctx, selected_partner),
            )
        )

    runtime = RunnerRuntime(
        ctx=ctx,
        partner_id=selected_partner,
        partner_actor=partner(selected_partner),
        admin_actor=admin(),
    )
    results = run_lines(runtime, script.splitlines())

    return HTMLResponse(
        render_page(
            selected_partner=selected_partner,
            selected_scenario=selected_scenario,
            script=script,
            results=results,
            current_state=get_partner_current_state(ctx, selected_partner),
        )
    )
