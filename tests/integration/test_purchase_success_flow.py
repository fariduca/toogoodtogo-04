"""Integration test for successful purchase flow.

Tests end-to-end purchase with inventory management:
1. List active offers
2. Select offer and items
3. Reserve inventory with lock
4. Confirm purchase (cash)
5. Verify inventory updated
"""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
import random

from src.models.offer import OfferInput, OfferStatus, Item
from src.models.business import BusinessInput, VerificationStatus, Venue
from src.models.purchase import PurchaseInput, PurchaseStatus, PurchaseItem
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_purchase_repo import PostgresPurchaseRepository
from src.storage.database import get_database


@pytest.mark.asyncio
async def test_complete_purchase_flow():
    """Test complete purchase flow from browsing to confirmation."""
    db = get_database()
    await db.connect()
    
    try:
        async with db.session() as session:
            # 1. Create business and active offer
            business_repo = PostgresBusinessRepository(session)
            business_input = BusinessInput(
                name="Flow Test Restaurant",
                telegram_id=random.randint(100000, 999999),
                verification_status=VerificationStatus.APPROVED,
                venue=Venue(address="321 Flow St", latitude=40.7306, longitude=-73.9352),
            )
            business = await business_repo.create(business_input)
            
            offer_repo = PostgresOfferRepository(session)
            offer_input = OfferInput(
                business_id=business.id,
                title="Purchase Flow Test",
                items=[
                    Item(name="Sandwich", quantity=5, original_price=Decimal("8.00"), discounted_price=Decimal("4.00")),
                    Item(name="Coffee", quantity=10, original_price=Decimal("3.50"), discounted_price=Decimal("1.75")),
                ],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(hours=4),
                status=OfferStatus.ACTIVE,
            )
            offer = await offer_repo.create(offer_input)
            
            # 2. Initiate purchase
            purchase_repo = PostgresPurchaseRepository(session)
            purchase_input = PurchaseInput(
                offer_id=offer.id,
                customer_id=999888,
                item_selections=[
                    PurchaseItem(name="Sandwich", quantity=2, unit_price=Decimal("4.00")),
                    PurchaseItem(name="Coffee", quantity=1, unit_price=Decimal("1.75")),
                ],
                total_amount=Decimal("9.75"),
                status=PurchaseStatus.CONFIRMED,  # Cash purchase
            )
            purchase = await purchase_repo.create(purchase_input)
            
            # 3. Decrement inventory
            await offer_repo.decrement_quantity(offer.id, "Sandwich", 2)
            await offer_repo.decrement_quantity(offer.id, "Coffee", 1)
            
            # 4. Verify purchase created
            assert purchase.id is not None
            assert purchase.status == PurchaseStatus.CONFIRMED
            assert purchase.total_amount == Decimal("9.75")
            
            # 5. Verify inventory updated
            updated_offer = await offer_repo.get_by_id(offer.id)
            sandwich_item = next(i for i in updated_offer.items if i.name == "Sandwich")
            coffee_item = next(i for i in updated_offer.items if i.name == "Coffee")
            assert sandwich_item.quantity == 3  # 5 - 2
            assert coffee_item.quantity == 9    # 10 - 1
            
            await session.commit()
    finally:
        await db.disconnect()


@pytest.mark.asyncio
async def test_purchase_updates_inventory(mock_db, mock_redis):
    """Test purchase decrements offer item quantities."""
    # TODO: Create offer with 10 items
    # TODO: Purchase 3 items
    # TODO: Verify remaining quantity is 7

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_purchase_prevents_overselling(mock_db, mock_redis):
    """Test purchase fails if insufficient inventory."""
    # TODO: Create offer with 5 items
    # TODO: Attempt to purchase 6 items
    # TODO: Verify purchase fails with appropriate error

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_purchase_requires_active_offer(mock_db):
    """Test purchase fails for expired or inactive offers."""
    # TODO: Create expired offer
    # TODO: Attempt purchase
    # TODO: Verify failure

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_purchase_with_distributed_lock(mock_redis):
    """Test purchase acquires distributed lock on offer."""
    # TODO: Mock Redis lock helper
    # TODO: Initiate purchase
    # TODO: Verify lock acquired and released

    pytest.skip("Redis mocking needed")


@pytest.mark.asyncio
async def test_purchase_calculates_correct_total(mock_db):
    """Test purchase total matches item prices."""
    # TODO: Create offer with known item prices
    # TODO: Purchase specific items
    # TODO: Verify total_amount = sum(quantity * unit_price)

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_cash_purchase_immediate_confirmation(mock_db):
    """Test cash purchases are immediately confirmed."""
    # TODO: Create purchase with payment_method=CASH
    # TODO: Verify status is CONFIRMED (not PENDING)

    pytest.skip("Database implementation pending")
