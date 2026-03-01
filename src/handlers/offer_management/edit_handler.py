"""Edit offer handler for price/quantity/description/time updates."""

from datetime import datetime
from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from uuid import UUID

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)

# Conversation states for edit flow
EDIT_PRICE, EDIT_QUANTITY, EDIT_DESCRIPTION, EDIT_PICKUP_END = range(4)


async def handle_edit_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit offer callback - show edit options."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract offer_id from callback_data (format: "edit_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text(t("err_offer_not_found", lang))
        return ConversationHandler.END
    
    # Validate state
    if offer.state not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
        await query.edit_message_text(
            t("offer_edit_cannot", lang, state=offer.state.value)
        )
        return ConversationHandler.END
    
    # Store offer_id in context
    context.user_data["edit_offer_id"] = str(offer_id)
    context.user_data["edit_offer"] = offer
    
    # Show edit options
    keyboard = [
        [InlineKeyboardButton(t("btn_edit_price", lang), callback_data="edit_field:price")],
        [InlineKeyboardButton(t("btn_edit_quantity", lang), callback_data="edit_field:quantity")],
        [InlineKeyboardButton(t("btn_edit_description", lang), callback_data="edit_field:description")],
        [InlineKeyboardButton(t("btn_edit_pickup", lang), callback_data="edit_field:pickup_end")],
        [InlineKeyboardButton(t("btn_cancel", lang), callback_data="edit_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t("offer_edit_header", lang,
          title=offer.title,
          price=offer.price_per_unit,
          remaining=offer.quantity_remaining,
          total=offer.quantity_total,
          description=offer.description[:50],
          pickup_end=offer.pickup_end_time.strftime('%H:%M')),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END  # We'll handle field selection via callbacks


async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    field = query.data.split(":")[1]
    offer = context.user_data.get("edit_offer")
    
    if not offer:
        await query.edit_message_text(t("offer_edit_session_expired", lang))
        return ConversationHandler.END
    
    if field == "price":
        await query.edit_message_text(
            t("offer_edit_price_prompt", lang, price=offer.price_per_unit)
        )
        return EDIT_PRICE
    
    elif field == "quantity":
        await query.edit_message_text(
            t("offer_edit_quantity_prompt", lang, remaining=offer.quantity_remaining)
        )
        return EDIT_QUANTITY
    
    elif field == "description":
        await query.edit_message_text(
            t("offer_edit_desc_prompt", lang, description=offer.description)
        )
        return EDIT_DESCRIPTION
    
    elif field == "pickup_end":
        await query.edit_message_text(
            t("offer_edit_pickup_prompt", lang, pickup_end=offer.pickup_end_time.strftime('%H:%M'))
        )
        return EDIT_PICKUP_END
    
    return ConversationHandler.END


async def handle_edit_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price edit input."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    try:
        new_price = Decimal(update.message.text.strip())
        
        if new_price <= 0:
            await update.message.reply_text(t("offer_edit_price_invalid", lang))
            return EDIT_PRICE
        
        # Update offer
        offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
        offer_id = UUID(context.user_data["edit_offer_id"])
        offer = await offer_repo.get_by_id(offer_id)
        
        offer.price_per_unit = new_price
        updated = await offer_repo.update(offer)
        
        await update.message.reply_text(
            t("offer_edit_price_updated", lang, price=new_price)
        )
        
        logger.info(
            "offer_price_updated",
            offer_id=str(offer_id),
            new_price=str(new_price)
        )
        
        return ConversationHandler.END
    
    except (ValueError, decimal.InvalidOperation):
        await update.message.reply_text(
            t("offer_edit_price_format", lang)
        )
        return EDIT_PRICE


async def handle_edit_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity edit input."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    try:
        new_quantity = int(update.message.text.strip())
        
        if new_quantity < 0:
            await update.message.reply_text(t("offer_edit_quantity_invalid", lang))
            return EDIT_QUANTITY
        
        # Update offer
        offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
        offer_id = UUID(context.user_data["edit_offer_id"])
        offer = await offer_repo.get_by_id(offer_id)
        
        offer.quantity_remaining = new_quantity
        # Also update total if new quantity is greater
        if new_quantity > offer.quantity_total:
            offer.quantity_total = new_quantity
        
        updated = await offer_repo.update(offer)
        
        await update.message.reply_text(
            t("offer_edit_quantity_updated", lang, quantity=new_quantity)
        )
        
        logger.info(
            "offer_quantity_updated",
            offer_id=str(offer_id),
            new_quantity=new_quantity
        )
        
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text(
            t("offer_edit_quantity_format", lang)
        )
        return EDIT_QUANTITY


async def handle_edit_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle description edit input."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    new_description = update.message.text.strip()
    
    if len(new_description) < 10 or len(new_description) > 200:
        await update.message.reply_text(
            t("offer_edit_desc_invalid", lang)
        )
        return EDIT_DESCRIPTION
    
    # Update offer
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    offer_id = UUID(context.user_data["edit_offer_id"])
    offer = await offer_repo.get_by_id(offer_id)
    
    offer.description = new_description
    updated = await offer_repo.update(offer)
    
    await update.message.reply_text(
        t("offer_edit_desc_updated", lang)
    )
    
    logger.info(
        "offer_description_updated",
        offer_id=str(offer_id)
    )
    
    return ConversationHandler.END


async def handle_edit_pickup_end_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup end time edit input."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    time_str = update.message.text.strip()
    
    try:
        # Parse HH:MM format
        time_parts = time_str.split(":")
        if len(time_parts) != 2:
            raise ValueError("Invalid format")
        
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError("Invalid time range")
        
        # Update offer
        offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
        offer_id = UUID(context.user_data["edit_offer_id"])
        offer = await offer_repo.get_by_id(offer_id)
        
        # Create new datetime with same date but new time
        new_end_time = offer.pickup_end_time.replace(hour=hour, minute=minute)
        
        # Validate it's after start time
        if new_end_time <= offer.pickup_start_time:
            await update.message.reply_text(
                t("offer_edit_pickup_after_start", lang,
                  start_time=offer.pickup_start_time.strftime('%H:%M'))
            )
            return EDIT_PICKUP_END
        
        # Validate it's in the future
        if new_end_time <= datetime.utcnow():
            await update.message.reply_text(
                t("offer_edit_pickup_future", lang)
            )
            return EDIT_PICKUP_END
        
        offer.pickup_end_time = new_end_time
        updated = await offer_repo.update(offer)
        
        await update.message.reply_text(
            t("offer_edit_pickup_updated", lang, time=new_end_time.strftime('%H:%M'))
        )
        
        logger.info(
            "offer_pickup_end_updated",
            offer_id=str(offer_id),
            new_end_time=new_end_time.isoformat()
        )
        
        return ConversationHandler.END
    
    except (ValueError, IndexError):
        await update.message.reply_text(
            t("offer_edit_pickup_format", lang)
        )
        return EDIT_PICKUP_END


async def handle_edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit cancellation."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    query = update.callback_query
    if query:
        await query.answer("Cancelled")
        await query.edit_message_text(t("offer_edit_cancelled", lang))
    else:
        await update.message.reply_text(t("offer_edit_cancelled", lang))
    
    return ConversationHandler.END


def get_edit_conversation_handler() -> ConversationHandler:
    """Create edit offer conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_edit_offer, pattern=r"^edit_offer:"),
        ],
        states={
            ConversationHandler.TIMEOUT: [
                CallbackQueryHandler(handle_edit_field_selection, pattern=r"^edit_field:"),
            ],
            EDIT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_price_input),
            ],
            EDIT_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_quantity_input),
            ],
            EDIT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_description_input),
            ],
            EDIT_PICKUP_END: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_pickup_end_input),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(handle_edit_cancel, pattern=r"^edit_cancel$"),
        ],
        conversation_timeout=300,  # 5 minutes
    )


# For backward compatibility - also export callback handlers
def get_edit_handler() -> CallbackQueryHandler:
    """Create edit offer initial callback handler."""
    return CallbackQueryHandler(handle_edit_offer, pattern=r"^edit_offer:")
