"""Pause and resume offer handlers."""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository
from uuid import UUID

logger = get_logger(__name__)


async def handle_pause_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pause offer callback."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract offer_id from callback_data (format: "pause_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Offer not found.")
        return
    
    # Validate state
    if offer.state != OfferStatus.ACTIVE:
        await query.edit_message_text(
            f"❌ Cannot pause offer in {offer.state.value} state."
        )
        return
    
    # Update state to PAUSED
    updated_offer = await offer_repo.update_state(offer_id, OfferStatus.PAUSED)
    
    await query.edit_message_text(
        f"⏸️ **{offer.title}** is now paused.\n\n"
        "Customers won't see this offer in browse results. "
        "Use /myoffers to resume it.",
        parse_mode="Markdown"
    )
    
    logger.info(
        "offer_paused",
        offer_id=str(offer_id),
        business_id=str(offer.business_id)
    )


async def handle_resume_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle resume offer callback."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract offer_id from callback_data (format: "resume_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Offer not found.")
        return
    
    # Validate state
    if offer.state != OfferStatus.PAUSED:
        await query.edit_message_text(
            f"❌ Cannot resume offer in {offer.state.value} state."
        )
        return
    
    # Check if offer is expired
    if offer.is_expired:
        await query.edit_message_text(
            f"❌ Cannot resume expired offer. "
            f"Pickup window ended at {offer.pickup_end_time.strftime('%H:%M')}."
        )
        return
    
    # Update state to ACTIVE
    updated_offer = await offer_repo.update_state(offer_id, OfferStatus.ACTIVE)
    
    await query.edit_message_text(
        f"▶️ **{offer.title}** is now active!\n\n"
        "Customers can now see and reserve this offer.",
        parse_mode="Markdown"
    )
    
    logger.info(
        "offer_resumed",
        offer_id=str(offer_id),
        business_id=str(offer.business_id)
    )


def get_pause_handler() -> CallbackQueryHandler:
    """Create pause offer callback handler."""
    return CallbackQueryHandler(handle_pause_offer, pattern=r"^pause_offer:")


def get_resume_handler() -> CallbackQueryHandler:
    """Create resume offer callback handler."""
    return CallbackQueryHandler(handle_resume_offer, pattern=r"^resume_offer:")
