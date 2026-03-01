"""Create new deal handler for business users."""

from datetime import datetime, timedelta
from decimal import Decimal

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.offer import OfferCategory, OfferInput, OfferStatus
from src.models.user import UserRole
from src.security.permissions import PermissionChecker
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)

# Conversation states
TITLE, DESCRIPTION, CATEGORY, PRICE, QUANTITY, PICKUP_START, PICKUP_END, PHOTO, CONFIRM = range(9)


async def newdeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the /newdeal conversation flow."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    telegram_user = update.effective_user
    
    # Get user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        await update.message.reply_text(
            t("offer_need_register", "en")
        )
        return ConversationHandler.END
    
    lang = get_lang(user)
    
    if user.role != UserRole.BUSINESS:
        await update.message.reply_text(
            t("offer_business_only", lang)
        )
        return ConversationHandler.END
    
    # Get user's business
    businesses = await business_repo.get_by_owner_id(user.id)
    
    if not businesses:
        await update.message.reply_text(
            t("offer_no_business", lang)
        )
        return ConversationHandler.END
    
    business = businesses[0]  # Use first business
    
    # Check permissions
    permission_checker: PermissionChecker = context.bot_data["permission_checker"]
    if not permission_checker.can_post_offer(user, business):
        await update.message.reply_text(
            t("offer_pending_verification", lang)
        )
        return ConversationHandler.END
    
    # Store business in context
    context.user_data["business_id"] = str(business.id)
    context.user_data["lang"] = lang
    
    await update.message.reply_text(
        t("offer_start_creation", lang, business_name=business.business_name)
    )
    
    return TITLE


async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle title input."""
    lang = context.user_data.get("lang", "en")
    title = update.message.text.strip()
    
    if len(title) < 3 or len(title) > 100:
        await update.message.reply_text(
            t("offer_title_validation", lang)
        )
        return TITLE
    
    context.user_data["title"] = title
    
    await update.message.reply_text(
        t("offer_ask_description", lang)
    )
    return DESCRIPTION


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle description input."""
    lang = context.user_data.get("lang", "en")
    description = update.message.text.strip()
    
    if len(description) < 10 or len(description) > 200:
        await update.message.reply_text(
            t("offer_desc_validation", lang)
        )
        return DESCRIPTION
    
    context.user_data["description"] = description
    
    await update.message.reply_text(
        t("offer_ask_category", lang)
    )
    return CATEGORY


async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category input."""
    lang = context.user_data.get("lang", "en")
    category_text = update.message.text.strip().upper()
    
    try:
        category = OfferCategory(category_text)
    except ValueError:
        await update.message.reply_text(
            t("offer_category_invalid", lang)
        )
        return CATEGORY
    
    context.user_data["category"] = category.value
    
    await update.message.reply_text(
        t("offer_ask_price", lang)
    )
    return PRICE


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price input."""
    lang = context.user_data.get("lang", "en")
    try:
        price = Decimal(update.message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            t("offer_price_invalid", lang)
        )
        return PRICE
    
    context.user_data["price"] = str(price)
    
    await update.message.reply_text(
        t("offer_ask_quantity", lang)
    )
    return QUANTITY


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input."""
    lang = context.user_data.get("lang", "en")
    try:
        quantity = int(update.message.text.strip())
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            t("offer_quantity_invalid", lang)
        )
        return QUANTITY
    
    context.user_data["quantity"] = quantity
    
    await update.message.reply_text(
        t("offer_ask_pickup_start", lang)
    )
    return PICKUP_START


async def handle_pickup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup start time input."""
    lang = context.user_data.get("lang", "en")
    try:
        pickup_start = datetime.strptime(update.message.text.strip(), "%Y-%m-%d %H:%M")
        
        if pickup_start <= datetime.utcnow():
            await update.message.reply_text(
                t("offer_pickup_start_past", lang)
            )
            return PICKUP_START
        
    except ValueError:
        await update.message.reply_text(
            t("offer_pickup_format_invalid", lang)
        )
        return PICKUP_START
    
    context.user_data["pickup_start"] = pickup_start.isoformat()
    
    await update.message.reply_text(
        t("offer_ask_pickup_end", lang)
    )
    return PICKUP_END


