"""Callback query routing for inline buttons.

Maps callback patterns to handlers for inline keyboard interactions.
"""

from telegram.ext import Application, CallbackQueryHandler

from src.handlers.discovery.list_offers_handler import view_offer_details
from src.handlers.purchasing.reserve_handler import (
    handle_reserve,
    handle_confirm_reserve,
)
from src.handlers.purchasing.cancel_reservation_handler import (
    handle_cancel_reservation,
    handle_confirm_cancel_reservation,
    handle_keep_reservation,
)
from src.handlers.offer_management.pause_resume_handler import (
    handle_pause_offer,
    handle_resume_offer,
)
from src.handlers.offer_management.end_offer_handler import (
    handle_end_offer,
    handle_confirm_end,
    handle_cancel_end,
)
from src.handlers.offer_management.edit_handler import (
    handle_edit_field_selection,
)
from src.handlers.system.settings_handler import (
    handle_toggle_notifications,
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

    # Reservation flow (replaces old purchase flow)
    app.add_handler(
        CallbackQueryHandler(handle_reserve, pattern=r"^reserve:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_confirm_reserve, pattern=r"^confirm_reserve:")
    )
    
    # Reservation cancellation (Phase 6)
    app.add_handler(
        CallbackQueryHandler(handle_cancel_reservation, pattern=r"^cancel_reservation:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_confirm_cancel_reservation, pattern=r"^confirm_cancel_reservation:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_keep_reservation, pattern=r"^keep_reservation:")
    )
    
    # Offer management callbacks (Phase 5)
    app.add_handler(
        CallbackQueryHandler(handle_pause_offer, pattern=r"^pause_offer:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_resume_offer, pattern=r"^resume_offer:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_end_offer, pattern=r"^end_offer:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_confirm_end, pattern=r"^confirm_end:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_cancel_end, pattern=r"^cancel_end:")
    )
    app.add_handler(
        CallbackQueryHandler(handle_edit_field_selection, pattern=r"^edit_field:")
    )

    # Navigation
    app.add_handler(
        CallbackQueryHandler(handle_back_to_offers, pattern=r"^back_to_offers$")
    )
    
    # Settings (Phase 7)
    app.add_handler(
        CallbackQueryHandler(handle_toggle_notifications, pattern=r"^toggle_notifications:")
    )

    logger.info("callback_handlers_registered", count=14)
