"""PostgreSQL repository for Offer entities."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.offer import Offer, OfferInput, OfferStatus
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
            description=entity.description,
            photo_url=entity.photo_url,
            category=entity.category,
            price_per_unit=entity.price_per_unit,
            currency=entity.currency,
            quantity_total=entity.quantity_total,
            quantity_remaining=entity.quantity_total,
            pickup_start_time=entity.pickup_start_time,
            pickup_end_time=entity.pickup_end_time,
            state=OfferStatus.ACTIVE,
            published_at=datetime.utcnow(),
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
        db_offer.description = entity.description
        db_offer.photo_url = entity.photo_url
        db_offer.category = entity.category
        db_offer.price_per_unit = entity.price_per_unit
        db_offer.quantity_total = entity.quantity_total
        db_offer.quantity_remaining = entity.quantity_remaining
        db_offer.pickup_start_time = entity.pickup_start_time
        db_offer.pickup_end_time = entity.pickup_end_time
        db_offer.state = entity.state

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
            .where(OfferTable.state == OfferStatus.ACTIVE)
            .where(OfferTable.pickup_end_time > datetime.utcnow())
            .where(OfferTable.quantity_remaining > 0)
            .order_by(OfferTable.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        db_offers = result.scalars().all()

        return [self._to_domain_model(db_offer) for db_offer in db_offers]

    async def get_expired_offers(self) -> list[Offer]:
        """Get offers past pickup_end_time with active status."""
        stmt = (
            select(OfferTable)
            .where(OfferTable.state == OfferStatus.ACTIVE)
            .where(OfferTable.pickup_end_time <= datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        db_offers = result.scalars().all()

        return [self._to_domain_model(db_offer) for db_offer in db_offers]

    async def update_state(self, id: UUID, state: OfferStatus) -> Offer:
        """Update offer state."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            raise ValueError(f"Offer not found: {id}")

        db_offer.state = state
        await self.session.flush()

        logger.info("offer_state_updated", offer_id=str(id), state=state.value)

        return self._to_domain_model(db_offer)

    async def decrement_quantity(self, id: UUID, quantity: int) -> bool:
        """Atomically decrement quantity_remaining."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            return False

        if db_offer.quantity_remaining < quantity:
            logger.warning(
                "insufficient_quantity",
                offer_id=str(id),
                available=db_offer.quantity_remaining,
                requested=quantity,
            )
            return False

        db_offer.quantity_remaining -= quantity

        # Auto-transition to SOLD_OUT if quantity reaches 0
        if db_offer.quantity_remaining == 0:
            db_offer.state = OfferStatus.SOLD_OUT
            logger.info("offer_sold_out", offer_id=str(id))

        await self.session.flush()

        logger.info(
            "quantity_decremented",
            offer_id=str(id),
            quantity_removed=quantity,
            remaining=db_offer.quantity_remaining,
        )

        return True

    async def increment_quantity(self, id: UUID, quantity: int) -> bool:
        """Increment quantity_remaining (for cancellations)."""
        stmt = select(OfferTable).where(OfferTable.id == id)
        result = await self.session.execute(stmt)
        db_offer = result.scalar_one_or_none()

        if not db_offer:
            return False

        db_offer.quantity_remaining += quantity

        # If was SOLD_OUT and now has inventory, revert to ACTIVE
        if db_offer.state == OfferStatus.SOLD_OUT and db_offer.quantity_remaining > 0:
            if db_offer.pickup_end_time > datetime.utcnow():
                db_offer.state = OfferStatus.ACTIVE
                logger.info("offer_reactivated_from_sold_out", offer_id=str(id))

        await self.session.flush()

        logger.info(
            "quantity_incremented",
            offer_id=str(id),
            quantity_added=quantity,
            remaining=db_offer.quantity_remaining,
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
        return Offer(
            id=db_offer.id,
            business_id=db_offer.business_id,
            title=db_offer.title,
            description=db_offer.description,
            photo_url=db_offer.photo_url,
            category=db_offer.category,
            price_per_unit=db_offer.price_per_unit,
            currency=db_offer.currency,
            quantity_total=db_offer.quantity_total,
            quantity_remaining=db_offer.quantity_remaining,
            pickup_start_time=db_offer.pickup_start_time,
            pickup_end_time=db_offer.pickup_end_time,
            state=db_offer.state,
            created_at=db_offer.created_at,
            published_at=db_offer.published_at,
            updated_at=db_offer.updated_at,
        )
