"""End offer early handler."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from uuid import UUID

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


async def handle_end_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle end offer callback - show confirmation prompt."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract offer_id from callback_data (format: "end_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Offer not found.")
        return
    
    # Validate state
    if offer.state not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
        await query.edit_message_text(
            f"❌ Cannot end offer in {offer.state.value} state."
        )
        return
    
    # Show confirmation prompt
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, end now", callback_data=f"confirm_end:{offer_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_end:{offer_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🛑 **End {offer.title}?**\n\n"
        f"This will permanently end the offer and remove it from customer view.\n"
        f"Currently {offer.quantity_remaining} units remaining.\n\n"
        "This action cannot be undone.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmed end offer action."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract offer_id from callback_data (format: "confirm_end:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Offer not found.")
        return
    
    # Update state to EXPIRED_EARLY
    updated_offer = await offer_repo.update_state(offer_id, OfferStatus.EXPIRED_EARLY)
    
    await query.edit_message_text(
        f"🛑 **{offer.title}** has been ended.\n\n"
        "The offer is no longer visible to customers.",
        parse_mode="Markdown"
    )
    
    logger.info(
        "offer_ended_early",
        offer_id=str(offer_id),
        business_id=str(offer.business_id),
        quantity_remaining=offer.quantity_remaining
    )


async def handle_cancel_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancelled end offer action."""
    query = update.callback_query
    await query.answer("Cancelled")
    
    await query.edit_message_text(
        "✅ Offer ending cancelled. Use /myoffers to manage your offers."
    )


def get_end_handler() -> CallbackQueryHandler:
    """Create end offer callback handler."""
    return CallbackQueryHandler(handle_end_offer, pattern=r"^end_offer:")


def get_confirm_end_handler() -> CallbackQueryHandler:
    """Create confirm end callback handler."""
    return CallbackQueryHandler(handle_confirm_end, pattern=r"^confirm_end:")


def get_cancel_end_handler() -> CallbackQueryHandler:
    """Create cancel end callback handler."""
    return CallbackQueryHandler(handle_cancel_end, pattern=r"^cancel_end:")
