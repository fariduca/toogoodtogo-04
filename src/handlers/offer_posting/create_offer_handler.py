"""Create new deal handler for business users."""

from datetime import datetime, timedelta
from decimal import Decimal

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

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
            "❌ You need to register first. Use /start to begin."
        )
        return ConversationHandler.END
    
    if user.role != UserRole.BUSINESS:
        await update.message.reply_text(
            "❌ Only business accounts can post deals. "
            "If you're a business, please register with /start"
        )
        return ConversationHandler.END
    
    # Get user's business
    businesses = await business_repo.get_by_owner_id(user.id)
    
    if not businesses:
        await update.message.reply_text(
            "❌ You don't have a registered business yet. Use /start to register."
        )
        return ConversationHandler.END
    
    business = businesses[0]  # Use first business
    
    # Check permissions
    permission_checker: PermissionChecker = context.bot_data["permission_checker"]
    if not permission_checker.can_post_offer(user, business):
        await update.message.reply_text(
            "❌ Your business is still pending verification. "
            "You'll be notified when you can start posting deals."
        )
        return ConversationHandler.END
    
    # Store business in context
    context.user_data["business_id"] = str(business.id)
    
    await update.message.reply_text(
        f"🎉 Let's create a new deal for {business.business_name}!\n\n"
        "First, what's the title of your deal?\n"
        "Example: Fresh Bakery Box, Mixed Produce Bag, etc.\n\n"
        "Type /cancel anytime to stop."
    )
    
    return TITLE


async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle title input."""
    title = update.message.text.strip()
    
    if len(title) < 3 or len(title) > 100:
        await update.message.reply_text(
            "❌ Title must be between 3 and 100 characters. Please try again:"
        )
        return TITLE
    
    context.user_data["title"] = title
    
    await update.message.reply_text(
        "Great! Now provide a description (10-200 characters):\n"
        "Example: Mixed seasonal produce, perfect for soups and salads"
    )
    return DESCRIPTION


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle description input."""
    description = update.message.text.strip()
    
    if len(description) < 10 or len(description) > 200:
        await update.message.reply_text(
            "❌ Description must be between 10 and 200 characters. Please try again:"
        )
        return DESCRIPTION
    
    context.user_data["description"] = description
    
    await update.message.reply_text(
        "What category best describes this deal?\n"
        "Options: MEALS, BAKERY, PRODUCE, OTHER\n\n"
        "Reply with one of these options:"
    )
    return CATEGORY


async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category input."""
    category_text = update.message.text.strip().upper()
    
    try:
        category = OfferCategory(category_text)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid category. Please choose: MEALS, BAKERY, PRODUCE, or OTHER"
        )
        return CATEGORY
    
    context.user_data["category"] = category.value
    
    await update.message.reply_text(
        "What's the price per unit? (e.g., 5.99)\n"
        "This is the discounted price customers will pay:"
    )
    return PRICE


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price input."""
    try:
        price = Decimal(update.message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Invalid price. Please enter a positive number (e.g., 5.99):"
        )
        return PRICE
    
    context.user_data["price"] = str(price)
    
    await update.message.reply_text(
        "How many units are available?\n"
        "Enter a whole number (e.g., 10):"
    )
    return QUANTITY


async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input."""
    try:
        quantity = int(update.message.text.strip())
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except (ValueError, Exception):
        await update.message.reply_text(
            "❌ Invalid quantity. Please enter a positive whole number:"
        )
        return QUANTITY
    
    context.user_data["quantity"] = quantity
    
    await update.message.reply_text(
        "When can customers start picking up?\n"
        "Enter the start time in format: YYYY-MM-DD HH:MM\n"
        "Example: 2025-11-30 14:00"
    )
    return PICKUP_START


async def handle_pickup_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup start time input."""
    try:
        pickup_start = datetime.strptime(update.message.text.strip(), "%Y-%m-%d %H:%M")
        
        if pickup_start <= datetime.utcnow():
            await update.message.reply_text(
                "❌ Pickup start time must be in the future. Please try again:"
            )
            return PICKUP_START
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Use: YYYY-MM-DD HH:MM\n"
            "Example: 2025-11-30 14:00"
        )
        return PICKUP_START
    
    context.user_data["pickup_start"] = pickup_start.isoformat()
    
    await update.message.reply_text(
        "When should pickup end?\n"
        "Enter the end time in format: YYYY-MM-DD HH:MM\n"
        "Example: 2025-11-30 18:00"
    )
    return PICKUP_END


