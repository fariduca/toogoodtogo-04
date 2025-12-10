"""Purchase webhook handler for Stripe payment notifications.

Note: For MVP with cash-only payments, this handler is minimal.
Will be extended when online payments are enabled.
"""

from telegram.ext import ContextTypes

from src.logging import get_logger
from src.models.purchase import PurchaseStatus
from src.services.stripe_checkout import StripeCheckoutService
from src.storage.postgres_purchase_repo import PostgresPurchaseRepository

logger = get_logger(__name__)


async def handle_stripe_webhook(
    webhook_data: dict, context: ContextTypes.DEFAULT_TYPE
) -> dict:
    """
    Process Stripe webhook event.

    Args:
        webhook_data: Webhook payload from Stripe
        context: Bot context for accessing services

    Returns:
        Dictionary with processing result
    """
    event_type = webhook_data.get("type")
    event_id = webhook_data.get("id")

    logger.info("stripe_webhook_received", event_type=event_type, event_id=event_id)

    try:
        if event_type == "checkout.session.completed":
            return await _handle_checkout_completed(webhook_data, context)

        elif event_type == "checkout.session.expired":
            return await _handle_checkout_expired(webhook_data, context)

        else:
            logger.info("stripe_webhook_ignored", event_type=event_type)
            return {"status": "ignored", "event_type": event_type}

    except Exception as e:
        logger.error(
            "stripe_webhook_processing_failed",
            event_type=event_type,
            error=str(e),
            exc_info=True,
        )
        return {"status": "error", "error": str(e)}


async def _handle_checkout_completed(
    webhook_data: dict, context: ContextTypes.DEFAULT_TYPE
) -> dict:
    """Handle successful checkout completion."""
    session_data = webhook_data.get("data", {}).get("object", {})
    session_id = session_data.get("id")

    # Extract purchase_id from session metadata
    metadata = session_data.get("metadata", {})
    purchase_id = metadata.get("purchase_id")

    if not purchase_id:
        logger.error("checkout_completed_missing_purchase_id", session_id=session_id)
        return {"status": "error", "error": "Missing purchase_id in metadata"}

    try:
        repo: PostgresPurchaseRepository = context.bot_data.get("purchase_repo")
        stripe_service: StripeCheckoutService = context.bot_data.get("stripe_service")

        # Verify payment
        payment_info = await stripe_service.verify_payment(session_id)

        # Update purchase status
        # await repo.confirm_purchase(purchase_id)

        logger.info(
            "checkout_completed",
            purchase_id=purchase_id,
            session_id=session_id,
            amount=payment_info.get("amount_total"),
        )

        # TODO: Send confirmation message to customer via Telegram

        return {"status": "success", "purchase_id": purchase_id}

    except Exception as e:
        logger.error(
            "checkout_completion_failed",
            purchase_id=purchase_id,
            error=str(e),
            exc_info=True,
        )
        return {"status": "error", "error": str(e)}


async def _handle_checkout_expired(
    webhook_data: dict, context: ContextTypes.DEFAULT_TYPE
) -> dict:
    """Handle expired checkout session."""
    session_data = webhook_data.get("data", {}).get("object", {})
    session_id = session_data.get("id")

    metadata = session_data.get("metadata", {})
    purchase_id = metadata.get("purchase_id")

    if not purchase_id:
        logger.warning("checkout_expired_missing_purchase_id", session_id=session_id)
        return {"status": "ignored"}

    try:
        repo: PostgresPurchaseRepository = context.bot_data.get("purchase_repo")

        # Cancel purchase and release inventory
        # await repo.update_status(purchase_id, PurchaseStatus.CANCELED)

        logger.info(
            "checkout_expired",
            purchase_id=purchase_id,
            session_id=session_id,
        )

        # TODO: Send notification to customer

        return {"status": "success", "purchase_id": purchase_id}

    except Exception as e:
        logger.error(
            "checkout_expiration_failed",
            purchase_id=purchase_id,
            error=str(e),
            exc_info=True,
        )
        return {"status": "error", "error": str(e)}
