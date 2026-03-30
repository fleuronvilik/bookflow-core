import pytest

from domain.delivery_request import (
    DeliveryRequest,
    RequestItem,
    InvalidTransition,
    Status,
    InvalidDeliveryRequest,
)


@pytest.mark.parametrize(
    "start_status",
    [
        Status.DRAFT,
        Status.SUBMITTED,
        Status.DELIVERED,
        Status.REJECTED,
    ],
)
def test_mark_delivered_allowed_only_from_approved(start_status):
    dr = make_dr(start_status)
    with pytest.raises(InvalidTransition, match="only if APPROVED"):
        dr.mark_delivered()


def test_mark_delivered_transitions_approved_to_delivered():
    dr = make_dr(Status.APPROVED)
    dr = dr.mark_delivered()
    assert dr.status == Status.DELIVERED


@pytest.mark.parametrize(
    "start_status", [Status.DRAFT, Status.APPROVED, Status.DELIVERED, Status.REJECTED]
)
def test_approve_allowed_only_from_submitted(start_status):
    dr = make_dr(start_status)
    with pytest.raises(InvalidTransition, match=r"only if SUBMITTED"):
        dr.approve()


def test_approve_transitions_submitted_to_approved():
    dr = make_dr(Status.SUBMITTED)
    dr = dr.approve()
    assert dr.status == Status.APPROVED


@pytest.mark.parametrize(
    "start_status",
    [Status.SUBMITTED, Status.APPROVED, Status.DELIVERED, Status.REJECTED],
)
def test_submit_allowed_only_from_draft(start_status):
    dr = make_dr(start_status)
    with pytest.raises(InvalidTransition, match=r"only if DRAFT"):
        dr.submit()


def test_submit_transitions_draft_to_submitted():
    dr = make_dr(Status.DRAFT)
    dr = dr.submit()
    assert dr.status == Status.SUBMITTED


def test_save_draft_requires_partner_id():
    with pytest.raises(InvalidDeliveryRequest, match=r"partner_id is missing"):
        DeliveryRequest.save_draft(
            partner_id="",
            items=[RequestItem("b1", 2)],
        )


def test_save_draft_requires_at_least_one_item():
    with pytest.raises(InvalidDeliveryRequest, match=r"at least one title"):
        DeliveryRequest.save_draft(
            partner_id="p1",
            items=[],
        )


def test_save_draft_requires_all_item_book_ids_present():
    with pytest.raises(InvalidDeliveryRequest, match=r"book_id is required"):
        DeliveryRequest.save_draft(
            partner_id="p1",
            items=[RequestItem("", 1)],
        )


def test_save_draft_rejects_duplicate_book_ids():
    with pytest.raises(InvalidDeliveryRequest, match=r"duplicate book_id"):
        DeliveryRequest.save_draft(
            partner_id="p1",
            items=[RequestItem("b1", 1), RequestItem("b1", 2)],
        )


def test_save_draft_requires_positive_quantities():
    with pytest.raises(InvalidDeliveryRequest, match=r"quantity must be positive"):
        DeliveryRequest.save_draft(
            partner_id="p1",
            items=[RequestItem("b1", 0)],
        )


def test_save_draft_requires_min_total_copies():
    # On met exprès une taille "trop petite". Ajuste selon MIN_TOTAL_QUANTITY si besoin.
    with pytest.raises(InvalidDeliveryRequest, match=r"request minimum size is"):
        DeliveryRequest.save_draft(
            partner_id="p1",
            items=[RequestItem("b1", 1)],
        )


def test_save_draft_happy_path():
    dr = DeliveryRequest.save_draft(
        partner_id="p1",
        items=[RequestItem("b1", 1), RequestItem("b2", 1)],
    )
    assert dr.partner_id == "p1"
    assert dr.status == Status.DRAFT  # ou dr.status.value == "DRAFT" selon ton impl
    assert len(dr.items) == 2


""" Helpers """


def make_dr(status: Status) -> DeliveryRequest:
    return DeliveryRequest(
        id=1, partner_id="p1", status=status, items=[RequestItem("b1", 2)]
    )
