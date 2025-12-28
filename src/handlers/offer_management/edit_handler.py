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

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)

# Conversation states for edit flow
EDIT_PRICE, EDIT_QUANTITY, EDIT_DESCRIPTION, EDIT_PICKUP_END = range(4)


async def handle_edit_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit offer callback - show edit options."""
    query = update.callback_query
    await query.answer()
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract offer_id from callback_data (format: "edit_offer:uuid")
    offer_id_str = query.data.split(":")[1]
    offer_id = UUID(offer_id_str)
    
    # Get offer
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Offer not found.")
        return ConversationHandler.END
    
    # Validate state
    if offer.state not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
        await query.edit_message_text(
            f"❌ Cannot edit offer in {offer.state.value} state."
        )
        return ConversationHandler.END
    
    # Store offer_id in context
    context.user_data["edit_offer_id"] = str(offer_id)
    context.user_data["edit_offer"] = offer
    
    # Show edit options
    keyboard = [
        [InlineKeyboardButton("💰 Edit Price", callback_data="edit_field:price")],
        [InlineKeyboardButton("📦 Edit Quantity", callback_data="edit_field:quantity")],
        [InlineKeyboardButton("📝 Edit Description", callback_data="edit_field:description")],
        [InlineKeyboardButton("⏰ Edit Pickup Time", callback_data="edit_field:pickup_end")],
        [InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✏️ **Edit {offer.title}**\n\n"
        f"Current settings:\n"
        f"• Price: €{offer.price_per_unit}\n"
        f"• Quantity: {offer.quantity_remaining}/{offer.quantity_total}\n"
        f"• Description: {offer.description[:50]}...\n"
        f"• Pickup ends: {offer.pickup_end_time.strftime('%H:%M')}\n\n"
        "What would you like to edit?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END  # We'll handle field selection via callbacks


async def handle_edit_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    
    field = query.data.split(":")[1]
    offer = context.user_data.get("edit_offer")
    
    if not offer:
        await query.edit_message_text("❌ Session expired. Use /myoffers to try again.")
        return ConversationHandler.END
    
    if field == "price":
        await query.edit_message_text(
            f"💰 **Edit Price**\n\n"
            f"Current price: €{offer.price_per_unit}\n\n"
            f"Enter new price (e.g., 5.50):\n"
            f"Type /cancel to abort."
        )
        return EDIT_PRICE
    
    elif field == "quantity":
        await query.edit_message_text(
            f"📦 **Edit Quantity**\n\n"
            f"Current remaining: {offer.quantity_remaining}\n\n"
            f"Enter new quantity available:\n"
            f"Type /cancel to abort."
        )
        return EDIT_QUANTITY
    
    elif field == "description":
        await query.edit_message_text(
            f"📝 **Edit Description**\n\n"
            f"Current: {offer.description}\n\n"
            f"Enter new description (10-200 characters):\n"
            f"Type /cancel to abort."
        )
        return EDIT_DESCRIPTION
    
    elif field == "pickup_end":
        await query.edit_message_text(
            f"⏰ **Edit Pickup End Time**\n\n"
            f"Current: {offer.pickup_end_time.strftime('%H:%M')}\n\n"
            f"Enter new end time (format: HH:MM, e.g., 18:30):\n"
            f"Type /cancel to abort."
        )
        return EDIT_PICKUP_END
    
    return ConversationHandler.END


async def handle_edit_price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle price edit input."""
    try:
        new_price = Decimal(update.message.text.strip())
        
        if new_price <= 0:
            await update.message.reply_text("❌ Price must be greater than 0. Try again:")
            return EDIT_PRICE
        
        # Update offer
        offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
        offer_id = UUID(context.user_data["edit_offer_id"])
        offer = await offer_repo.get_by_id(offer_id)
        
        offer.price_per_unit = new_price
        updated = await offer_repo.update(offer)
        
        await update.message.reply_text(
            f"✅ Price updated to €{new_price}\n\n"
            "Use /myoffers to see your offers."
        )
        
        logger.info(
            "offer_price_updated",
            offer_id=str(offer_id),
            new_price=str(new_price)
        )
        
        return ConversationHandler.END
    
    except (ValueError, decimal.InvalidOperation):
        await update.message.reply_text(
            "❌ Invalid price format. Enter a number (e.g., 5.50):"
        )
        return EDIT_PRICE


async def handle_edit_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity edit input."""
    try:
        new_quantity = int(update.message.text.strip())
        
        if new_quantity < 0:
            await update.message.reply_text("❌ Quantity cannot be negative. Try again:")
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
            f"✅ Quantity updated to {new_quantity} units\n\n"
            "Use /myoffers to see your offers."
        )
        
        logger.info(
            "offer_quantity_updated",
            offer_id=str(offer_id),
            new_quantity=new_quantity
        )
        
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid quantity. Enter a whole number:"
        )
        return EDIT_QUANTITY


async def handle_edit_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle description edit input."""
    new_description = update.message.text.strip()
    
    if len(new_description) < 10 or len(new_description) > 200:
        await update.message.reply_text(
            "❌ Description must be 10-200 characters. Try again:"
        )
        return EDIT_DESCRIPTION
    
    # Update offer
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    offer_id = UUID(context.user_data["edit_offer_id"])
    offer = await offer_repo.get_by_id(offer_id)
    
    offer.description = new_description
    updated = await offer_repo.update(offer)
    
    await update.message.reply_text(
        f"✅ Description updated\n\n"
        "Use /myoffers to see your offers."
    )
    
    logger.info(
        "offer_description_updated",
        offer_id=str(offer_id)
    )
    
    return ConversationHandler.END


async def handle_edit_pickup_end_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle pickup end time edit input."""
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
                f"❌ End time must be after start time "
                f"({offer.pickup_start_time.strftime('%H:%M')}). Try again:"
            )
            return EDIT_PICKUP_END
        
        # Validate it's in the future
        if new_end_time <= datetime.utcnow():
            await update.message.reply_text(
                "❌ End time must be in the future. Try again:"
            )
            return EDIT_PICKUP_END
        
        offer.pickup_end_time = new_end_time
        updated = await offer_repo.update(offer)
        
        await update.message.reply_text(
            f"✅ Pickup end time updated to {new_end_time.strftime('%H:%M')}\n\n"
            "Use /myoffers to see your offers."
        )
        
        logger.info(
            "offer_pickup_end_updated",
            offer_id=str(offer_id),
            new_end_time=new_end_time.isoformat()
        )
        
        return ConversationHandler.END
    
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Invalid time format. Use HH:MM (e.g., 18:30):"
        )
        return EDIT_PICKUP_END


async def handle_edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit cancellation."""
    query = update.callback_query
    if query:
        await query.answer("Cancelled")
        await query.edit_message_text("✅ Edit cancelled. Use /myoffers to manage offers.")
    else:
        await update.message.reply_text("✅ Edit cancelled. Use /myoffers to manage offers.")
    
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
