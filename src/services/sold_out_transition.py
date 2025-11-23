"""Sold-out transition service.

Automatically transitions offers to SOLD_OUT status when
all item inventory is depleted.
"""

from uuid import UUID

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


class SoldOutTransitionService:
    """Manages automatic sold-out transitions."""

    def __init__(self, offer_repo: PostgresOfferRepository):
        """
        Initialize sold-out transition service.

        Args:
            offer_repo: Offer repository for status updates
        """
        self.offer_repo = offer_repo

    async def check_and_transition_to_sold_out(self, offer_id: UUID) -> bool:
        """
        Check if offer should transition to sold-out and perform transition.

        Called after purchase completion or quantity updates to check
        if all items are depleted.

        Args:
            offer_id: Offer to check

        Returns:
            True if transition occurred, False otherwise
        """
        try:
            # Get current offer state
            offer = await self.offer_repo.get_by_id(offer_id)

            if not offer:
                logger.warning(
                    "sold_out_check_offer_not_found",
                    offer_id=str(offer_id),
                )
                return False

            # Skip if offer is not active or paused
            if offer.status not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
                logger.debug(
                    "sold_out_check_skipped",
                    offer_id=str(offer_id),
                    status=offer.status.value,
                    reason="Offer not in active or paused status",
                )
                return False

            # Check if all items are depleted
            total_remaining = sum(item.quantity for item in offer.items)

            if total_remaining > 0:
                logger.debug(
                    "sold_out_check_items_available",
                    offer_id=str(offer_id),
                    remaining=total_remaining,
                )
                return False

            # Transition to sold out
            await self.offer_repo.update_status(offer_id, OfferStatus.SOLD_OUT)

            logger.info(
                "offer_sold_out",
                offer_id=str(offer_id),
                offer_title=offer.title,
                previous_status=offer.status.value,
            )

            return True

        except Exception as e:
            logger.error(
                "sold_out_transition_failed",
                offer_id=str(offer_id),
                error=str(e),
                exc_info=True,
            )
            return False

    async def force_sold_out(self, offer_id: UUID) -> bool:
        """
        Force an offer to sold-out status (manual business action).

        Allows business owners to manually mark offers as sold out
        even if inventory remains.

        Args:
            offer_id: Offer to mark sold out

        Returns:
            True if successful
        """
        try:
            offer = await self.offer_repo.get_by_id(offer_id)

            if not offer:
                logger.warning(
                    "force_sold_out_offer_not_found",
                    offer_id=str(offer_id),
                )
                return False

            # Check current status allows transition
            if offer.status == OfferStatus.SOLD_OUT:
                logger.debug(
                    "force_sold_out_already_sold_out",
                    offer_id=str(offer_id),
                )
                return True

            if offer.status in [OfferStatus.EXPIRED, OfferStatus.DRAFT]:
                logger.warning(
                    "force_sold_out_invalid_status",
                    offer_id=str(offer_id),
                    status=offer.status.value,
                )
                return False

            # Update status
            await self.offer_repo.update_status(offer_id, OfferStatus.SOLD_OUT)

            logger.info(
                "offer_force_sold_out",
                offer_id=str(offer_id),
                offer_title=offer.title,
                previous_status=offer.status.value,
            )

            return True

        except Exception as e:
            logger.error(
                "force_sold_out_failed",
                offer_id=str(offer_id),
                error=str(e),
                exc_info=True,
            )
            return False

    async def can_transition_to_sold_out(self, offer_id: UUID) -> tuple[bool, str]:
        """
        Check if offer can transition to sold-out.

        Args:
            offer_id: Offer to check

        Returns:
            Tuple of (can_transition, reason_if_not)
        """
        try:
            offer = await self.offer_repo.get_by_id(offer_id)

            if not offer:
                return False, "Offer not found"

            # Check status
            if offer.status == OfferStatus.SOLD_OUT:
                return False, "Offer is already sold out"

            if offer.status == OfferStatus.EXPIRED:
                return False, "Offer has expired"

            if offer.status == OfferStatus.DRAFT:
                return False, "Offer is still in draft"

            # Check inventory
            total_remaining = sum(item.quantity for item in offer.items)

            if total_remaining == 0:
                return True, "All items depleted"

            return True, "Can be manually marked as sold out"

        except Exception as e:
            logger.error(
                "can_transition_check_failed",
                offer_id=str(offer_id),
                error=str(e),
                exc_info=True,
            )
            return False, f"Check failed: {str(e)}"
