from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.bootstrap import admin, make_ctx, partner
from app.queries import get_partner_current_state
from runner import RunnerRuntime, run_lines

from playground.views import (
    CATALOG,
    PARTNERS,
    catalog_entries,
    load_scenario,
    render_page as render_playground_page,
)


app = FastAPI()


def _make_runtime(partner_id: str, testing: bool = False) -> RunnerRuntime:
    ctx = make_ctx(testing, CATALOG)
    return RunnerRuntime(
        ctx=ctx,
        partner_id=partner_id,
        partner_actor=partner(partner_id),
        admin_actor=admin(),
    )


def _render_index(
    *,
    selected_partner: str = PARTNERS[0],
    selected_scenario: str = "",
    script: str = "",
    results: list[dict[str, bool | int | None | str]] | None = None,
) -> HTMLResponse:
    runtime = _make_runtime(selected_partner)
    return HTMLResponse(
        render_playground_page(
            selected_partner=selected_partner,
            selected_scenario=selected_scenario,
            script=script,
            results=results,
            current_state=get_partner_current_state(runtime.ctx, selected_partner),
        )
    )


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return _render_index()


@app.get("/catalog", response_class=JSONResponse)
async def get_catalog() -> JSONResponse:
    return JSONResponse(catalog_entries())


@app.get("/current-state", response_class=JSONResponse)
async def get_current_state(partner_id: str = PARTNERS[0]) -> JSONResponse:
    runtime = _make_runtime(partner_id if partner_id in PARTNERS else PARTNERS[0])
    return JSONResponse(get_partner_current_state(runtime.ctx, runtime.partner_id))


@app.post("/run", response_class=HTMLResponse)
async def run_script(request: Request) -> HTMLResponse:
    payload = parse_qs((await request.body()).decode("utf-8"))
    selected_partner = payload.get("partner", [PARTNERS[0]])[0] or PARTNERS[0]
    selected_scenario = payload.get("scenario", [""])[0]
    script = payload.get("script", [""])[0]
    action = payload.get("action", ["run"])[0]

    if action == "load":
        return _render_index(
            selected_partner=selected_partner,
            selected_scenario=selected_scenario,
            script=load_scenario(selected_scenario),
        )

    runtime = _make_runtime(selected_partner)
    results = run_lines(runtime, script.splitlines())
    return _render_index(
        selected_partner=selected_partner,
        selected_scenario=selected_scenario,
        script=script,
        results=results,
    )


render_page = render_playground_page
