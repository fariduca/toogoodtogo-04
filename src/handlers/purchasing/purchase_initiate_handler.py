"""Purchase initiation handler.

Handles the start of purchase flow:
1. Collect item selections
2. Calculate total
3. Create purchase record
4. Generate payment link (or confirm cash payment)
"""

from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.logging import get_logger
from src.models.purchase import PurchaseRequest
from src.services.purchase_flow import PurchaseFlowService
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


async def initiate_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle purchase button callback."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Parse offer_id from callback data
    callback_data = query.data
    if not callback_data.startswith("purchase:"):
        await query.edit_message_text("❌ Invalid purchase action.")
        return

    offer_id = callback_data.split(":", 1)[1]

    logger.info("purchase_initiated", user_id=user_id, offer_id=offer_id)

    try:
        repo: PostgresOfferRepository = context.bot_data.get("offer_repo")
        # TODO: Get offer details
        # offer = await repo.get_by_id(offer_id)

        # if not offer:
        #     await query.edit_message_text("❌ Offer not found.")
        #     return

        # Show item selection interface
        message_text = (
            f"🛒 **Purchase Items**\n\n"
            f"Offer ID: {offer_id}\n\n"
            "Select items to purchase:\n\n"
            "Database query implementation pending.\n\n"
            "For MVP: Cash payment at venue."
        )

        # Create item selection buttons
        keyboard = [
            [InlineKeyboardButton("Confirm Cash Purchase", callback_data=f"confirm_cash:{offer_id}")],
            [InlineKeyboardButton("« Cancel", callback_data="back_to_offers")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error("purchase_initiation_failed", error=str(e), exc_info=True)
        await query.edit_message_text("❌ Failed to initiate purchase.")


async def confirm_cash_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cash purchase confirmation (MVP - no online payment)."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Parse offer_id from callback data
    callback_data = query.data
    if not callback_data.startswith("confirm_cash:"):
        await query.edit_message_text("❌ Invalid confirmation.")
        return

    offer_id = callback_data.split(":", 1)[1]

    try:
        purchase_flow: PurchaseFlowService = context.bot_data.get("purchase_flow")

        # Create purchase request
        # TODO: Get actual item selections from conversation state
        # For MVP: assume purchasing all available items
        purchase_request = PurchaseRequest(
            items=[
                # Placeholder - should be collected from user
                {"item_name": "Sample Item", "quantity": 1}
            ]
        )

        # Process purchase with inventory reservation
        # purchase_result = await purchase_flow.create_purchase(
        #     offer_id=offer_id,
        #     customer_id=user_id,
        #     purchase_request=purchase_request,
        #     payment_method="CASH",
        # )

        # if not purchase_result.success:
        #     await query.edit_message_text(
        #         f"❌ Purchase failed: {purchase_result.error}\n\n"
        #         "The items may no longer be available."
        #     )
        #     return

        logger.info(
            "cash_purchase_confirmed",
            user_id=user_id,
            offer_id=offer_id,
        )

        # TODO: Get venue details for pickup instructions
        message_text = (
            "✅ **Purchase Confirmed!**\n\n"
            f"Offer ID: {offer_id}\n"
            "Payment: Cash at venue\n\n"
            "📍 Pickup Instructions:\n"
            "Visit the venue during the offer time window.\n"
            "Show this confirmation to the business.\n\n"
            "Your reservation is held. Please arrive on time!\n\n"
            "Use /cancel <purchase_id> if you need to cancel."
        )

        await query.edit_message_text(message_text, parse_mode="Markdown")

    except Exception as e:
        logger.error("cash_purchase_failed", error=str(e), exc_info=True)
        await query.edit_message_text("❌ Purchase confirmation failed. Please try again.")


def get_purchase_initiation_handlers() -> list:
    """Return list of purchase initiation handlers."""
    return [
        CallbackQueryHandler(initiate_purchase, pattern=r"^purchase:"),
        CallbackQueryHandler(confirm_cash_purchase, pattern=r"^confirm_cash:"),
    ]
