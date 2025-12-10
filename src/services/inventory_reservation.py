"""Inventory reservation service.

Manages temporary reservations of offer items during purchase flow
using Redis locks to prevent overselling.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import AsyncIterator
from uuid import UUID

from src.logging import get_logger
from src.models.offer import Offer
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.redis_locks import RedisLockHelper

logger = get_logger(__name__)

# Reservation timeout (5 minutes to complete purchase)
RESERVATION_TIMEOUT_SECONDS = 300


class InventoryReservation:
    """Manages inventory reservations with locks."""

    def __init__(
        self,
        offer_repo: PostgresOfferRepository,
        lock_helper: RedisLockHelper,
    ):
        """
        Initialize inventory reservation service.

        Args:
            offer_repo: Offer repository for updating quantities
            lock_helper: Redis lock helper for preventing race conditions
        """
        self.offer_repo = offer_repo
        self.lock_helper = lock_helper

    @asynccontextmanager
    async def reserve_items(
        self,
        offer_id: UUID,
        item_requests: list[dict],
    ) -> AsyncIterator[dict]:
        """
        Reserve items from an offer with distributed lock.

        Context manager that acquires lock, reserves items, and releases
        on exit (commit or rollback).

        Args:
            offer_id: Offer to reserve from
            item_requests: List of {"item_name": str, "quantity": int}

        Yields:
            Reservation info with success status and details

        Raises:
            ValueError: If reservation fails (insufficient quantity, etc.)
        """
        reservation = {"success": False, "items": [], "error": None}

        # Acquire distributed lock on offer
        async with self.lock_helper.acquire_offer_lock(offer_id) as lock_acquired:
            if not lock_acquired:
                reservation["error"] = "Could not acquire lock (offer busy)"
                logger.warning("reservation_lock_failed", offer_id=str(offer_id))
                yield reservation
                return

            try:
                # Get current offer state
                offer = await self.offer_repo.get_by_id(offer_id)

                if not offer:
                    reservation["error"] = "Offer not found"
                    yield reservation
                    return

                # Check offer is still active
                if offer.is_expired:
                    reservation["error"] = "Offer has expired"
                    yield reservation
                    return

                # Validate item requests against available inventory
                for item_req in item_requests:
                    item_name = item_req["item_name"]
                    requested_qty = item_req["quantity"]

                    # Find item in offer
                    offer_item = next(
                        (item for item in offer.items if item.name == item_name),
                        None,
                    )

                    if not offer_item:
                        reservation["error"] = f"Item '{item_name}' not found in offer"
                        yield reservation
                        return

                    if offer_item.quantity < requested_qty:
                        reservation["error"] = (
                            f"Insufficient quantity for '{item_name}'. "
                            f"Available: {offer_item.quantity}, "
                            f"Requested: {requested_qty}"
                        )
                        yield reservation
                        return

                    reservation["items"].append(
                        {
                            "name": item_name,
                            "quantity": requested_qty,
                            "unit_price": offer_item.discounted_price,
                        }
                    )

                # Decrement quantities atomically
                for item_req in item_requests:
                    success = await self.offer_repo.decrement_quantity(
                        offer_id,
                        item_req["item_name"],
                        item_req["quantity"],
                    )

                    if not success:
                        reservation["error"] = "Failed to reserve inventory"
                        # TODO: Rollback previous decrements
                        yield reservation
                        return

                reservation["success"] = True
                logger.info(
                    "inventory_reserved",
                    offer_id=str(offer_id),
                    items=len(item_requests),
                )

                # Yield control to caller (purchase flow)
                try:
                    yield reservation
                except Exception as e:
                    # Exception occurred in caller code after successful reservation
                    # Log it but don't re-yield (would cause "generator didn't stop" error)
                    logger.error(
                        "reservation_context_error",
                        offer_id=str(offer_id),
                        error=str(e),
                        exc_info=True,
                    )
                    raise

                # Lock released on context exit

            except Exception as e:
                # Exception during reservation setup (before yield)
                if not reservation["success"]:
                    reservation["error"] = f"Reservation failed: {str(e)}"
                    logger.error(
                        "reservation_error",
                        offer_id=str(offer_id),
                        error=str(e),
                        exc_info=True,
                    )
                    yield reservation
                else:
                    # Exception after successful reservation, already logged above
                    raise

    async def release_reservation(
        self,
        offer_id: UUID,
        item_requests: list[dict],
    ) -> bool:
        """
        Release a reservation (restore inventory).

        Used when purchase is canceled or fails.

        Args:
            offer_id: Offer to release items back to
            item_requests: List of {"item_name": str, "quantity": int}

        Returns:
            True if successful
        """
        try:
            # TODO: Implement increment_quantity in repository
            # For now, log the action

            logger.info(
                "inventory_released",
                offer_id=str(offer_id),
                items=item_requests,
            )

            return True

        except Exception as e:
            logger.error(
                "inventory_release_failed",
                offer_id=str(offer_id),
                error=str(e),
                exc_info=True,
            )
            return False
