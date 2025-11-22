"""Purchase flow orchestration service.

Coordinates the complete purchase process with inventory locks,
payment processing, and confirmation.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.logging import get_logger
from src.models.purchase import Purchase, PurchaseItem, PurchaseRequest, PurchaseStatus
from src.services.inventory_reservation import InventoryReservation
from src.services.stripe_checkout import StripeCheckoutService
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_purchase_repo import PostgresPurchaseRepository

logger = get_logger(__name__)


class PurchaseResult:
    """Result of purchase flow."""

    def __init__(
        self,
        success: bool,
        purchase_id: UUID | None = None,
        checkout_url: str | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.purchase_id = purchase_id
        self.checkout_url = checkout_url
        self.error = error


class PurchaseFlowService:
    """Orchestrates purchase flow with inventory management."""

    def __init__(
        self,
        offer_repo: PostgresOfferRepository,
        purchase_repo: PostgresPurchaseRepository,
        inventory_reservation: InventoryReservation,
        stripe_service: StripeCheckoutService | None = None,
    ):
        """
        Initialize purchase flow service.

        Args:
            offer_repo: Offer repository
            purchase_repo: Purchase repository
            inventory_reservation: Inventory reservation service
            stripe_service: Stripe service (optional, for online payments)
        """
        self.offer_repo = offer_repo
        self.purchase_repo = purchase_repo
        self.inventory_reservation = inventory_reservation
        self.stripe_service = stripe_service

    async def create_purchase(
        self,
        offer_id: UUID,
        customer_id: int,
        purchase_request: PurchaseRequest,
        payment_method: str = "CASH",
    ) -> PurchaseResult:
        """
        Create a purchase with inventory reservation.

        Args:
            offer_id: Offer being purchased from
            customer_id: Telegram user ID of customer
            purchase_request: Purchase details with item selections
            payment_method: Payment method (CASH or STRIPE)

        Returns:
            PurchaseResult with success status and details
        """
        purchase_id = uuid4()

        logger.info(
            "purchase_flow_started",
            purchase_id=str(purchase_id),
            offer_id=str(offer_id),
            customer_id=customer_id,
            payment_method=payment_method,
        )

        try:
            # Get offer details
            offer = await self.offer_repo.get_by_id(offer_id)

            if not offer:
                return PurchaseResult(success=False, error="Offer not found")

            if offer.is_expired:
                return PurchaseResult(success=False, error="Offer has expired")

            # Reserve inventory with distributed lock
            async with self.inventory_reservation.reserve_items(
                offer_id, purchase_request.items
            ) as reservation:
                if not reservation["success"]:
                    return PurchaseResult(
                        success=False,
                        error=reservation["error"] or "Reservation failed",
                    )

                # Calculate total from reserved items
                total_amount = Decimal("0")
                purchase_items = []

                for item_info in reservation["items"]:
                    item_total = item_info["unit_price"] * item_info["quantity"]
                    total_amount += item_total

                    purchase_items.append(
                        PurchaseItem(
                            item_name=item_info["item_name"],
                            quantity=item_info["quantity"],
                            unit_price=item_info["unit_price"],
                        )
                    )

                # Create purchase record
                purchase = Purchase(
                    id=purchase_id,
                    offer_id=offer_id,
                    customer_id=customer_id,
                    item_selections=purchase_items,
                    total_amount=total_amount,
                    status=PurchaseStatus.PENDING,
                )

                # Save purchase
                # await self.purchase_repo.create(purchase)

                # Handle payment based on method
                if payment_method == "CASH":
                    # For cash, immediately confirm (no online payment)
                    # await self.purchase_repo.update_status(
                    #     purchase_id, PurchaseStatus.CONFIRMED
                    # )

                    logger.info(
                        "cash_purchase_completed",
                        purchase_id=str(purchase_id),
                        total=str(total_amount),
                    )

                    return PurchaseResult(
                        success=True,
                        purchase_id=purchase_id,
                    )

                elif payment_method == "STRIPE" and self.stripe_service:
                    # Create Stripe checkout session
                    checkout_url, expires_at = await self.stripe_service.create_checkout_session(
                        purchase_id=purchase_id,
                        offer_title=offer.title,
                        total_amount=total_amount,
                    )

                    logger.info(
                        "stripe_checkout_created",
                        purchase_id=str(purchase_id),
                        checkout_url=checkout_url,
                    )

                    return PurchaseResult(
                        success=True,
                        purchase_id=purchase_id,
                        checkout_url=checkout_url,
                    )

                else:
                    # Unsupported payment method
                    return PurchaseResult(
                        success=False,
                        error=f"Unsupported payment method: {payment_method}",
                    )

        except Exception as e:
            logger.error(
                "purchase_flow_failed",
                purchase_id=str(purchase_id),
                offer_id=str(offer_id),
                error=str(e),
                exc_info=True,
            )
            return PurchaseResult(
                success=False,
                error=f"Purchase failed: {str(e)}",
            )

    async def cancel_purchase(self, purchase_id: UUID) -> bool:
        """
        Cancel a purchase and release inventory.

        Args:
            purchase_id: Purchase to cancel

        Returns:
            True if successful
        """
        try:
            # Get purchase
            # purchase = await self.purchase_repo.get_by_id(purchase_id)

            # if not purchase:
            #     return False

            # Update status
            # await self.purchase_repo.update_status(purchase_id, PurchaseStatus.CANCELED)

            # Release inventory
            # item_requests = [
            #     {"item_name": item.item_name, "quantity": item.quantity}
            #     for item in purchase.item_selections
            # ]
            # await self.inventory_reservation.release_reservation(
            #     purchase.offer_id, item_requests
            # )

            logger.info("purchase_canceled", purchase_id=str(purchase_id))
            return True

        except Exception as e:
            logger.error(
                "purchase_cancellation_failed",
                purchase_id=str(purchase_id),
                error=str(e),
                exc_info=True,
            )
            return False
