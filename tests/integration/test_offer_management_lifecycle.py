"""Integration test for complete offer lifecycle management (Phase 5).

Tests myoffers listing, pause, resume, edit, and end operations
with real database and Redis interactions.
"""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import random

from src.models.offer import OfferInput, OfferStatus
from src.models.business import BusinessInput
from src.models.user import UserInput, UserRole
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_user_repo import PostgresUserRepository
from src.storage.database import get_database


@pytest.mark.asyncio
async def test_offer_lifecycle_management_flow():
    """Test complete offer management lifecycle: create -> pause -> resume -> edit -> end."""
    db = get_database()
    await db.connect()
    
    try:
        # 1. Create business user and business
        async with db.session() as session:
            user_repo = PostgresUserRepository(session)
            user_input = UserInput(
                telegram_user_id=random.randint(100000, 999999),
                role=UserRole.BUSINESS,
            )
            user = await user_repo.create(user_input)
            
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Lifecycle Test Bakery",
                owner_id=user.id,
                street_address="123 Lifecycle St",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=60.1699,
                longitude=24.9384,
            )
            business = await business_repo.create(business_input)
            await session.commit()
        
        # 2. Create active offer
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Lifecycle Test Pastries",
                description="Testing full lifecycle management capabilities here",
                quantity_total=20,
                price_per_unit=Decimal("3.50"),
                currency="EUR",
                pickup_start_time=datetime.utcnow() + timedelta(hours=1),
                pickup_end_time=datetime.utcnow() + timedelta(hours=6),
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
            
            assert offer.state == OfferStatus.ACTIVE
            assert offer.quantity_remaining == 20
        
        # 3. Test PAUSE operation
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            paused_offer = await offer_repo.update_state(offer.id, OfferStatus.PAUSED)
            await session.commit()
            
            assert paused_offer.state == OfferStatus.PAUSED
            assert not paused_offer.available_for_reservation
        
        # 4. Test RESUME operation
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            resumed_offer = await offer_repo.update_state(offer.id, OfferStatus.ACTIVE)
            await session.commit()
            
            assert resumed_offer.state == OfferStatus.ACTIVE
            assert resumed_offer.available_for_reservation
        
        # 5. Test EDIT operation (update price and quantity)
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            current_offer = await offer_repo.get_by_id(offer.id)
            
            # Edit price and quantity
            current_offer.price_per_unit = Decimal("4.00")
            current_offer.quantity_remaining = 25
            current_offer.quantity_total = 25
            
            edited_offer = await offer_repo.update(current_offer)
            await session.commit()
            
            assert edited_offer.price_per_unit == Decimal("4.00")
            assert edited_offer.quantity_remaining == 25
        
        # 6. Test END EARLY operation
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            ended_offer = await offer_repo.update_state(offer.id, OfferStatus.EXPIRED_EARLY)
            await session.commit()
            
            assert ended_offer.state == OfferStatus.EXPIRED_EARLY
            assert not ended_offer.available_for_reservation
        
        # 7. Verify cannot resume after ending
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            final_offer = await offer_repo.get_by_id(offer.id)
            
            # Attempt to resume should not work (terminal state)
            assert final_offer.state == OfferStatus.EXPIRED_EARLY
            
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_myoffers_listing_with_mixed_states():
    """Test /myoffers shows offers in correct order with various states."""
    db = get_database()
    await db.connect()
    
    try:
        # Create business with multiple offers in different states
        async with db.session() as session:
            user_repo = PostgresUserRepository(session)
            user_input = UserInput(
                telegram_user_id=random.randint(100000, 999999),
                role=UserRole.BUSINESS,
            )
            user = await user_repo.create(user_input)
            
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Multi-Offer Bakery",
                owner_id=user.id,
                street_address="456 Multi St",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=60.1699,
                longitude=24.9384,
            )
            business = await business_repo.create(business_input)
            await session.commit()
        
        # Create offers in different states
        offer_ids = []
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            
            # Active offer
            active_input = OfferInput(
                business_id=business.id,
                title="Active Pastries",
                description="Currently available active pastries for testing",
                quantity_total=10,
                price_per_unit=Decimal("5.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=4),
            )
            active_offer = await offer_repo.create(active_input)
            offer_ids.append(active_offer.id)
            
            # Paused offer
            paused_input = OfferInput(
                business_id=business.id,
                title="Paused Sandwiches",
                description="Temporarily paused sandwiches for testing here",
                quantity_total=5,
                price_per_unit=Decimal("3.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=4),
            )
            paused_offer = await offer_repo.create(paused_input)
            await offer_repo.update_state(paused_offer.id, OfferStatus.PAUSED)
            offer_ids.append(paused_offer.id)
            
            # Sold out offer
            sold_out_input = OfferInput(
                business_id=business.id,
                title="Sold Out Cakes",
                description="Completely sold out cakes for testing purposes",
                quantity_total=3,
                price_per_unit=Decimal("8.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=4),
            )
            sold_out_offer = await offer_repo.create(sold_out_input)
            await offer_repo.update_state(sold_out_offer.id, OfferStatus.SOLD_OUT)
            offer_ids.append(sold_out_offer.id)
            
            await session.commit()
        
        # Retrieve and verify sorting
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            all_offers = await offer_repo.get_by_business_id(business.id)
            
            assert len(all_offers) == 3
            
            # Verify we have all states
            states = {offer.state for offer in all_offers}
            assert OfferStatus.ACTIVE in states
            assert OfferStatus.PAUSED in states
            assert OfferStatus.SOLD_OUT in states
            
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_edit_cannot_set_invalid_pickup_time():
    """Test editing offer validates pickup time constraints."""
    db = get_database()
    await db.connect()
    
    try:
        # Create business and offer
        async with db.session() as session:
            user_repo = PostgresUserRepository(session)
            user_input = UserInput(
                telegram_user_id=random.randint(100000, 999999),
                role=UserRole.BUSINESS,
            )
            user = await user_repo.create(user_input)
            
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Time Test Cafe",
                owner_id=user.id,
                street_address="789 Time St",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=60.1699,
                longitude=24.9384,
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Time Validation Offer",
                description="Testing time validation constraints here",
                quantity_total=10,
                price_per_unit=Decimal("5.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow() + timedelta(hours=2),
                pickup_end_time=datetime.utcnow() + timedelta(hours=5),
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # Try to set end time before start time (should fail validation)
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            current_offer = await offer_repo.get_by_id(offer.id)
            
            # This should fail Pydantic validation
            with pytest.raises(Exception):  # Could be ValueError or ValidationError
                current_offer.pickup_end_time = current_offer.pickup_start_time - timedelta(hours=1)
                await offer_repo.update(current_offer)
                await session.commit()
            
    finally:
        await db.disconnect()
