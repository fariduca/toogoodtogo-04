"""Callback query routing for inline buttons.

Maps callback patterns to handlers for inline keyboard interactions.
"""

from telegram.ext import Application, CallbackQueryHandler

from src.handlers.discovery.list_offers_handler import view_offer_details
from src.handlers.purchasing.purchase_initiate_handler import (
    confirm_cash_purchase,
    initiate_purchase,
)
from src.logging import get_logger

logger = get_logger(__name__)


async def handle_back_to_offers(update, context):
    """Handle back button to return to offers list."""
    query = update.callback_query
    await query.answer()

    # Re-show offers list
    await query.edit_message_text(
        "Use /offers or /browse to see available offers.",
    )


def register_callback_handlers(app: Application) -> None:
    """
    Register callback query handlers for inline buttons.

    Args:
        app: Telegram bot Application instance
    """
    # Offer viewing
    app.add_handler(
        CallbackQueryHandler(view_offer_details, pattern=r"^view_offer:")
    )

    # Purchase flow
    app.add_handler(
        CallbackQueryHandler(initiate_purchase, pattern=r"^purchase:")
    )
    app.add_handler(
        CallbackQueryHandler(confirm_cash_purchase, pattern=r"^confirm_cash:")
    )

    # Navigation
    app.add_handler(
        CallbackQueryHandler(handle_back_to_offers, pattern=r"^back_to_offers$")
    )

    logger.info("callback_handlers_registered", count=4)
