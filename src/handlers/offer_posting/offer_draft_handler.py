"""Offer draft creation conversation handler.

Handles multi-step offer creation flow:
1. /newoffer command initiates
2. Collect offer title
3. Collect items (name, price, quantity) - repeatable
4. Collect start time
5. Collect end time
6. Create draft offer
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.logging import get_logger
from src.models.offer import Item, OfferInput, OfferStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)

# Conversation states
TITLE, ITEMS, START_TIME, END_TIME = range(4)


async def newoffer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start new offer creation conversation."""
    user_id = update.effective_user.id

    # Check if user has approved business
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    # TODO: Get user's business_id from database
    business_id = "placeholder"  # Replace with actual lookup

    if not permission_checker or not permission_checker.can_post_offer(
        business_id, user_id
    ):
        await update.message.reply_text(
            "❌ You don't have an approved business yet.\n"
            "Use /register to register your business first."
        )
        return ConversationHandler.END

    logger.info("offer_creation_started", user_id=user_id)

    # Initialize offer data storage
    context.user_data["items"] = []

    await update.message.reply_text(
        "Let's create a new offer! 🎉\n\n"
        "First, what's the title of your offer?\n"
        "Example: 'Fresh Bakery Goods - 50% Off'"
    )
    return TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate offer title."""
    title = update.message.text.strip()

    if len(title) < 3 or len(title) > 120:
        await update.message.reply_text(
            "Title must be between 3 and 120 characters. Please try again:"
        )
        return TITLE

    context.user_data["title"] = title
    logger.info("offer_title_received", title=title)

    await update.message.reply_text(
        f"Great! Title: {title}\n\n"
        "Now, let's add items to your offer.\n\n"
        "Send item details in this format:\n"
        "Item Name | Price | Quantity\n\n"
        "Example: Fresh Bread | 2.50 | 10\n\n"
        "Send 'done' when you've added all items."
    )
    return ITEMS


async def receive_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate item details."""
    text = update.message.text.strip()

    if text.lower() == "done":
        if not context.user_data.get("items"):
            await update.message.reply_text(
                "You must add at least one item. Please add an item:"
            )
            return ITEMS

        # Show summary and ask for start time
        items_summary = "\n".join(
            f"• {item['name']} - ${item['price']} ({item['quantity']} available)"
            for item in context.user_data["items"]
        )

        await update.message.reply_text(
            f"Items added:\n{items_summary}\n\n"
            "When should this offer start?\n"
            "Format: YYYY-MM-DD HH:MM\n"
            "Example: 2025-11-20 08:00"
        )
        return START_TIME

    # Parse item details
    try:
        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 3:
            raise ValueError("Expected 3 parts")

        item_name = parts[0]
        item_price = Decimal(parts[1])
        item_quantity = int(parts[2])

        if len(item_name) < 2:
            raise ValueError("Item name too short")
        if item_price <= 0:
            raise ValueError("Price must be positive")
        if item_quantity <= 0:
            raise ValueError("Quantity must be positive")

        context.user_data["items"].append(
            {"name": item_name, "price": item_price, "quantity": item_quantity}
        )

        logger.info("item_added", name=item_name, price=str(item_price), quantity=item_quantity)

        await update.message.reply_text(
            f"✅ Added: {item_name} - ${item_price} ({item_quantity} available)\n\n"
            "Add another item or send 'done' to continue."
        )
        return ITEMS

    except (ValueError, InvalidOperation) as e:
        await update.message.reply_text(
            "Invalid format. Please use:\n"
            "Item Name | Price | Quantity\n"
            "Example: Fresh Bread | 2.50 | 10"
        )
        return ITEMS


async def receive_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate start time."""
    time_str = update.message.text.strip()

    try:
        start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")

        if start_time < datetime.utcnow():
            await update.message.reply_text(
                "Start time cannot be in the past. Please provide a future time:"
            )
            return START_TIME

        context.user_data["start_time"] = start_time
        logger.info("start_time_received", start_time=start_time.isoformat())

        await update.message.reply_text(
            f"Start time: {start_time.strftime('%Y-%m-%d %H:%M')}\n\n"
            "When should this offer end?\n"
            "Format: YYYY-MM-DD HH:MM\n"
            "Example: 2025-11-20 18:00"
        )
        return END_TIME

    except ValueError:
        await update.message.reply_text(
            "Invalid time format. Please use:\n"
            "YYYY-MM-DD HH:MM\n"
            "Example: 2025-11-20 08:00"
        )
        return START_TIME


async def receive_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive end time and create draft offer."""
    time_str = update.message.text.strip()

    try:
        end_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        start_time = context.user_data["start_time"]

        if end_time <= start_time:
            await update.message.reply_text(
                "End time must be after start time. Please provide a valid end time:"
            )
            return END_TIME

        context.user_data["end_time"] = end_time
        logger.info("end_time_received", end_time=end_time.isoformat())

        # Create draft offer
        try:
            items = [
                Item(
                    name=item["name"],
                    unit_price=item["price"],
                    quantity_available=item["quantity"],
                )
                for item in context.user_data["items"]
            ]

            offer_input = OfferInput(
                title=context.user_data["title"],
                items=items,
                start_time=start_time,
                end_time=end_time,
            )

            # TODO: Save draft to database
            # repo: PostgresOfferRepository = context.bot_data.get("offer_repo")
            # draft_offer = await repo.create(offer_input)

            logger.info(
                "draft_offer_created",
                user_id=update.effective_user.id,
                title=offer_input.title,
            )

            await update.message.reply_text(
                "✅ Draft offer created!\n\n"
                f"Title: {offer_input.title}\n"
                f"Items: {len(items)}\n"
                f"Duration: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}\n\n"
                "Use /publish <offer_id> to make this offer live."
            )

        except Exception as e:
            logger.error("draft_creation_failed", error=str(e), exc_info=True)
            await update.message.reply_text(
                "❌ Failed to create draft offer. Please try again later."
            )

        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "Invalid time format. Please use:\n"
            "YYYY-MM-DD HH:MM\n"
            "Example: 2025-11-20 18:00"
        )
        return END_TIME


async def cancel_offer_creation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel offer creation conversation."""
    await update.message.reply_text(
        "Offer creation cancelled. Use /newoffer to start again."
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_offer_draft_handler() -> ConversationHandler:
    """Build and return the offer draft conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("newoffer", newoffer_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            ITEMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_item)],
            START_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_time)
            ],
            END_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_end_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_offer_creation)],
    )
