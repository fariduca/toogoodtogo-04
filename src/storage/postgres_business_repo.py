"""PostgreSQL repository for Business entities."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.logging import get_logger
from src.models.business import Business, BusinessInput, VerificationStatus, Venue
from src.storage.db_models import BusinessTable, VenueTable
from src.storage.repository_base import RepositoryBase

logger = get_logger(__name__)


class PostgresBusinessRepository(RepositoryBase[Business]):
    """Business repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[Business]:
        """Retrieve business by ID."""
        stmt = (
            select(BusinessTable)
            .where(BusinessTable.id == id)
            .options(selectinload(BusinessTable.venue))
        )
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            return None

        return self._to_domain_model(db_business)

    async def create(self, entity: BusinessInput) -> Business:
        """Create new business with venue."""
        db_business = BusinessTable(
            name=entity.name,
            telegram_id=entity.telegram_id,
            verification_status=entity.verification_status,
            photo_url=getattr(entity, 'photo_url', None),
        )

        # Create venue
        db_venue = VenueTable(
            business=db_business,
            address=entity.venue.address,
            latitude=entity.venue.latitude,
            longitude=entity.venue.longitude,
        )

        self.session.add(db_business)
        self.session.add(db_venue)
        await self.session.flush()

        logger.info("business_created", business_id=str(db_business.id), telegram_id=entity.telegram_id)

        return self._to_domain_model(db_business)

    async def update(self, entity: Business) -> Business:
        """Update existing business."""
        stmt = select(BusinessTable).where(BusinessTable.id == entity.id)
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            raise ValueError(f"Business not found: {entity.id}")

        db_business.name = entity.name
        db_business.verification_status = entity.verification_status
        if hasattr(entity, 'photo_url'):
            db_business.photo_url = entity.photo_url

        await self.session.flush()

        logger.info("business_updated", business_id=str(entity.id))

        return self._to_domain_model(db_business)

    async def delete(self, id: UUID) -> bool:
        """Delete business by ID."""
        stmt = select(BusinessTable).where(BusinessTable.id == id)
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            return False

        await self.session.delete(db_business)
        await self.session.flush()

        logger.info("business_deleted", business_id=str(id))

        return True

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[Business]:
        """Get business by Telegram user ID."""
        stmt = (
            select(BusinessTable)
            .where(BusinessTable.telegram_id == telegram_id)
            .options(selectinload(BusinessTable.venue))
        )
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            return None

        return self._to_domain_model(db_business)

    async def get_by_verification_status(
        self, status: VerificationStatus
    ) -> list[Business]:
        """Get businesses by verification status."""
        stmt = (
            select(BusinessTable)
            .where(BusinessTable.verification_status == status)
            .options(selectinload(BusinessTable.venue))
            .order_by(BusinessTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_businesses = result.scalars().all()

        return [self._to_domain_model(db_business) for db_business in db_businesses]

    async def approve_business(self, id: UUID) -> Business:
        """Approve pending business."""
        stmt = select(BusinessTable).where(BusinessTable.id == id)
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            raise ValueError(f"Business not found: {id}")

        db_business.verification_status = VerificationStatus.APPROVED
        await self.session.flush()

        logger.info("business_approved", business_id=str(id))

        return self._to_domain_model(db_business)

    def _to_domain_model(self, db_business: BusinessTable) -> Business:
        """Convert database model to domain model."""
        venue = None
        if db_business.venue:
            venue = Venue(
                address=db_business.venue.address,
                latitude=float(db_business.venue.latitude),
                longitude=float(db_business.venue.longitude),
            )

        return Business(
            id=db_business.id,
            name=db_business.name,
            telegram_id=db_business.telegram_id,
            verification_status=db_business.verification_status,
            venue=venue,
            photo_url=db_business.photo_url,
            created_at=db_business.created_at,
        )
