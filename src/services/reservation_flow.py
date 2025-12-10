"""Reservation flow service with atomic inventory management."""

from decimal import Decimal
from uuid import UUID

from src.logging import get_logger
from src.models.reservation import ReservationInput
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.redis_locks import RedisLockHelper

logger = get_logger(__name__)


class ReservationFlowService:
    """Service for managing reservation creation with race condition prevention."""

    def __init__(
        self,
        offer_repo: PostgresOfferRepository,
        reservation_repo: PostgresReservationRepository,
        redis_locks: RedisLockHelper,
    ):
        """Initialize reservation flow service."""
        self.offer_repo = offer_repo
        self.reservation_repo = reservation_repo
        self.redis_locks = redis_locks

    async def create_reservation(
        self,
        customer_id: int,
        offer_id: UUID,
        quantity: int,
    ) -> tuple[bool, str, str | None]:
        """
        Create a reservation with atomic inventory decrement.
        
        Returns: (success, message, order_id)
        """
        # Acquire lock on offer
        async with self.redis_locks.acquire_offer_lock(offer_id) as acquired:
            if not acquired:
                logger.warning("lock_acquisition_failed", offer_id=str(offer_id))
                return False, "Offer is currently locked. Please try again.", None

            # Get offer details
            offer = await self.offer_repo.get_by_id(offer_id)
            if not offer:
                return False, "Offer not found", None

            # Validate offer is available
            if not offer.available_for_reservation:
                return False, "Offer is no longer available", None

            # Validate quantity
            if quantity > offer.quantity_remaining:
                return (
                    False,
                    f"Only {offer.quantity_remaining} units available",
                    None,
                )

            # Decrement inventory
            success = await self.offer_repo.decrement_quantity(offer_id, quantity)
            if not success:
                logger.error("inventory_decrement_failed", offer_id=str(offer_id))
                return False, "Failed to reserve units. Please try again.", None

            # Create reservation
            total_price = Decimal(str(quantity)) * offer.price_per_unit
            reservation_input = ReservationInput(
                offer_id=offer_id,
                customer_id=customer_id,
                quantity=quantity,
                unit_price=offer.price_per_unit,
                total_price=total_price,
                currency=offer.currency,
                pickup_start_time=offer.pickup_start_time,
                pickup_end_time=offer.pickup_end_time,
            )

            try:
                reservation = await self.reservation_repo.create(reservation_input)
                logger.info(
                    "reservation_created",
                    reservation_id=str(reservation.id),
                    order_id=reservation.order_id,
                    customer_id=customer_id,
                    offer_id=str(offer_id),
                    quantity=quantity,
                )
                return True, "Reservation confirmed!", reservation.order_id
            except Exception as e:
                logger.error(
                    "reservation_creation_failed",
                    offer_id=str(offer_id),
                    error=str(e),
                )
                # Rollback inventory decrement
                await self.offer_repo.increment_quantity(offer_id, quantity)
                return False, "Failed to create reservation. Please try again.", None
