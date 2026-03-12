from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app.bootstrap import admin, make_ctx, partner
from runner import RunnerRuntime, run_lines


PARTNERS = ("luigi", "mario", "peach")
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"

app = FastAPI()


def make_runtime(partner_id: str) -> RunnerRuntime:
    ctx = make_ctx()
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


def render_page(
    *,
    selected_partner: str = PARTNERS[0],
    selected_scenario: str = "",
    script: str = "",
    results: Iterable[dict[str, bool | int | None | str]] | None = None,
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

    results_html = ""
    if results is not None:
        lines = "\n".join(
            f"{'OK' if result['ok'] else 'ERR'} {escape(str(result['msg']))}"
            for result in results
        )
        results_html = f"<h2>Results</h2><pre>{lines or 'No output'}</pre>"

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
      pre {{
        background: #f4f4f4;
        padding: 1rem;
        overflow-x: auto;
        white-space: pre-wrap;
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
      <label>
        DSL script
        <textarea name="script">{escape(script)}</textarea>
      </label>
      <button type="submit">Run</button>
    </form>
    {results_html}
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(render_page())


@app.post("/run", response_class=HTMLResponse)
async def run_script(request: Request) -> HTMLResponse:
    payload = parse_qs((await request.body()).decode("utf-8"))
    selected_partner = payload.get("partner", [PARTNERS[0]])[0] or PARTNERS[0]
    selected_scenario = payload.get("scenario", [""])[0]
    script = payload.get("script", [""])[0]
    action = payload.get("action", ["run"])[0]

    if action == "load":
        return HTMLResponse(
            render_page(
                selected_partner=selected_partner,
                selected_scenario=selected_scenario,
                script=load_scenario(selected_scenario),
            )
        )

    runtime = make_runtime(selected_partner)
    results = run_lines(runtime, script.splitlines())

    return HTMLResponse(
        render_page(
            selected_partner=selected_partner,
            selected_scenario=selected_scenario,
            script=script,
            results=results,
        )
    )