async def handle_pickup_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup end time input."""
    try:
        pickup_end = datetime.strptime(update.message.text.strip(), "%Y-%m-%d %H:%M")
        pickup_start = datetime.fromisoformat(context.user_data["pickup_start"])
        
        if pickup_end <= pickup_start:
            await update.message.reply_text(
                "❌ Pickup end time must be after start time. Please try again:"
            )
            return PICKUP_END
        
        time_window = pickup_end - pickup_start
        if time_window > timedelta(hours=24):
            await update.message.reply_text(
                "❌ Pickup window cannot exceed 24 hours. Please enter a shorter end time:"
            )
            return PICKUP_END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Use: YYYY-MM-DD HH:MM\n"
            "Example: 2025-11-30 18:00"
        )
        return PICKUP_END
    
    context.user_data["pickup_end"] = pickup_end.isoformat()
    
    await update.message.reply_text(
        "Would you like to add a photo of your deal?\n"
        "Send a photo now, or type SKIP to continue without a photo."
    )
    return PHOTO


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle photo upload."""
    if update.message.text and update.message.text.strip().upper() == "SKIP":
        context.user_data["photo_url"] = None
        return await show_confirmation(update, context)
    
    if not update.message.photo:
        await update.message.reply_text(
            "Please send a photo, or type SKIP to continue without one."
        )
        return PHOTO
    
    # Get largest photo
    photo = update.message.photo[-1]
    context.user_data["photo_file_id"] = photo.file_id
    
    # TODO: Upload to Azure Blob Storage using ImageProcessingService
    # For now, store file_id for later download
    
    await update.message.reply_text("✅ Photo received!")
    
    return await show_confirmation(update, context)


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show deal summary and ask for confirmation."""
    pickup_start = datetime.fromisoformat(context.user_data["pickup_start"])
    pickup_end = datetime.fromisoformat(context.user_data["pickup_end"])
    
    summary = (
        "📋 Deal Summary:\n\n"
        f"**Title:** {context.user_data['title']}\n"
        f"**Description:** {context.user_data['description']}\n"
        f"**Category:** {context.user_data['category']}\n"
        f"**Price:** ${context.user_data['price']} per unit\n"
        f"**Quantity:** {context.user_data['quantity']} units\n"
        f"**Pickup Window:** {pickup_start.strftime('%b %d, %H:%M')} - {pickup_end.strftime('%H:%M')}\n"
        f"**Photo:** {'Yes ✅' if context.user_data.get('photo_file_id') else 'No'}\n\n"
        "Reply YES to publish this deal, or NO to cancel."
    )
    
    await update.message.reply_text(summary)
    return CONFIRM


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle final confirmation and create offer."""
    response = update.message.text.strip().upper()
    
    if response != "YES":
        await update.message.reply_text(
            "❌ Deal creation cancelled. Use /newdeal to start over.",
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
        f"🎉 Deal published successfully!\n\n"
        f"**{offer.title}**\n"
        f"Customers can now discover and reserve your deal.\n\n"
        f"Share this link to promote your deal:\n{share_link}\n\n"
        "Commands:\n"
        "• /mydeals — Manage your deals\n"
        "• /newdeal — Create another deal",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_newdeal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel deal creation."""
    context.user_data.clear()
    await update.message.reply_text(
        "Deal creation cancelled.",
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
