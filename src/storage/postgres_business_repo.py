"""PostgreSQL repository for Business entities."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.business import Business, BusinessInput, VerificationStatus, Venue
from src.storage.db_models import BusinessTable
from src.storage.repository_base import RepositoryBase

logger = get_logger(__name__)


class PostgresBusinessRepository(RepositoryBase[Business]):
    """Business repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[Business]:
        """Retrieve business by ID."""
        stmt = select(BusinessTable).where(BusinessTable.id == id)
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            return None

        return self._to_domain_model(db_business)

    async def create(self, entity: BusinessInput) -> Business:
        """Create new business."""
        db_business = BusinessTable(
            owner_id=entity.owner_id,
            business_name=entity.business_name,
            street_address=entity.street_address,
            city=entity.city,
            postal_code=entity.postal_code,
            country_code=entity.country_code,
            latitude=entity.latitude,
            longitude=entity.longitude,
            contact_phone=entity.phone,
            logo_url=entity.logo_url,
        )

        self.session.add(db_business)
        await self.session.flush()
        await self.session.commit()

        logger.info(
            "business_created",
            business_id=str(db_business.id),
            owner_id=entity.owner_id,
            business_name=entity.business_name,
        )

        return self._to_domain_model(db_business)

    async def update(self, entity: Business) -> Business:
        """Update existing business."""
        stmt = select(BusinessTable).where(BusinessTable.id == entity.id)
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            raise ValueError(f"Business not found: {entity.id}")

        db_business.business_name = entity.business_name
        db_business.street_address = entity.venue.street_address
        db_business.city = entity.venue.city
        db_business.postal_code = entity.venue.postal_code
        db_business.country_code = entity.venue.country_code
        db_business.latitude = entity.venue.latitude
        db_business.longitude = entity.venue.longitude
        db_business.contact_phone = entity.contact_phone
        db_business.logo_url = entity.logo_url
        db_business.verification_status = entity.verification_status
        db_business.verification_notes = entity.verification_notes
        db_business.verified_at = entity.verified_at
        db_business.verified_by = entity.verified_by

        await self.session.flush()
        await self.session.commit()

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
        await self.session.commit()

        logger.info("business_deleted", business_id=str(id))

        return True

    async def get_by_owner_id(self, owner_id: int) -> list[Business]:
        """Get businesses by owner user ID."""
        stmt = (
            select(BusinessTable)
            .where(BusinessTable.owner_id == owner_id)
            .order_by(BusinessTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_businesses = result.scalars().all()

        return [self._to_domain_model(db_business) for db_business in db_businesses]

    async def get_by_verification_status(
        self, status: VerificationStatus
    ) -> list[Business]:
        """Get businesses by verification status."""
        stmt = (
            select(BusinessTable)
            .where(BusinessTable.verification_status == status)
            .order_by(BusinessTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_businesses = result.scalars().all()

        return [self._to_domain_model(db_business) for db_business in db_businesses]

    async def approve_business(self, id: UUID, approved_by: int) -> Business:
        """Approve pending business."""
        stmt = select(BusinessTable).where(BusinessTable.id == id)
        result = await self.session.execute(stmt)
        db_business = result.scalar_one_or_none()

        if not db_business:
            raise ValueError(f"Business not found: {id}")

        db_business.verification_status = VerificationStatus.APPROVED
        db_business.verified_at = datetime.utcnow()
        db_business.verified_by = approved_by

        await self.session.flush()
        await self.session.commit()

        logger.info("business_approved", business_id=str(id), approved_by=approved_by)

        return self._to_domain_model(db_business)

    def _to_domain_model(self, db_business: BusinessTable) -> Business:
        """Convert database model to domain model."""
        venue = Venue(
            street_address=db_business.street_address,
            city=db_business.city,
            postal_code=db_business.postal_code,
            country_code=db_business.country_code,
            latitude=float(db_business.latitude) if db_business.latitude else None,
            longitude=float(db_business.longitude) if db_business.longitude else None,
        )

        return Business(
            id=db_business.id,
            owner_id=db_business.owner_id,
            business_name=db_business.business_name,
            venue=venue,
            contact_phone=db_business.contact_phone,
            logo_url=db_business.logo_url,
            verification_status=db_business.verification_status,
            verification_notes=db_business.verification_notes,
            verified_at=db_business.verified_at,
            verified_by=db_business.verified_by,
            created_at=db_business.created_at,
            updated_at=db_business.updated_at,
        )
