"""Integration test for successful reservation flow.

Tests end-to-end reservation with inventory management:
1. List active offers
2. Select offer and quantity
3. Reserve inventory with lock
4. Confirm reservation (on-site payment)
5. Verify inventory updated
"""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import random

from src.models.offer import OfferInput, OfferStatus
from src.models.business import BusinessInput, VerificationStatus, Venue
from src.models.reservation import ReservationInput, ReservationStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.database import get_database


@pytest.mark.asyncio
async def test_complete_reservation_flow():
    """Test complete reservation flow from browsing to confirmation."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # 1. Create business and active offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                business_name="Flow Test Restaurant",
                owner_id=random.randint(100000, 999999),
                street_address="321 Flow St",
                city="Helsinki",
                postal_code="00100",
                country_code="FI",
                latitude=40.7306,
                longitude=-73.9352,
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Reservation Flow Test",
                description="Test offer for reservation flow testing purposes",
                quantity_total=10,
                price_per_unit=Decimal("5.00"),
                currency="EUR",
                pickup_start_time=datetime.utcnow(),
                pickup_end_time=datetime.utcnow() + timedelta(hours=4),
            )
            offer = await offer_repo.create(offer_input)
            
            # 2. Create reservation
            reservation_repo = PostgresReservationRepository(session)
            reservation_input = ReservationInput(
                offer_id=offer.id,
                customer_id=999888,
                quantity=3,
                unit_price=Decimal("5.00"),
            )
            reservation = await reservation_repo.create(reservation_input)
            
            # 3. Decrement inventory
            await offer_repo.decrement_quantity(offer.id, 3)
            
            # 4. Verify reservation created
            assert reservation.id is not None
            assert reservation.status == ReservationStatus.CONFIRMED
            assert reservation.total_price == Decimal("15.00")  # 3 * 5.00
            
            # 5. Verify inventory updated
            updated_offer = await offer_repo.get_by_id(offer.id)
            assert updated_offer.quantity_remaining == 7  # 10 - 3
            
            await session.commit()
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_reservation_updates_inventory(mock_db, mock_redis):
    """Test reservation decrements offer quantities."""
    # TODO: Create offer with 10 units
    # TODO: Reserve 3 units
    # TODO: Verify remaining quantity is 7

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_reservation_prevents_overselling(mock_db, mock_redis):
    """Test reservation fails if insufficient inventory."""
    # TODO: Create offer with 5 units
    # TODO: Attempt to reserve 6 units
    # TODO: Verify reservation fails with appropriate error

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_reservation_requires_active_offer(mock_db):
    """Test reservation fails for expired or inactive offers."""
    # TODO: Create expired offer
    # TODO: Attempt reservation
    # TODO: Verify failure

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_reservation_with_distributed_lock(mock_redis):
    """Test reservation acquires distributed lock on offer."""
    # TODO: Mock Redis lock helper
    # TODO: Initiate reservation
    # TODO: Verify lock acquired and released

    pytest.skip("Redis mocking needed")


@pytest.mark.asyncio
async def test_reservation_calculates_correct_total(mock_db):
    """Test reservation total matches quantity and unit price."""
    # TODO: Create offer with known unit price
    # TODO: Reserve specific quantity
    # TODO: Verify total_price = quantity * unit_price

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_reservation_immediate_confirmation(mock_db):
    """Test reservations are immediately confirmed."""
    # TODO: Create reservation
    # TODO: Verify status is CONFIRMED (customer pays on-site)

    pytest.skip("Database implementation pending")
