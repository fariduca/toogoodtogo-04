"""Pause and resume offer handlers."""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository
from uuid import UUID

logger = get_logger(__name__)


async def handle_pause_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pause offer callback."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract offer_id from callback_data (format: "pause_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text(t("err_offer_not_found", lang))
        return
    
    # Validate state
    if offer.state != OfferStatus.ACTIVE:
        await query.edit_message_text(
            t("offer_pause_cannot", lang, state=offer.state.value)
        )
        return
    
    # Update state to PAUSED
    updated_offer = await offer_repo.update_state(offer_id, OfferStatus.PAUSED)
    
    await query.edit_message_text(
        t("offer_paused", lang, title=offer.title),
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
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract offer_id from callback_data (format: "resume_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text(t("err_offer_not_found", lang))
        return
    
    # Validate state
    if offer.state != OfferStatus.PAUSED:
        await query.edit_message_text(
            t("offer_resume_cannot", lang, state=offer.state.value)
        )
        return
    
    # Check if offer is expired
    if offer.is_expired:
        await query.edit_message_text(
            t("offer_resume_expired", lang, end_time=offer.pickup_end_time.strftime('%H:%M'))
        )
        return
    
    # Update state to ACTIVE
    updated_offer = await offer_repo.update_state(offer_id, OfferStatus.ACTIVE)
    
    await query.edit_message_text(
        t("offer_resumed", lang, title=offer.title),
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
