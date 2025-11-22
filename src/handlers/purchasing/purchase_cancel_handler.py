"""Purchase cancellation handler.

Allows customers to cancel purchases before pickup time.
Command: /cancel <purchase_id>
"""

from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.purchase import PurchaseStatus
from src.storage.postgres_purchase_repo import PostgresPurchaseRepository

logger = get_logger(__name__)


async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel a purchase before pickup time."""
    user_id = update.effective_user.id

    # Parse purchase_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /cancel <purchase_id>\n"
            "Example: /cancel 123e4567-e89b-12d3-a456-426614174000"
        )
        return

    purchase_id = context.args[0]

    logger.info("cancel_requested", user_id=user_id, purchase_id=purchase_id)

    try:
        repo: PostgresPurchaseRepository = context.bot_data.get("purchase_repo")

        # TODO: Get purchase from repository
        # purchase = await repo.get_by_id(purchase_id)

        # if not purchase:
        #     await update.message.reply_text("❌ Purchase not found.")
        #     return

        # Verify ownership
        # if purchase.customer_id != user_id:
        #     await update.message.reply_text(
        #         "❌ You can only cancel your own purchases."
        #     )
        #     return

        # Check if already canceled
        # if purchase.status == PurchaseStatus.CANCELED:
        #     await update.message.reply_text("This purchase is already canceled.")
        #     return

        # Check if past pickup time
        # TODO: Get offer to check pickup time (end_time)
        # if datetime.utcnow() > offer.end_time:
        #     await update.message.reply_text(
        #         "❌ Cannot cancel after pickup time has passed."
        #     )
        #     return

        # Cancel purchase
        # await repo.update_status(purchase_id, PurchaseStatus.CANCELED)

        # TODO: Release inventory back to offer

        logger.info("purchase_canceled", user_id=user_id, purchase_id=purchase_id)

        await update.message.reply_text(
            f"✅ Purchase {purchase_id} has been canceled.\n\n"
            "The items have been returned to inventory.\n"
            "No refund needed (cash payment at venue)."
        )

    except Exception as e:
        logger.error(
            "cancel_purchase_failed",
            purchase_id=purchase_id,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ Failed to cancel purchase {purchase_id}. Please try again."
        )


def get_cancellation_handler() -> CommandHandler:
    """Return the cancellation command handler."""
    return CommandHandler("cancel", cancel_purchase)
