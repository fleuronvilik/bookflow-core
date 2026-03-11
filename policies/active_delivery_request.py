from __future__ import annotations

from app.repositories import InMemoryDeliveryRequestRepo
from domain.delivery_request import Status
from infra.sql.sql_delivery_request_repo import SqlDeliveryRequestRepo


class ActiveDeliveryRequestExists(Exception):
    pass


ACTIVE_STATUSES = {Status.SUBMITTED, Status.APPROVED}


def ensure_no_active_delivery_request_for_partner(
    *, partner_id: str, dr_repo: SqlDeliveryRequestRepo
) -> None:
    # if hasattr(dr_repo, "list_entries"):
    #     has_active_request = any(
    #         dr.partner_id == partner_id and dr.status in ACTIVE_STATUSES
    #         for _, dr in dr_repo.list_entries()
    #     )
    # else:
    cur = dr_repo.conn.cursor()
    cur.execute(
        """
        SELECT 1
        FROM delivery_requests
        WHERE partner_id = ?
        AND status IN ('SUBMITTED', 'APPROVED')
        LIMIT 1
        """,
        (partner_id,),
    )
    has_active_request = cur.fetchone() is not None

    if has_active_request:
        raise ActiveDeliveryRequestExists("ActiveDeliveryRequestExists")