async def handle_pickup_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup end time input."""
    lang = context.user_data.get("lang", "en")
    try:
        pickup_end = datetime.strptime(update.message.text.strip(), "%Y-%m-%d %H:%M")
        pickup_start = datetime.fromisoformat(context.user_data["pickup_start"])
        
        if pickup_end <= pickup_start:
            await update.message.reply_text(
                t("offer_pickup_end_before_start", lang)
            )
            return PICKUP_END
        
        time_window = pickup_end - pickup_start
        if time_window > timedelta(hours=24):
            await update.message.reply_text(
                t("offer_pickup_window_exceeded", lang)
            )
            return PICKUP_END
        
    except ValueError:
        await update.message.reply_text(
            t("offer_pickup_end_format_invalid", lang)
        )
        return PICKUP_END
    
    context.user_data["pickup_end"] = pickup_end.isoformat()
    
    await update.message.reply_text(
        t("offer_ask_photo", lang)
    )
    return PHOTO


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo upload."""
    lang = context.user_data.get("lang", "en")
    if update.message.text and update.message.text.strip().upper() == "SKIP":
        context.user_data["photo_url"] = None
        return await show_confirmation(update, context)
    
    if not update.message.photo:
        await update.message.reply_text(
            t("offer_photo_prompt", lang)
        )
        return PHOTO
    
    # Get largest photo
    photo = update.message.photo[-1]
    context.user_data["photo_file_id"] = photo.file_id
    
    # TODO: Upload to Azure Blob Storage using ImageProcessingService
    # For now, store file_id for later download
    
    await update.message.reply_text(t("offer_photo_received", lang))
    
    return await show_confirmation(update, context)


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show deal summary and ask for confirmation."""
    lang = context.user_data.get("lang", "en")
    pickup_start = datetime.fromisoformat(context.user_data["pickup_start"])
    pickup_end = datetime.fromisoformat(context.user_data["pickup_end"])
    
    has_photo = t("offer_photo_yes", lang) if context.user_data.get("photo_file_id") else t("offer_photo_no", lang)
    
    summary = t(
        "offer_summary",
        lang,
        title=context.user_data["title"],
        description=context.user_data["description"],
        category=context.user_data["category"],
        price=context.user_data["price"],
        quantity=context.user_data["quantity"],
        pickup_start=pickup_start.strftime("%b %d, %H:%M"),
        pickup_end=pickup_end.strftime("%H:%M"),
        has_photo=has_photo,
    )
    
    await update.message.reply_text(summary)
    return CONFIRM


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle final confirmation and create offer."""
    response = update.message.text.strip().upper()
    
    lang = context.user_data.get("lang", "en")
    
    if response != "YES":
        await update.message.reply_text(
            t("offer_creation_cancelled", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Create offer
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    settings = context.bot_data["settings"]
    
    from uuid import UUID
    
    business_id = UUID(context.user_data["business_id"])
    
    offer_input = OfferInput(
        business_id=business_id,
        title=context.user_data["title"],
        description=context.user_data["description"],
        category=OfferCategory(context.user_data["category"]),
        price_per_unit=Decimal(context.user_data["price"]),
        currency="USD",
        quantity_total=context.user_data["quantity"],
        pickup_start_time=datetime.fromisoformat(context.user_data["pickup_start"]),
        pickup_end_time=datetime.fromisoformat(context.user_data["pickup_end"]),
        image_url=context.user_data.get("photo_url"),
    )
    
    offer = await offer_repo.create(offer_input)
    
    logger.info(
        "offer_created",
        offer_id=str(offer.id),
        business_id=str(business_id),
        title=offer.title,
        quantity=offer.quantity_total,
    )
    
    # Generate share link
    bot_username = (await context.bot.get_me()).username
    share_link = f"https://t.me/{bot_username}?start=offer_{offer.id}"
    
    # Send success message
    await update.message.reply_text(
        t("offer_published", lang, title=offer.title, share_link=share_link),
        reply_markup=ReplyKeyboardRemove(),
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_newdeal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel deal creation."""
    lang = context.user_data.get("lang", "en")
    context.user_data.clear()
    await update.message.reply_text(
        t("offer_cancel_newdeal", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def get_newdeal_handler() -> ConversationHandler:
    """Create and return newdeal conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("newdeal", newdeal_command)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
            PICKUP_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pickup_start)],
            PICKUP_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pickup_end)],
            PHOTO: [
                MessageHandler(filters.PHOTO, handle_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_photo),
            ],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirmation)],
        },
        fallbacks=[CommandHandler("cancel", cancel_newdeal)],
    )
