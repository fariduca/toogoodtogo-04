"""End offer early handler."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from uuid import UUID

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def handle_end_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle end offer callback - show confirmation prompt."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract offer_id from callback_data (format: "end_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text(t("err_offer_not_found", lang))
        return
    
    # Validate state
    if offer.state not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
        await query.edit_message_text(
            t("offer_end_cannot", lang, state=offer.state.value)
        )
        return
    
    # Show confirmation prompt
    keyboard = [
        [
            InlineKeyboardButton(t("btn_confirm_end", lang), callback_data=f"confirm_end:{offer_id}"),
            InlineKeyboardButton(t("btn_cancel_end", lang), callback_data=f"cancel_end:{offer_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t("offer_end_prompt", lang, title=offer.title, remaining=offer.quantity_remaining),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_confirm_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmed end offer action."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract offer_id from callback_data (format: "confirm_end:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text(t("err_offer_not_found", lang))
        return
    
    # Update state to EXPIRED_EARLY
    updated_offer = await offer_repo.update_state(offer_id, OfferStatus.EXPIRED_EARLY)
    
    await query.edit_message_text(
        t("offer_ended", lang, title=offer.title),
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
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    query = update.callback_query
    await query.answer("Cancelled")
    
    await query.edit_message_text(
        t("offer_end_cancelled", lang)
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
