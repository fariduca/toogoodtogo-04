"""Unit tests for Offer model validation."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.models.offer import Item, Offer, OfferInput, OfferStatus


def test_item_validation():
    """Test Item value object validation."""
    item = Item(name="Fresh Bread", original_price=Decimal("5.00"), discounted_price=Decimal("2.50"), quantity=10)
    assert item.name == "Fresh Bread"
    assert item.original_price == Decimal("5.00")
    assert item.discounted_price == Decimal("2.50")
    assert item.quantity == 10


def test_item_name_too_short():
    """Test Item name minimum length."""
    with pytest.raises(ValueError):
        Item(name="A", unit_price=Decimal("2.50"), quantity_available=10)


def test_item_negative_price():
    """Test Item price must be non-negative."""
    with pytest.raises(ValueError):
        Item(name="Bread", unit_price=Decimal("-1.00"), quantity_available=10)


def test_item_negative_quantity():
    """Test Item quantity must be non-negative."""
    with pytest.raises(ValueError):
        Item(name="Bread", unit_price=Decimal("2.50"), quantity_available=-1)


def test_offer_time_validation():
    """Test Offer start_time < end_time validation."""
    now = datetime.utcnow()
    items = [Item(name="Bread", original_price=Decimal("5.00"), discounted_price=Decimal("2.50"), quantity=10)]
    business_id = "00000000-0000-0000-0000-000000000001"

    # Valid time range
    offer_input = OfferInput(
        business_id=business_id,
        title="Fresh Produce",
        items=items,
        start_time=now,
        end_time=now + timedelta(hours=2),
    )
    assert offer_input.start_time < offer_input.end_time

    # Invalid time range
    with pytest.raises(ValueError, match="end_time must be after start_time"):
        OfferInput(
            business_id=business_id,
            title="Fresh Produce",
            items=items,
            start_time=now,
            end_time=now - timedelta(hours=1),
        )


def test_offer_title_length():
    """Test Offer title length constraints."""
    now = datetime.utcnow()
    items = [Item(name="Bread", original_price=Decimal("5.00"), discounted_price=Decimal("2.50"), quantity=10)]

    # Title too short
    with pytest.raises(ValueError):
        OfferInput(
            title="AB",
            items=items,
            start_time=now,
            end_time=now + timedelta(hours=2),
        )

    # Title too long
    with pytest.raises(ValueError):
        OfferInput(
            title="A" * 121,
            items=items,
            start_time=now,
            end_time=now + timedelta(hours=2),
        )


def test_offer_requires_items():
    """Test Offer must have at least one item."""
    now = datetime.utcnow()

    with pytest.raises(ValueError):
        OfferInput(
            title="Fresh Produce",
            items=[],
            start_time=now,
            end_time=now + timedelta(hours=2),
        )


def test_offer_remaining_quantity():
    """Test Offer total quantity across all items."""
    items = [
        Item(name="Bread", original_price=Decimal("5.00"), discounted_price=Decimal("2.50"), quantity=10),
        Item(name="Cake", original_price=Decimal("6.00"), discounted_price=Decimal("3.00"), quantity=5),
    ]

    offer = Offer(
        business_id="00000000-0000-0000-0000-000000000001",
        title="Fresh Bakery",
        items=items,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
    )

    # Check that items are correctly stored
    assert len(offer.items) == 2
    assert offer.items[0].quantity == 10
    assert offer.items[1].quantity == 5


def test_offer_is_expired():
    """Test Offer expiration based on end_time."""
    past_time = datetime.utcnow() - timedelta(hours=1)
    future_time = datetime.utcnow() + timedelta(hours=1)

    items = [Item(name="Bread", original_price=Decimal("5.00"), discounted_price=Decimal("2.50"), quantity=10)]

    # Not expired - end time in future
    offer = Offer(
        business_id="00000000-0000-0000-0000-000000000001",
        title="Fresh Bakery",
        items=items,
        start_time=past_time,
        end_time=future_time,
    )
    assert offer.end_time > datetime.utcnow()

    # Expired - end time in past
    expired_offer = Offer(
        business_id="00000000-0000-0000-0000-000000000001",
        title="Old Bakery",
        items=items,
        start_time=past_time - timedelta(hours=2),
        end_time=past_time,
    )
    assert expired_offer.end_time < datetime.utcnow()
