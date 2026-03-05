# conftest.py
import pytest

from app.support.event_order import EventOrder
from app.repositories import InMemorySalesReportRepo, InMemoryDeliveryRequestRepo
from app.context import Context
from policies.identity import Actor, Role
from app.audit import InMemoryAudit


@pytest.fixture
def catalog() -> set[str]:
    # Catalogue global "par défaut" pour la majorité des tests
    return {"b1", "b2", "b3", "b4"}


@pytest.fixture
def order() -> EventOrder:
    # Ordre partagé DR/SR (pour ReportRequired)
    return EventOrder()


@pytest.fixture
def dr_repo(order: EventOrder) -> InMemoryDeliveryRequestRepo:
    return InMemoryDeliveryRequestRepo(order=order)


@pytest.fixture
def sr_repo(order: EventOrder) -> InMemorySalesReportRepo:
    # IMPORTANT : partage le même order que dr_repo
    return InMemorySalesReportRepo(order=order)


@pytest.fixture
def ctx(catalog, dr_repo, sr_repo) -> Context:
    return Context(catalog, dr_repo, sr_repo, InMemoryAudit())


@pytest.fixture
def partner_actor() -> Actor:
    return Actor(role=Role.PARTNER, partner_id="p1")


@pytest.fixture
def admin_actor() -> Actor:
    return Actor(role=Role.ADMIN)
