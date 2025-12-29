"""PostgreSQL repository for Reservation entities."""

import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import get_logger
from src.models.reservation import Reservation, ReservationInput, ReservationStatus
from src.storage.db_models import ReservationTable
from src.storage.repository_base import RepositoryBase

logger = get_logger(__name__)


class PostgresReservationRepository(RepositoryBase[Reservation]):
    """Reservation repository using PostgreSQL."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[Reservation]:
        """Retrieve reservation by ID."""
        stmt = select(ReservationTable).where(ReservationTable.id == id)
        result = await self.session.execute(stmt)
        db_reservation = result.scalar_one_or_none()

        if not db_reservation:
            return None

        return self._to_domain_model(db_reservation)

    async def create(self, entity: ReservationInput) -> Reservation:
        """Create new reservation with unique order ID."""
        order_id = self._generate_order_id()

        db_reservation = ReservationTable(
            order_id=order_id,
            offer_id=entity.offer_id,
            customer_id=entity.customer_id,
            quantity=entity.quantity,
            unit_price=entity.unit_price,
            total_price=entity.total_price,
            currency=entity.currency,
            status=ReservationStatus.CONFIRMED,
            pickup_start_time=entity.pickup_start_time,
            pickup_end_time=entity.pickup_end_time,
        )

        self.session.add(db_reservation)
        await self.session.flush()
        await self.session.commit()

        logger.info(
            "reservation_created",
            reservation_id=str(db_reservation.id),
            order_id=order_id,
            offer_id=str(entity.offer_id),
            customer_id=entity.customer_id,
            quantity=entity.quantity,
            total_price=float(entity.total_price),
        )

        return self._to_domain_model(db_reservation)

    async def update(self, entity: Reservation) -> Reservation:
        """Update existing reservation."""
        stmt = select(ReservationTable).where(ReservationTable.id == entity.id)
        result = await self.session.execute(stmt)
        db_reservation = result.scalar_one_or_none()

        if not db_reservation:
            raise ValueError(f"Reservation not found: {entity.id}")

        db_reservation.status = entity.status
        db_reservation.cancellation_reason = entity.cancellation_reason
        db_reservation.cancelled_at = entity.cancelled_at

        await self.session.flush()
        await self.session.commit()

        logger.info("reservation_updated", reservation_id=str(entity.id))

        return self._to_domain_model(db_reservation)

    async def delete(self, id: UUID) -> bool:
        """Delete reservation by ID."""
        stmt = select(ReservationTable).where(ReservationTable.id == id)
        result = await self.session.execute(stmt)
        db_reservation = result.scalar_one_or_none()

        if not db_reservation:
            return False

        await self.session.delete(db_reservation)
        await self.session.flush()
        await self.session.commit()

        logger.info("reservation_deleted", reservation_id=str(id))

        return True

    async def get_by_order_id(self, order_id: str) -> Optional[Reservation]:
        """Get reservation by customer-facing order ID."""
        stmt = select(ReservationTable).where(ReservationTable.order_id == order_id)
        result = await self.session.execute(stmt)
        db_reservation = result.scalar_one_or_none()

        if not db_reservation:
            return None

        return self._to_domain_model(db_reservation)

    async def get_by_customer(
        self, customer_id: int, limit: int = 50
    ) -> list[Reservation]:
        """Get reservations for a customer, newest first."""
        stmt = (
            select(ReservationTable)
            .where(ReservationTable.customer_id == customer_id)
            .order_by(ReservationTable.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        db_reservations = result.scalars().all()

        return [self._to_domain_model(db_res) for db_res in db_reservations]

    async def get_by_offer(self, offer_id: UUID) -> list[Reservation]:
        """Get all reservations for an offer."""
        stmt = (
            select(ReservationTable)
            .where(ReservationTable.offer_id == offer_id)
            .order_by(ReservationTable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_reservations = result.scalars().all()

        return [self._to_domain_model(db_res) for db_res in db_reservations]

    async def get_active_by_customer(self, customer_id: int) -> list[Reservation]:
        """Get confirmed reservations for a customer."""
        stmt = (
            select(ReservationTable)
            .where(ReservationTable.customer_id == customer_id)
            .where(ReservationTable.status == ReservationStatus.CONFIRMED)
            .order_by(ReservationTable.pickup_end_time.asc())
        )
        result = await self.session.execute(stmt)
        db_reservations = result.scalars().all()

        return [self._to_domain_model(db_res) for db_res in db_reservations]

    async def cancel(
        self, reservation_id: UUID, reason: Optional[str] = None
    ) -> Reservation:
        """Cancel a reservation."""
        stmt = select(ReservationTable).where(ReservationTable.id == reservation_id)
        result = await self.session.execute(stmt)
        db_reservation = result.scalar_one_or_none()

        if not db_reservation:
            raise ValueError(f"Reservation not found: {reservation_id}")

        if db_reservation.status != ReservationStatus.CONFIRMED:
            raise ValueError(
                f"Cannot cancel reservation with status: {db_reservation.status}"
            )

        db_reservation.status = ReservationStatus.CANCELLED
        db_reservation.cancellation_reason = reason
        db_reservation.cancelled_at = datetime.utcnow()

        await self.session.flush()
        await self.session.commit()

        logger.info(
            "reservation_cancelled",
            reservation_id=str(reservation_id),
            reason=reason,
        )

        return self._to_domain_model(db_reservation)

    def _generate_order_id(self) -> str:
        """Generate unique order ID in format RES-XXXXXXXX."""
        random_hex = secrets.token_hex(4).upper()
        return f"RES-{random_hex}"

    def _to_domain_model(self, db_reservation: ReservationTable) -> Reservation:
        """Convert database model to domain model."""
        return Reservation(
            id=db_reservation.id,
            order_id=db_reservation.order_id,
            offer_id=db_reservation.offer_id,
            customer_id=db_reservation.customer_id,
            quantity=db_reservation.quantity,
            unit_price=db_reservation.unit_price,
            total_price=db_reservation.total_price,
            currency=db_reservation.currency,
            status=db_reservation.status,
            pickup_start_time=db_reservation.pickup_start_time,
            pickup_end_time=db_reservation.pickup_end_time,
            cancellation_reason=db_reservation.cancellation_reason,
            cancelled_at=db_reservation.cancelled_at,
            created_at=db_reservation.created_at,
            updated_at=db_reservation.updated_at,
        )
