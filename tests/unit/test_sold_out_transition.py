"""Unit tests for sold-out transition logic.

Tests automatic and manual sold-out state transitions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4
import pytest

from src.models.offer import Offer, OfferStatus, Item
from src.services.sold_out_transition import SoldOutTransitionService


@pytest.fixture
def mock_offer_repo():
    """Mock offer repository."""
    return AsyncMock()


@pytest.fixture
def sample_offer_with_inventory():
    """Sample offer with remaining inventory."""
    return Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Test Offer",
        items=[
            Item(name="Sandwich", quantity=5, original_price=Decimal("8.00"), discounted_price=Decimal("4.00")),
            Item(name="Salad", quantity=3, original_price=Decimal("6.00"), discounted_price=Decimal("3.00")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=4),
        status=OfferStatus.ACTIVE,
    )


@pytest.fixture
def sample_offer_depleted():
    """Sample offer with all inventory depleted."""
    return Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Depleted Offer",
        items=[
            Item(name="Bagel", quantity=0, original_price=Decimal("2.00"), discounted_price=Decimal("1.00")),
            Item(name="Donut", quantity=0, original_price=Decimal("1.50"), discounted_price=Decimal("0.75")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        status=OfferStatus.ACTIVE,
    )


@pytest.mark.asyncio
async def test_transition_depleted_offer_to_sold_out(
    mock_offer_repo,
    sample_offer_depleted,
):
    """Test automatic transition when all inventory is depleted."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer_depleted
    mock_offer_repo.update_status.return_value = True
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.check_and_transition_to_sold_out(sample_offer_depleted.id)
    
    # Verify
    assert result is True
    mock_offer_repo.update_status.assert_called_once_with(
        sample_offer_depleted.id,
        OfferStatus.SOLD_OUT
    )


@pytest.mark.asyncio
async def test_no_transition_when_inventory_remains(
    mock_offer_repo,
    sample_offer_with_inventory,
):
    """Test no transition when inventory still available."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer_with_inventory
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.check_and_transition_to_sold_out(sample_offer_with_inventory.id)
    
    # Verify
    assert result is False
    mock_offer_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_no_transition_for_expired_offer(mock_offer_repo):
    """Test no transition for already expired offers."""
    # Setup: Expired offer
    expired_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Expired Offer",
        items=[
            Item(name="Cookie", quantity=0, original_price=Decimal("2.00"), discounted_price=Decimal("1.00")),
        ],
        start_time=datetime.utcnow() - timedelta(hours=5),
        end_time=datetime.utcnow() - timedelta(hours=1),
        status=OfferStatus.EXPIRED,
    )
    
    mock_offer_repo.get_by_id.return_value = expired_offer
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.check_and_transition_to_sold_out(expired_offer.id)
    
    # Verify
    assert result is False
    mock_offer_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_no_transition_for_draft_offer(mock_offer_repo):
    """Test no transition for draft offers."""
    # Setup: Draft offer
    draft_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Draft Offer",
        items=[
            Item(name="Muffin", quantity=0, original_price=Decimal("3.00"), discounted_price=Decimal("1.50")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=3),
        status=OfferStatus.DRAFT,
    )
    
    mock_offer_repo.get_by_id.return_value = draft_offer
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.check_and_transition_to_sold_out(draft_offer.id)
    
    # Verify
    assert result is False
    mock_offer_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_transition_paused_depleted_offer(mock_offer_repo):
    """Test transition works for paused offers with no inventory."""
    # Setup: Paused offer with no inventory
    paused_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Paused Depleted",
        items=[
            Item(name="Bread", quantity=0, original_price=Decimal("4.00"), discounted_price=Decimal("2.00")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        status=OfferStatus.PAUSED,
    )
    
    mock_offer_repo.get_by_id.return_value = paused_offer
    mock_offer_repo.update_status.return_value = True
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.check_and_transition_to_sold_out(paused_offer.id)
    
    # Verify
    assert result is True
    mock_offer_repo.update_status.assert_called_once()


@pytest.mark.asyncio
async def test_force_sold_out_with_inventory(
    mock_offer_repo,
    sample_offer_with_inventory,
):
    """Test manual force sold-out even with inventory remaining."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer_with_inventory
    mock_offer_repo.update_status.return_value = True
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.force_sold_out(sample_offer_with_inventory.id)
    
    # Verify
    assert result is True
    mock_offer_repo.update_status.assert_called_once_with(
        sample_offer_with_inventory.id,
        OfferStatus.SOLD_OUT
    )


@pytest.mark.asyncio
async def test_force_sold_out_already_sold_out(mock_offer_repo):
    """Test forcing sold-out on already sold-out offer is idempotent."""
    # Setup
    sold_out_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Already Sold Out",
        items=[
            Item(name="Pastry", quantity=0, original_price=Decimal("3.50"), discounted_price=Decimal("1.75")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        status=OfferStatus.SOLD_OUT,
    )
    
    mock_offer_repo.get_by_id.return_value = sold_out_offer
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.force_sold_out(sold_out_offer.id)
    
    # Verify
    assert result is True
    # Should not call update_status since already sold out
    mock_offer_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_cannot_force_sold_out_expired_offer(mock_offer_repo):
    """Test cannot force sold-out on expired offer."""
    # Setup
    expired_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Expired",
        items=[
            Item(name="Cake", quantity=2, original_price=Decimal("10.00"), discounted_price=Decimal("5.00")),
        ],
        start_time=datetime.utcnow() - timedelta(hours=4),
        end_time=datetime.utcnow() - timedelta(hours=1),
        status=OfferStatus.EXPIRED,
    )
    
    mock_offer_repo.get_by_id.return_value = expired_offer
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.force_sold_out(expired_offer.id)
    
    # Verify
    assert result is False
    mock_offer_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_cannot_force_sold_out_draft_offer(mock_offer_repo):
    """Test cannot force sold-out on draft offer."""
    # Setup
    draft_offer = Offer(
        id=uuid4(),
        business_id=uuid4(),
        title="Draft",
        items=[
            Item(name="Soup", quantity=5, original_price=Decimal("6.00"), discounted_price=Decimal("3.00")),
        ],
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=3),
        status=OfferStatus.DRAFT,
    )
    
    mock_offer_repo.get_by_id.return_value = draft_offer
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.force_sold_out(draft_offer.id)
    
    # Verify
    assert result is False
    mock_offer_repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_can_transition_check(mock_offer_repo, sample_offer_depleted):
    """Test checking if offer can transition to sold-out."""
    # Setup
    mock_offer_repo.get_by_id.return_value = sample_offer_depleted
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    can_transition, reason = await service.can_transition_to_sold_out(sample_offer_depleted.id)
    
    # Verify
    assert can_transition is True
    assert "depleted" in reason.lower() or "sold out" in reason.lower()


@pytest.mark.asyncio
async def test_check_nonexistent_offer(mock_offer_repo):
    """Test checking non-existent offer."""
    # Setup
    mock_offer_repo.get_by_id.return_value = None
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    can_transition, reason = await service.can_transition_to_sold_out(uuid4())
    
    # Verify
    assert can_transition is False
    assert "not found" in reason.lower()


@pytest.mark.asyncio
async def test_transition_handles_repository_error(mock_offer_repo):
    """Test transition handles repository errors gracefully."""
    # Setup
    mock_offer_repo.get_by_id.side_effect = Exception("Database error")
    
    service = SoldOutTransitionService(mock_offer_repo)
    
    # Execute
    result = await service.check_and_transition_to_sold_out(uuid4())
    
    # Verify
    assert result is False
