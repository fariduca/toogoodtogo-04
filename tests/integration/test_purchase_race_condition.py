"""Integration test for reservation race condition prevention.

Tests that concurrent reservation attempts are properly serialized
using distributed locks to prevent overselling.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import random

from src.models.offer import OfferInput
from src.models.business import BusinessInput
from src.services.reservation_flow import ReservationFlowService
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.redis_locks import RedisLockHelper
from src.storage.database import get_database
from src.config.settings import load_settings


@pytest.mark.asyncio
async def test_concurrent_reservation_prevents_overselling():
    """Test that concurrent reservations don't oversell limited inventory."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # 1. Create business and offer with limited inventory
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Race Test Restaurant",
                owner_id=random.randint(100000, 999999),
                street_address="789 Race St",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=40.7480,
                longitude=-73.9862,
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Limited Stock Test",
                description="Test offer with limited inventory for race condition testing",
                quantity_total=5,
                price_per_unit=Decimal("1.50"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=2),
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
            
        # 2. Initialize reservation services
        settings = load_settings()
        lock_helper = RedisLockHelper(redis_url=settings.redis_url)
        await lock_helper.connect()
        
        async def attempt_reservation(customer_id: int, quantity: int):
            """Simulate reservation attempt."""
            async with db.session() as session:
                offer_repo = PostgresOfferRepository(session)
                reservation_repo = PostgresReservationRepository(session)
                reservation_service = ReservationFlowService(
                    offer_repo,
                    reservation_repo,
                    lock_helper,
                )
                
                result = await reservation_service.create_reservation(
                    customer_id=customer_id,
                    offer_id=offer.id,
                    quantity=quantity,
                )
                await session.commit()
                return result
        
        # 3. Simulate 3 concurrent reservations of 2 units each (total demand = 6, supply = 5)
        tasks = [
            attempt_reservation(customer_id=1000 + i, quantity=2)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. Verify: Only 2 reservations should succeed (2 * 2 = 4 units), 1 should fail
        successful = [r for r in results if not isinstance(r, Exception) and r[0]]
        failed = [r for r in results if isinstance(r, Exception) or not r[0]]
        
        assert len(successful) == 2, f"Expected 2 successful reservations, got {len(successful)}"
        assert len(failed) == 1, f"Expected 1 failed reservation, got {len(failed)}"
        
        # 5. Verify final inventory (should be 1 remaining)
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            final_offer = await offer_repo.get_by_id(offer.id)
            assert final_offer is not None, "Offer should exist"
            assert final_offer.quantity_remaining == 1, f"Expected 1 remaining, got {final_offer.quantity_remaining}"
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_lock_prevents_simultaneous_reservation():
    """Test that Redis lock prevents simultaneous inventory checks."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Setup: Create offer with 3 units
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Lock Test Shop",
                owner_id=random.randint(100000, 999999),
                street_address="456 Lock Ave",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=40.7580,
                longitude=-73.9700,
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Lock Test Offer",
                description="Test offer for distributed lock testing purposes",
                quantity_total=3,
                price_per_unit=Decimal("1.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=1),
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        settings = load_settings()
        lock_helper = RedisLockHelper(redis_url=settings.redis_url)
        await lock_helper.connect()
        
        async def reserve_with_delay(customer_id: int):
            """Reserve with artificial delay to test lock behavior."""
            async with db.session() as session:
                offer_repo = PostgresOfferRepository(session)
                reservation_repo = PostgresReservationRepository(session)
                reservation_service = ReservationFlowService(
                    offer_repo,
                    reservation_repo,
                    lock_helper,
                )
                
                # Try to reserve 2 units with delay
                result = await reservation_service.create_reservation(
                    customer_id=customer_id,
                    offer_id=offer.id,
                    quantity=2,
                )
                
                if result[0]:  # success
                    # Add delay to keep lock held
                    await asyncio.sleep(0.1)
                
                await session.commit()
                return result[0]  # return success boolean
        
        # Launch 2 concurrent reservations (both want 2 units, only 3 available)
        task1 = asyncio.create_task(reserve_with_delay(2001))
        task2 = asyncio.create_task(reserve_with_delay(2002))
        
        result1, result2 = await asyncio.gather(task1, task2)
        
        # One should succeed, one should fail (or wait for lock)
        assert result1 != result2, "Both reservations should not have same outcome"
        assert result1 or result2, "At least one reservation should succeed"
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_reservation_after_inventory_depleted():
    """Test reservation fails gracefully when inventory is depleted."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create business and offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Depleted Test Cafe",
                owner_id=random.randint(100000, 999999),
                street_address="321 Empty St",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=40.7280,
                longitude=-73.9500,
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Sold Out Test",
                description="Test offer for depleted inventory testing",
                quantity_total=1,
                price_per_unit=Decimal("2.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=3),
            )
            offer = await offer_repo.create(offer_input)
            
            # Deplete inventory manually
            await offer_repo.decrement_quantity(offer.id, 1)
            await session.commit()
        
        # Try to reserve when inventory is 0
        settings = load_settings()
        lock_helper = RedisLockHelper(redis_url=settings.redis_url)
        await lock_helper.connect()
        
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            reservation_repo = PostgresReservationRepository(session)
            reservation_service = ReservationFlowService(
                offer_repo,
                reservation_repo,
                lock_helper,
            )
            
            result = await reservation_service.create_reservation(
                customer_id=3000,
                offer_id=offer.id,
                quantity=1,
            )
            
            # Reservation should fail
            assert not result[0], "Reservation should fail when inventory depleted"
            assert result[1] is not None and ("available" in result[1].lower() or "units" in result[1].lower())
        
    finally:
        await db.disconnect()
