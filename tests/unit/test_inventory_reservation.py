"""Unit tests for inventory reservation service.

Tests the InventoryReservation service in isolation using mocks
to verify reservation logic, lock acquisition, and error handling.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import pytest

from src.models.offer import Offer, OfferStatus, Item
from src.services.inventory_reservation import InventoryReservation, RESERVATION_TIMEOUT_SECONDS


@pytest.fixture
def mock_offer_repo():
    """Mock offer repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_lock_helper():
    """Mock Redis lock helper."""
    helper = MagicMock()
    return helper


@pytest.fixture
def sample_offer():
    """Sample offer for testing."""
    return Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Test Offer",
        items=[
            Item(name="Sandwich", quantity=10, original_price=Decimal("8.00"), discounted_price=Decimal("4.00")),
            Item(name="Salad", quantity=5, original_price=Decimal("6.00"), discounted_price=Decimal("3.00")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=4),
        status=OfferStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_reserve_items_success(mock_offer_repo, mock_lock_helper, sample_offer):
    """Test successful item reservation."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer
    mock_offer_repo.decrement_quantity.return_value = True
    
    # Mock lock context manager
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute
    item_requests = [
        {"item_name": "Sandwich", "quantity": 2},
        {"item_name": "Salad", "quantity": 1},
    ]
    
    async with service.reserve_items(sample_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is True
        assert len(reservation["items"]) == 2
        assert reservation["error"] is None
        
        # Check items reserved
        assert reservation["items"][0]["name"] == "Sandwich"
        assert reservation["items"][0]["quantity"] == 2
        assert reservation["items"][1]["name"] == "Salad"
        assert reservation["items"][1]["quantity"] == 1
    
    # Verify lock was acquired
    mock_lock_helper.acquire_offer_lock.assert_called_once_with(sample_offer.id)
    
    # Verify quantities decremented
    assert mock_offer_repo.decrement_quantity.call_count == 2


@pytest.mark.asyncio
async def test_reserve_items_insufficient_quantity(mock_offer_repo, mock_lock_helper, sample_offer):
    """Test reservation fails when insufficient quantity."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute: Request more than available (Salad only has 5)
    item_requests = [{"item_name": "Salad", "quantity": 6}]
    
    async with service.reserve_items(sample_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "Insufficient quantity" in reservation["error"]
        assert len(reservation["items"]) == 0
    
    # Verify no decrement occurred
    mock_offer_repo.decrement_quantity.assert_not_called()


@pytest.mark.asyncio
async def test_reserve_items_nonexistent_item(mock_offer_repo, mock_lock_helper, sample_offer):
    """Test reservation fails for non-existent item."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute: Request non-existent item
    item_requests = [{"item_name": "Pizza", "quantity": 1}]
    
    async with service.reserve_items(sample_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "not found in offer" in reservation["error"]
    
    mock_offer_repo.decrement_quantity.assert_not_called()


@pytest.mark.asyncio
async def test_reserve_items_expired_offer(mock_offer_repo, mock_lock_helper):
    """Test reservation fails for expired offer."""
    # Setup: Create expired offer
    expired_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Expired Offer",
        items=[
            Item(name="Bread", quantity=10, original_price=Decimal("5.00"), discounted_price=Decimal("2.50")),
        ],
        start_time=datetime.utcnow() - timedelta(hours=5),
        end_time=datetime.utcnow() - timedelta(hours=1),  # Already expired
        status=OfferStatus.ACTIVE,
    )
    
    mock_offer_repo.get_by_id.return_value = expired_offer
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute
    item_requests = [{"item_name": "Bread", "quantity": 2}]
    
    async with service.reserve_items(expired_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "expired" in reservation["error"].lower()
    
    mock_offer_repo.decrement_quantity.assert_not_called()


@pytest.mark.asyncio
async def test_reserve_items_lock_not_acquired(mock_offer_repo, mock_lock_helper, sample_offer):
    """Test reservation fails when lock cannot be acquired."""
    # Setup: Lock acquisition fails
    mock_offer_repo.get_by_id.return_value = sample_offer
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=False)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute
    item_requests = [{"item_name": "Sandwich", "quantity": 1}]
    
    async with service.reserve_items(sample_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "lock" in reservation["error"].lower()
    
    # Should not attempt to get offer or decrement
    mock_offer_repo.get_by_id.assert_not_called()
    mock_offer_repo.decrement_quantity.assert_not_called()


@pytest.mark.asyncio
async def test_reserve_items_offer_not_found(mock_offer_repo, mock_lock_helper):
    """Test reservation fails when offer doesn't exist."""
    # Setup
    mock_offer_repo.get_by_id.return_value = None
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute
    offer_id = uuid4()
    item_requests = [{"item_name": "Anything", "quantity": 1}]
    
    async with service.reserve_items(offer_id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "not found" in reservation["error"]
    
    mock_offer_repo.decrement_quantity.assert_not_called()


@pytest.mark.asyncio
async def test_reserve_items_decrement_fails(mock_offer_repo, mock_lock_helper, sample_offer):
    """Test reservation fails when decrement operation fails."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer
    mock_offer_repo.decrement_quantity.return_value = False  # Decrement fails
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute
    item_requests = [{"item_name": "Sandwich", "quantity": 2}]
    
    async with service.reserve_items(sample_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "Failed to reserve" in reservation["error"]
    
    mock_offer_repo.decrement_quantity.assert_called_once()


@pytest.mark.asyncio
async def test_release_reservation(mock_offer_repo, mock_lock_helper):
    """Test inventory release logs properly."""
    # Setup
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute
    offer_id = uuid4()
    item_requests = [{"item_name": "Sandwich", "quantity": 2}]
    
    result = await service.release_reservation(offer_id, item_requests)
    
    # Verify
    assert result is True
    # Note: Current implementation just logs; no actual increment yet


@pytest.mark.asyncio
async def test_reserve_multiple_items_validates_all(mock_offer_repo, mock_lock_helper, sample_offer):
    """Test that all items are validated before any decrement."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer
    mock_lock_helper.acquire_offer_lock.return_value.__aenter__ = AsyncMock(return_value=True)
    mock_lock_helper.acquire_offer_lock.return_value.__aexit__ = AsyncMock(return_value=None)
    
    service = InventoryReservation(mock_offer_repo, mock_lock_helper)
    
    # Execute: Second item has too much quantity requested
    item_requests = [
        {"item_name": "Sandwich", "quantity": 2},  # Valid
        {"item_name": "Salad", "quantity": 10},    # Invalid (only 5 available)
    ]
    
    async with service.reserve_items(sample_offer.id, item_requests) as reservation:
        # Verify
        assert reservation["success"] is False
        assert "Insufficient quantity" in reservation["error"]
        assert "Salad" in reservation["error"]
    
    # Verify NO decrements happened (validation failed before decrement)
    mock_offer_repo.decrement_quantity.assert_not_called()
