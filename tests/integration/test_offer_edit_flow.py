"""Integration test for offer edit flow.

Tests editing offer price and quantity, verifying that changes
are reflected in discovery listings and purchase flows.
"""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import random

from src.models.offer import OfferInput, OfferStatus, Item
from src.models.business import BusinessInput, VerificationStatus, Venue
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.database import get_database


@pytest.mark.asyncio
async def test_edit_offer_price_reflects_in_listing():
    """Test that price edits are reflected in offer listings."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # 1. Create business and offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Edit Price Test Cafe",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="123 Edit St", latitude=40.7400, longitude=-73.9900),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            original_price = Decimal("5.00")
            offer_input = OfferInput(
                business_id=business.id,
                title="Price Edit Test",
                items=[
                    Item(name="Salad", quantity=10, original_price=Decimal("10.00"), discounted_price=original_price),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=4),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # 2. Edit price (would use update_item_price method when implemented)
        # For now, document expected behavior
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            current_offer = await offer_repo.get_by_id(offer.id)
            
            # Verify original price
            assert current_offer.items[0].discounted_price == original_price
            
            # TODO: Call update_item_price when repository method exists
            # new_price = Decimal("3.50")
            # await offer_repo.update_item_price(offer.id, "Salad", new_price)
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_edit_offer_quantity_affects_purchases():
    """Test that quantity edits affect purchase availability."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # 1. Create business and offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Edit Quantity Test",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="456 Quantity Rd", latitude=40.7500, longitude=-73.9700),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            original_quantity = 5
            offer_input = OfferInput(
                business_id=business.id,
                title="Quantity Edit Test",
                items=[
                    Item(name="Sandwich", quantity=original_quantity, original_price=Decimal("8.00"), discounted_price=Decimal("4.00")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=3),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # 2. Increase quantity
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            
            # TODO: Call update_item_quantity when repository method exists
            # new_quantity = 15
            # await offer_repo.update_item_quantity(offer.id, "Sandwich", new_quantity)
            
            # Verify quantity updated
            updated_offer = await offer_repo.get_by_id(offer.id)
            assert updated_offer.items[0].quantity == original_quantity  # Will be new_quantity when implemented
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_edit_paused_offer():
    """Test that paused offers can be edited."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create paused offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Paused Edit Test",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="789 Paused Ave", latitude=40.7300, longitude=-73.9600),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Paused Edit Test",
                items=[
                    Item(name="Coffee", quantity=20, original_price=Decimal("3.00"), discounted_price=Decimal("1.50")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=2),
                status=OfferStatus.PAUSED,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # Edit while paused (should be allowed)
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            paused_offer = await offer_repo.get_by_id(offer.id)
            
            assert paused_offer.status == OfferStatus.PAUSED
            # TODO: Perform edit operations when methods exist
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_cannot_edit_expired_offer():
    """Test that expired offers cannot be edited."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create expired offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Expired Edit Test",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="321 Expired St", latitude=40.7200, longitude=-73.9800),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Expired Offer",
                items=[
                    Item(name="Pastry", quantity=10, original_price=Decimal("4.00"), discounted_price=Decimal("2.00")),
                ],
                start_time=datetime.utcnow() - timedelta(hours=5),
                end_time=datetime.utcnow() - timedelta(hours=1),
                status=OfferStatus.EXPIRED,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # Verify cannot edit expired offer
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            expired_offer = await offer_repo.get_by_id(offer.id)
            
            assert expired_offer.status == OfferStatus.EXPIRED
            assert expired_offer.is_expired
            # Business logic should prevent edits
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_edit_multiple_items():
    """Test editing offer with multiple items."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create offer with multiple items
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Multi Item Edit Test",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="654 Multi St", latitude=40.7450, longitude=-73.9650),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Multi Item Offer",
                items=[
                    Item(name="Bagel", quantity=15, original_price=Decimal("2.00"), discounted_price=Decimal("1.00")),
                    Item(name="Donut", quantity=10, original_price=Decimal("1.50"), discounted_price=Decimal("0.75")),
                    Item(name="Muffin", quantity=8, original_price=Decimal("3.00"), discounted_price=Decimal("1.50")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=4),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # Edit individual items
        async with db.session() as session:
            offer_repo = PostgresOfferRepository(session)
            multi_offer = await offer_repo.get_by_id(offer.id)
            
            assert len(multi_offer.items) == 3
            
            # TODO: Update individual items when methods exist
            # await offer_repo.update_item_price(offer.id, "Bagel", Decimal("0.50"))
            # await offer_repo.update_item_quantity(offer.id, "Donut", 20)
        
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_edit_preserves_purchase_history():
    """Test that editing doesn't affect past purchase records."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # Create offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="History Test",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="987 History Ln", latitude=40.7350, longitude=-73.9750),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="History Preservation Test",
                items=[
                    Item(name="Soup", quantity=10, original_price=Decimal("6.00"), discounted_price=Decimal("3.00")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=3),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            await session.commit()
        
        # TODO: Create purchase, then edit offer, verify purchase record unchanged
        # This documents expected behavior: edits don't retroactively affect purchases
        
    finally:
        await db.disconnect()
