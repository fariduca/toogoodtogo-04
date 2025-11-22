"""PostgreSQL repository for Offer entities."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from src.logging import get_logger
from src.models.offer import Offer, OfferInput, OfferStatus, Item
from src.storage.db_models import OfferTable
from src.storage.repository_base import RepositoryBase

logger = get_logger(__name__)


class PostgresOfferRepository(RepositoryBase[Offer]):
    """Offer repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[Offer]:
        """Retrieve offer by ID."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            return None

        return self._to_domain_model(db_offer)

    async def create(self, entity: OfferInput) -> Offer:
        """Create new offer."""
        db_offer = OfferTable(
            business_id=entity.business_id,
            title=entity.title,
            items=[
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "original_price": float(item.original_price),
                    "discounted_price": float(item.discounted_price),
                }
                for item in entity.items
            ],
            start_time=entity.start_time,
            end_time=entity.end_time,
            status=entity.status,
            image_url=getattr(entity, 'image_url', None),
        )

        self.session.add(db_offer)
        await self.session.flush()

        logger.info("offer_created", offer_id=str(db_offer.id), business_id=str(entity.business_id))

        return self._to_domain_model(db_offer)

    async def update(self, entity: Offer) -> Offer:
        """Update existing offer."""
        stmt = select(OfferTable).where(OfferTable.id == entity.id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            raise ValueError(f"Offer not found: {entity.id}")

        db_offer.title = entity.title
        db_offer.items = [
            {
                "name": item.name,
                "quantity": item.quantity,
                "original_price": float(item.original_price),
                "discounted_price": float(item.discounted_price),
            }
            for item in entity.items
        ]
        db_offer.start_time = entity.start_time
        db_offer.end_time = entity.end_time
        db_offer.status = entity.status
        if hasattr(entity, 'image_url'):
            db_offer.image_url = entity.image_url

        await self.session.flush()

        logger.info("offer_updated", offer_id=str(entity.id))

        return self._to_domain_model(db_offer)

    async def delete(self, id: UUID) -> bool:
        """Delete offer by ID."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            return False

        await self.session.delete(db_offer)
        await self.session.flush()

        logger.info("offer_deleted", offer_id=str(id))

        return True

    async def get_active_offers(self, limit: int = 20) -> list[Offer]:
        """Get active offers ordered by creation time."""
        stmt = (
            select(OfferTable)
            .where(OfferTable.status == OfferStatus.ACTIVE)
            .where(OfferTable.end_time > datetime.utcnow())
            .order_by(OfferTable.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        db_offers = result.scalars().all()

        return [self._to_domain_model(db_offer) for db_offer in db_offers]

    async def get_expired_offers(self) -> list[Offer]:
        """Get offers past end_time with active status."""
        stmt = (
            select(OfferTable)
            .where(OfferTable.status == OfferStatus.ACTIVE)
            .where(OfferTable.end_time <= datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        db_offers = result.scalars().all()

        return [self._to_domain_model(db_offer) for db_offer in db_offers]

    async def update_status(self, id: UUID, status: OfferStatus) -> Offer:
        """Update offer status."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            raise ValueError(f"Offer not found: {id}")

        db_offer.status = status
        await self.session.flush()

        logger.info("offer_status_updated", offer_id=str(id), status=status.value)

        return self._to_domain_model(db_offer)

    async def decrement_quantity(
        self, id: UUID, item_name: str, quantity: int
    ) -> bool:
        """Atomically decrement item quantity."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            return False

        # Find the item in the items JSON array
        items = db_offer.items
        item_found = False
        for item in items:
            if item["name"] == item_name:
                if item["quantity"] < quantity:
                    logger.warning(
                        "insufficient_quantity",
                        offer_id=str(id),
                        item_name=item_name,
                        available=item["quantity"],
                        requested=quantity,
                    )
                    return False
                item["quantity"] -= quantity
                item_found = True
                break

        if not item_found:
            logger.warning("item_not_found", offer_id=str(id), item_name=item_name)
            return False

        # Mark JSON column as modified and update
        flag_modified(db_offer, "items")
        await self.session.flush()

        logger.info(
            "quantity_decremented",
            offer_id=str(id),
            item_name=item_name,
            quantity_removed=quantity,
        )

        return True

    async def get_offers_by_business(self, business_id: UUID) -> list[Offer]:
        """Get all offers for a business."""
        stmt = (
            select(OfferTable)
            .where(OfferTable.business_id == business_id)
            .order_by(OfferTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_offers = result.scalars().all()

        return [self._to_domain_model(db_offer) for db_offer in db_offers]

    def _to_domain_model(self, db_offer: OfferTable) -> Offer:
        """Convert database model to domain model."""
        items = [
            Item(
                name=item["name"],
                quantity=item["quantity"],
                original_price=item["original_price"],
                discounted_price=item["discounted_price"],
            )
            for item in db_offer.items
        ]

        return Offer(
            id=db_offer.id,
            business_id=db_offer.business_id,
            title=db_offer.title,
            items=items,
            start_time=db_offer.start_time,
            end_time=db_offer.end_time,
            status=db_offer.status,
            image_url=db_offer.image_url,
            created_at=db_offer.created_at,
        )
