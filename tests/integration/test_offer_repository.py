"""Integration tests for Offer repository."""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from uuid import uuid4
import random

from src.models.offer import OfferInput, OfferStatus, Item
from src.models.business import BusinessInput, VerificationStatus, Venue
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.database import get_database


@pytest.mark.asyncio
async def test_offer_repository_create():
    """Test creating offer in repository."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create business first with unique telegram_id
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Test Restaurant",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="123 Test St", latitude=40.7128, longitude=-74.0060),
            )
            business = await business_repo.create(business_input)
            
            # Create offer
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Fresh Bread",
                items=[Item(name="Baguette", quantity=10, original_price=Decimal("5.00"), discounted_price=Decimal("2.50"))],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=2),
                status=OfferStatus.ACTIVE,
            )
            created = await offer_repo.create(offer_input)
            
            assert created.id is not None
            assert created.title == "Fresh Bread"
            assert len(created.items) == 1
            assert created.items[0].quantity == 10
            await session.commit()
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_offer_repository_get_active():
    """Test retrieving active offers."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            offers = await offer_repo.get_active_offers(limit=10)
            
            assert isinstance(offers, list)
            # All returned offers should be active and not expired
            for offer in offers:
                assert offer.status == OfferStatus.ACTIVE
                assert offer.end_time > datetime.utcnow()
            await session.commit()
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_offer_repository_get_expired():
    """Test retrieving expired offers."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            expired = await offer_repo.get_expired_offers()
            
            assert isinstance(expired, list)
            # All returned offers should be past their end_time
            for offer in expired:
                assert offer.status == OfferStatus.ACTIVE
                assert offer.end_time <= datetime.utcnow()
            await session.commit()
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_offer_repository_update_status():
    """Test updating offer status."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create test offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Status Test Restaurant",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="456 Test Ave", latitude=40.7580, longitude=-73.9855),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Status Test Offer",
                items=[Item(name="Croissant", quantity=5, original_price=Decimal("3.00"), discounted_price=Decimal("1.50"))],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=1),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            
            # Update status
            updated = await offer_repo.update_status(offer.id, OfferStatus.PAUSED)
            assert updated.status == OfferStatus.PAUSED
            await session.commit()
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_offer_repository_decrement_quantity():
    """Test atomic quantity decrement."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create test offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Quantity Test Restaurant",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="789 Test Blvd", latitude=40.7489, longitude=-73.9680),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Quantity Test Offer",
                items=[Item(name="Bread", quantity=10, original_price=Decimal("4.00"), discounted_price=Decimal("2.00"))],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=3),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            
            # Decrement quantity
            success = await offer_repo.decrement_quantity(offer.id, "Bread", 3)
            assert success
            
            # Verify updated quantity
            updated_offer = await offer_repo.get_by_id(offer.id)
            assert updated_offer.items[0].quantity == 7
            
            # Test insufficient quantity
            success = await offer_repo.decrement_quantity(offer.id, "Bread", 10)
            assert not success  # Should fail
            await session.commit()
    finally:
        await db.disconnect()
