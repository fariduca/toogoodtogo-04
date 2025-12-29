"""PostgreSQL repository for Purchase entities."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.purchase import Purchase, PurchaseInput, PurchaseStatus, PurchaseItem, Customer
from src.storage.db_models import PurchaseTable, CustomerTable
from src.storage.repository_base import RepositoryBase

logger = get_logger(__name__)


class PostgresPurchaseRepository(RepositoryBase[Purchase]):
    """Purchase repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[Purchase]:
        """Retrieve purchase by ID."""
        stmt = select(PurchaseTable).where(PurchaseTable.id == id)
        result = await self.session.execute(stmt)
        db_purchase = result.scalar_one_or_none()

        if not db_purchase:
            return None

        return self._to_domain_model(db_purchase)

    async def create(self, entity: PurchaseInput) -> Purchase:
        """Create new purchase."""
        # Ensure customer exists
        await self._ensure_customer_exists(entity.customer_id)

        db_purchase = PurchaseTable(
            offer_id=entity.offer_id,
            customer_id=entity.customer_id,
            item_selections=[
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price),
                }
                for item in entity.item_selections
            ],
            total_amount=entity.total_amount,
            status=entity.status,
            payment_provider=getattr(entity, 'payment_provider', None),
            payment_session_id=getattr(entity, 'payment_session_id', None),
        )

        self.session.add(db_purchase)
        await self.session.flush()
        await self.session.commit()

        logger.info(
            "purchase_created",
            purchase_id=str(db_purchase.id),
            offer_id=str(entity.offer_id),
            customer_id=entity.customer_id,
        )

        return self._to_domain_model(db_purchase)

    async def update(self, entity: Purchase) -> Purchase:
        """Update existing purchase."""
        stmt = select(PurchaseTable).where(PurchaseTable.id == entity.id)
        result = await self.session.execute(stmt)
        db_purchase = result.scalar_one_or_none()

        if not db_purchase:
            raise ValueError(f"Purchase not found: {entity.id}")

        db_purchase.item_selections = [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in entity.item_selections
        ]
        db_purchase.total_amount = entity.total_amount
        db_purchase.status = entity.status
        if hasattr(entity, 'payment_provider'):
            db_purchase.payment_provider = entity.payment_provider
        if hasattr(entity, 'payment_session_id'):
            db_purchase.payment_session_id = entity.payment_session_id

        await self.session.flush()
        await self.session.commit()

        logger.info("purchase_updated", purchase_id=str(entity.id))

        return self._to_domain_model(db_purchase)

    async def delete(self, id: UUID) -> bool:
        """Delete purchase by ID."""
        stmt = select(PurchaseTable).where(PurchaseTable.id == id)
        result = await self.session.execute(stmt)
        db_purchase = result.scalar_one_or_none()

        if not db_purchase:
            return False

        await self.session.delete(db_purchase)
        await self.session.flush()
        await self.session.commit()

        logger.info("purchase_deleted", purchase_id=str(id))

        return True

    async def get_by_offer(self, offer_id: UUID) -> list[Purchase]:
        """Get all purchases for an offer."""
        stmt = (
            select(PurchaseTable)
            .where(PurchaseTable.offer_id == offer_id)
            .order_by(PurchaseTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_purchases = result.scalars().all()

        return [self._to_domain_model(db_purchase) for db_purchase in db_purchases]

    async def update_status(self, id: UUID, status: PurchaseStatus) -> Purchase:
        """Update purchase status."""
        stmt = select(PurchaseTable).where(PurchaseTable.id == id)
        result = await self.session.execute(stmt)
        db_purchase = result.scalar_one_or_none()

        if not db_purchase:
            raise ValueError(f"Purchase not found: {id}")

        db_purchase.status = status
        await self.session.flush()
        await self.session.commit()

        logger.info("purchase_status_updated", purchase_id=str(id), status=status.value)

        return self._to_domain_model(db_purchase)

    async def confirm_purchase(self, id: UUID, payment_reference: str) -> Purchase:
        """Confirm purchase with payment reference."""
        stmt = select(PurchaseTable).where(PurchaseTable.id == id)
        result = await self.session.execute(stmt)
        db_purchase = result.scalar_one_or_none()

        if not db_purchase:
            raise ValueError(f"Purchase not found: {id}")

        db_purchase.status = PurchaseStatus.CONFIRMED
        db_purchase.payment_session_id = payment_reference
        await self.session.flush()
        await self.session.commit()

        logger.info(
            "purchase_confirmed",
            purchase_id=str(id),
            payment_reference=payment_reference,
        )

        return self._to_domain_model(db_purchase)

    async def get_by_customer(self, customer_id: int) -> list[Purchase]:
        """Get all purchases for a customer."""
        stmt = (
            select(PurchaseTable)
            .where(PurchaseTable.customer_id == customer_id)
            .order_by(PurchaseTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_purchases = result.scalars().all()

        return [self._to_domain_model(db_purchase) for db_purchase in db_purchases]

    async def _ensure_customer_exists(self, telegram_id: int, username: str = None):
        """Ensure customer record exists, create if not."""
        stmt = select(CustomerTable).where(CustomerTable.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        db_customer = result.scalar_one_or_none()

        if not db_customer:
            db_customer = CustomerTable(
                telegram_id=telegram_id,
                username=username,
            )
            self.session.add(db_customer)
            await self.session.flush()
            await self.session.commit()
            logger.info("customer_created", telegram_id=telegram_id)

    def _to_domain_model(self, db_purchase: PurchaseTable) -> Purchase:
        """Convert database model to domain model."""
        item_selections = [
            PurchaseItem(
                name=item["name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            for item in db_purchase.item_selections
        ]

        return Purchase(
            id=db_purchase.id,
            offer_id=db_purchase.offer_id,
            customer_id=db_purchase.customer_id,
            item_selections=item_selections,
            total_amount=db_purchase.total_amount,
            status=db_purchase.status,
            payment_provider=db_purchase.payment_provider,
            payment_session_id=db_purchase.payment_session_id,
            created_at=db_purchase.created_at,
        )
