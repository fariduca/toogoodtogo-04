"""Integration test for purchase race condition prevention.

Tests that concurrent purchase attempts are properly serialized
using distributed locks to prevent overselling.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import random

from src.models.offer import OfferInput, OfferStatus, Item
from src.models.business import BusinessInput, VerificationStatus, Venue
from src.models.purchase import PurchaseRequest
from src.services.purchase_flow import PurchaseFlowService
from src.services.inventory_reservation import InventoryReservation
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_purchase_repo import PostgresPurchaseRepository
from src.storage.redis_locks import RedisLockHelper
from src.storage.database import get_database
from src.config.settings import load_settings


@pytest.mark.asyncio
async def test_concurrent_purchase_prevents_overselling():
    """Test that concurrent purchases don't oversell limited inventory."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # 1. Create business and offer with limited inventory
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Race Test Restaurant",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="789 Race St", latitude=40.7480, longitude=-73.9862),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Limited Stock Test",
                items=[
                    Item(name="Bagel", quantity=5, original_price=Decimal("3.00"), discounted_price=Decimal("1.50")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=2),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
            
        # 2. Initialize purchase services
        settings = load_settings()
        lock_helper = RedisLockHelper(redis_url=settings.redis_url)
        await lock_helper.connect()
        
        async def attempt_purchase(customer_id: int, quantity: int):
            """Simulate purchase attempt."""
            async with db.session() as session:
                offer_repo = PostgresOfferRepository(session)
                purchase_repo = PostgresPurchaseRepository(session)
                inventory_service = InventoryReservation(offer_repo, lock_helper)
                purchase_service = PurchaseFlowService(
                    offer_repo,
                    purchase_repo,
                    inventory_service,
                )
                
                purchase_request = PurchaseRequest(
                    items=[{"item_name": "Bagel", "quantity": quantity}]
                )
                
                result = await purchase_service.create_purchase(
                    offer.id,
                    customer_id,
                    purchase_request,
                    payment_method="CASH",
                )
                await session.commit()
                return result
        
        # 3. Simulate 3 concurrent purchases of 2 items each (total demand = 6, supply = 5)
        tasks = [
            attempt_purchase(customer_id=1000 + i, quantity=2)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. Verify: Only 2 purchases should succeed (2 * 2 = 4 items), 1 should fail
        successful = [r for r in results if not isinstance(r, Exception) and getattr(r, 'success', False)]
        failed = [r for r in results if isinstance(r, Exception) or not getattr(r, 'success', False)]
        
        assert len(successful) == 2, f"Expected 2 successful purchases, got {len(successful)}"
        assert len(failed) == 1, f"Expected 1 failed purchase, got {len(failed)}"
        
        # 5. Verify final inventory (should be 1 remaining)
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            final_offer = await offer_repo.get_by_id(offer.id)
            assert final_offer is not None, "Offer should exist"
            bagel_item = next(i for i in final_offer.items if i.name == "Bagel")
            
            assert bagel_item.quantity == 1, f"Expected 1 remaining, got {bagel_item.quantity}"
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_lock_prevents_simultaneous_reservation():
    """Test that Redis lock prevents simultaneous inventory checks."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Setup: Create offer with 3 items
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Lock Test Shop",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="456 Lock Ave", latitude=40.7580, longitude=-73.9700),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Lock Test Offer",
                items=[
                    Item(name="Cookie", quantity=3, original_price=Decimal("2.00"), discounted_price=Decimal("1.00")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=1),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        settings = load_settings()
        lock_helper = RedisLockHelper(redis_url=settings.redis_url)
        await lock_helper.connect()
        
        async def purchase_with_delay(customer_id: int):
            """Purchase with artificial delay to test lock behavior."""
            async with db.session() as session:
                offer_repo = PostgresOfferRepository(session)
                purchase_repo = PostgresPurchaseRepository(session)
                inventory_service = InventoryReservation(offer_repo, lock_helper)
                
                # Try to reserve 2 items
                item_requests = [{"item_name": "Cookie", "quantity": 2}]
                
                async with inventory_service.reserve_items(offer.id, item_requests) as reservation:
                    if reservation["success"]:
                        # Add delay to keep lock held
                        await asyncio.sleep(0.1)
                    
                    await session.commit()
                    return reservation["success"]
        
        # Launch 2 concurrent purchases (both want 2 items, only 3 available)
        task1 = asyncio.create_task(purchase_with_delay(2001))
        task2 = asyncio.create_task(purchase_with_delay(2002))
        
        result1, result2 = await asyncio.gather(task1, task2)
        
        # One should succeed, one should fail (or wait for lock)
        assert result1 != result2, "Both purchases should not have same outcome"
        assert result1 or result2, "At least one purchase should succeed"
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_purchase_after_inventory_depleted():
    """Test purchase fails gracefully when inventory is depleted."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create business and offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Depleted Test Cafe",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="321 Empty St", latitude=40.7280, longitude=-73.9500),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Sold Out Test",
                items=[
                    Item(name="Muffin", quantity=1, original_price=Decimal("4.00"), discounted_price=Decimal("2.00")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=3),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            
            # Deplete inventory manually
            await offer_repo.decrement_quantity(offer.id, "Muffin", 1)
            await session.commit()
        
        # Try to purchase when inventory is 0
        settings = load_settings()
        lock_helper = RedisLockHelper(redis_url=settings.redis_url)
        await lock_helper.connect()
        
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            purchase_repo = PostgresPurchaseRepository(session)
            inventory_service = InventoryReservation(offer_repo, lock_helper)
            purchase_service = PurchaseFlowService(
                offer_repo,
                purchase_repo,
                inventory_service,
            )
            
            purchase_request = PurchaseRequest(
                items=[{"item_name": "Muffin", "quantity": 1}]
            )
            
            result = await purchase_service.create_purchase(
                offer.id,
                customer_id=3000,
                purchase_request=purchase_request,
                payment_method="CASH",
            )
            
            # Purchase should fail
            assert not result.success, "Purchase should fail when inventory depleted"
            assert result.error is not None and ("Insufficient quantity" in result.error or "quantity" in result.error.lower())
        
    finally:
        await db.disconnect()
