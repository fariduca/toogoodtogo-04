"""Unit tests for discovery ranking service."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.models.offer import Item, Offer
from src.services.discovery_ranking import DiscoveryRankingService


@pytest.mark.asyncio
async def test_discovery_rank_by_latest():
    """Test offers ranked by creation time (latest first)."""
    service = DiscoveryRankingService()

    now = datetime.utcnow()
    items = [Item(name="Bread", original_price=Decimal("5.00"), discounted_price=Decimal("2.50"), quantity=10)]

    offers = [
        Offer(
            business_id=uuid4(),
            title="Offer 1",
            items=items,
            start_time=now,
            end_time=now + timedelta(hours=2),
            created_at=now - timedelta(hours=3),
        ),
        Offer(
            business_id=uuid4(),
            title="Offer 2",
            items=items,
            start_time=now,
            end_time=now + timedelta(hours=2),
            created_at=now - timedelta(hours=1),
        ),
        Offer(
            business_id=uuid4(),
            title="Offer 3",
            items=items,
            start_time=now,
            end_time=now + timedelta(hours=2),
            created_at=now - timedelta(hours=2),
        ),
    ]

    ranked = await service.rank_offers(offers)

    # Most recent first
    assert ranked[0].title == "Offer 2"
    assert ranked[1].title == "Offer 3"
    assert ranked[2].title == "Offer 1"


@pytest.mark.asyncio
async def test_discovery_popularity_score():
    """Test getting popularity score for offer."""
    service = DiscoveryRankingService()

    offer_id = uuid4()

    # TODO: Mock purchase repository query
    score = await service.get_popularity_score(offer_id)
    # For now, returns 0 as database not implemented
    assert score == 0


@pytest.mark.asyncio
async def test_discovery_distance_calculation():
    """Test distance calculation between coordinates."""
    service = DiscoveryRankingService()

    # TODO: Implement haversine formula test
    distance = await service.calculate_distance((0.0, 0.0), (1.0, 1.0))
    # Placeholder returns 0 for now
    assert distance == 0.0
