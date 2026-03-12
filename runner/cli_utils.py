import sqlite3  # from dataclasses import dataclass
from pathlib import Path

from app.context import Context
from app.support.event_order import EventOrder 
from app.repositories import InMemoryDeliveryRequestRepo, InMemorySalesReportRepo
from app.audit import InMemoryAudit
from policies.identity import Actor, Role  # adapte

# --- Actors -------------------------------------------------


def partner(partner_id: str) -> Actor:
    return Actor(role=Role.PARTNER, partner_id=partner_id)


def admin() -> Actor:
    return Actor(role=Role.ADMIN, partner_id=None)


# --- Catalog ------------------------------------------------


def default_catalog():
    # adapte à ton type de catalogue
    return ("b1", "b2", "b3")


# --- Context ------------------------------------------------


def make_ctx(order: EventOrder = EventOrder(), catalog: tuple = default_catalog()) -> Context:
    return Context(
        catalog=catalog,
        dr_repo=InMemoryDeliveryRequestRepo(order),
        sr_repo=InMemorySalesReportRepo(order),
        audit=InMemoryAudit()
    )


# --- Pretty printing ---------------------------------------


def show_dr(id, dr) -> str:
    # suppose dr.id, dr.partner_id, dr.status existent
    return f"DR(id={id}, partner={dr.partner_id}, status={dr.status.name})"


def show_sr(id, sr) -> str:
    # suppose sr.id, sr.partner_id, sr.voided existent
    return f"SR(id={id}, partner={sr.partner_id}, voided={sr.voided})"


def step(title: str):
    print(f"\n== {title} ==")
