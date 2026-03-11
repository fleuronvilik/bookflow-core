# import os
# os.chdir("/home/vilfleur/python_playground/book_depot")

from app.bootstrap import admin, make_ctx, partner
from runner import *


def make_runtime() -> RunnerRuntime:
    return RunnerRuntime(
        ctx=make_ctx(),
        partner_id="luigi",
        partner_actor=partner("luigi"),
        admin_actor=admin(),
    )


bpmr = make_runtime()


# lc = parse_line("P create items=b1*3 -> dr1")
# print(run_create(bpmr, lc))
