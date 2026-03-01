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

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.purchase import PurchaseRequest
from src.services.purchase_flow import PurchaseFlowService
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def initiate_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle purchase button callback."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Resolve user language
    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    if not user:
        await query.edit_message_text(t("err_register_first", "en"))
        return
    lang = get_lang(user)

    # Parse offer_id from callback data
    callback_data = query.data
    if not callback_data.startswith("purchase:"):
        await query.edit_message_text(t("purchase_invalid_action", lang))
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
        message_text = t("purchase_items_header", lang, offer_id=offer_id)

        # Create item selection buttons
        keyboard = [
            [InlineKeyboardButton(t("btn_confirm_cash", lang), callback_data=f"confirm_cash:{offer_id}")],
            [InlineKeyboardButton(t("btn_cancel", lang), callback_data="back_to_offers")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error("purchase_initiation_failed", error=str(e), exc_info=True)
        await query.edit_message_text(t("purchase_initiate_failed", lang))


async def confirm_cash_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cash purchase confirmation (MVP - no online payment)."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Resolve user language
    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    lang = get_lang(user) if user else "en"

    # Parse offer_id from callback data
    callback_data = query.data
    if not callback_data.startswith("confirm_cash:"):
        await query.edit_message_text(t("purchase_invalid_confirmation", lang))
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
        message_text = t("purchase_confirmed", lang, offer_id=offer_id)

        await query.edit_message_text(message_text, parse_mode="Markdown")

    except Exception as e:
        logger.error("cash_purchase_failed", error=str(e), exc_info=True)
        await query.edit_message_text(t("purchase_confirm_failed", lang))


def get_purchase_initiation_handlers() -> list:
    """Return list of purchase initiation handlers."""
    return [
        CallbackQueryHandler(initiate_purchase, pattern=r"^purchase:"),
        CallbackQueryHandler(confirm_cash_purchase, pattern=r"^confirm_cash:"),
    ]
