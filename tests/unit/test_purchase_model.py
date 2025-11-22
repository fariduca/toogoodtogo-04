"""Unit tests for Purchase model validation."""

from decimal import Decimal

import pytest

from src.models.purchase import Purchase, PurchaseItem, PurchaseRequest, PurchaseStatus


def test_purchase_item_validation():
    """Test PurchaseItem value object validation."""
    item = PurchaseItem(
        name="Fresh Bread", quantity=2, unit_price=Decimal("2.50")
    )
    assert item.name == "Fresh Bread"
    assert item.quantity == 2
    assert item.unit_price == Decimal("2.50")


def test_purchase_item_quantity_positive():
    """Test PurchaseItem quantity must be positive."""
    with pytest.raises(ValueError):
        PurchaseItem(item_name="Bread", quantity=0, unit_price=Decimal("2.50"))

    with pytest.raises(ValueError):
        PurchaseItem(item_name="Bread", quantity=-1, unit_price=Decimal("2.50"))


def test_purchase_total_validation():
    """Test Purchase total_amount matches item selections."""
    items = [
        PurchaseItem(name="Bread", quantity=2, unit_price=Decimal("2.50")),
        PurchaseItem(name="Cake", quantity=1, unit_price=Decimal("3.00")),
    ]

    # Correct total
    purchase = Purchase(
        offer_id="00000000-0000-0000-0000-000000000001",
        customer_id=123456789,  # Telegram user ID
        item_selections=items,
        total_amount=Decimal("8.00"),  # 2*2.50 + 1*3.00
    )
    assert purchase.total_amount == Decimal("8.00")

    # Incorrect total
    with pytest.raises(ValueError, match="total_amount .* does not match calculated total"):
        Purchase(
            offer_id="00000000-0000-0000-0000-000000000001",
            customer_id="00000000-0000-0000-0000-000000000002",
            item_selections=items,
            total_amount=Decimal("10.00"),  # Wrong
        )


def test_purchase_request_validation():
    """Test PurchaseRequest validation."""
    # Valid request
    request = PurchaseRequest(
        items=[
            {"item_name": "Bread", "quantity": 2},
            {"item_name": "Pastry", "quantity": 1},
        ]
    )
    assert len(request.items) == 2

    # Missing item_name
    with pytest.raises(ValueError, match="item_name and quantity"):
        PurchaseRequest(items=[{"quantity": 2}])

    # Missing quantity
    with pytest.raises(ValueError, match="item_name and quantity"):
        PurchaseRequest(items=[{"item_name": "Bread"}])

    # Invalid quantity
    with pytest.raises(ValueError, match="positive integer"):
        PurchaseRequest(items=[{"item_name": "Bread", "quantity": 0}])

    # Empty items list
    with pytest.raises(ValueError):
        PurchaseRequest(items=[])


def test_purchase_status_transitions():
    """Test Purchase status enum."""
    assert PurchaseStatus.PENDING.value == "pending"
    assert PurchaseStatus.CONFIRMED.value == "confirmed"
    assert PurchaseStatus.CANCELED.value == "canceled"
