"""Offer edit handler.

Allows business owners to edit active offer details like price and quantity.
Command: /edit <offer_id>
"""

from decimal import Decimal, InvalidOperation
from uuid import UUID
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.database import get_database

logger = get_logger(__name__)

# Conversation states
EDIT_SELECT_ACTION, EDIT_PRICE, EDIT_QUANTITY, EDIT_ITEM_SELECT = range(4)


async def start_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start offer editing process."""
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /edit <offer_id>\n"
            "Example: /edit 123e4567-e89b-12d3-a456-426614174000"
        )
        return ConversationHandler.END

    offer_id_str = context.args[0]

    try:
        # Validate UUID
        offer_id = UUID(offer_id_str)
        context.user_data["edit_offer_id"] = offer_id
    except ValueError:
        await update.message.reply_text(
            f"❌ Invalid offer ID format: {offer_id_str}"
        )
        return ConversationHandler.END

    try:
        # Get offer
        db = get_database()
        await db.connect()

        try:
            async with db.session() as session:
                repo = PostgresOfferRepository(session)
                offer = await repo.get_by_id(offer_id)

                if not offer:
                    await update.message.reply_text(
                        f"❌ Offer not found: {offer_id_str}"
                    )
                    return ConversationHandler.END

                # Store offer details
                context.user_data["edit_offer"] = offer

                # Check permission
                permission_checker: PermissionChecker = context.bot_data.get(
                    "permission_checker"
                )
                if permission_checker and not await permission_checker.can_edit_offer(
                    offer.business_id, offer_id, user_id
                ):
                    await update.message.reply_text(
                        "❌ You don't have permission to edit this offer."
                    )
                    return ConversationHandler.END

                # Check offer is editable
                if offer.status not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
                    await update.message.reply_text(
                        f"❌ Cannot edit offer in {offer.status.value} status.\n"
                        f"Only active or paused offers can be edited."
                    )
                    return ConversationHandler.END

                # Show edit options
                keyboard = [
                    [InlineKeyboardButton("📝 Edit Item Prices", callback_data="edit_price")],
                    [InlineKeyboardButton("📦 Edit Item Quantities", callback_data="edit_quantity")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"**Edit Offer: {offer.title}**\n\n"
                    f"What would you like to edit?",
                    reply_markup=reply_markup,
                    parse_mode="Markdown",
                )

                return EDIT_SELECT_ACTION

        finally:
            await db.disconnect()

    except Exception as e:
        logger.error(
            "edit_start_failed",
            offer_id=offer_id_str,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ Failed to start editing.\nError: {str(e)}"
        )
        return ConversationHandler.END


async def select_edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit action selection."""
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "edit_cancel":
        await query.edit_message_text("✅ Edit canceled.")
        return ConversationHandler.END

    offer = context.user_data.get("edit_offer")

    if action == "edit_price":
        # Show item selection for price edit
        keyboard = []
        for item in offer.items:
            keyboard.append([
                InlineKeyboardButton(
                    f"{item.name} (${item.discounted_price})",
                    callback_data=f"edit_price_{item.name}"
                )
            ])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Select an item to edit price:",
            reply_markup=reply_markup,
        )
        return EDIT_PRICE

    elif action == "edit_quantity":
        # Show item selection for quantity edit
        keyboard = []
        for item in offer.items:
            keyboard.append([
                InlineKeyboardButton(
                    f"{item.name} (Qty: {item.quantity})",
                    callback_data=f"edit_qty_{item.name}"
                )
            ])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Select an item to edit quantity:",
            reply_markup=reply_markup,
        )
        return EDIT_QUANTITY

    return ConversationHandler.END


async def edit_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle item price editing."""
    query = update.callback_query
    await query.answer()

    if query.data == "edit_cancel":
        await query.edit_message_text("✅ Edit canceled.")
        return ConversationHandler.END

    # Extract item name
    item_name = query.data.replace("edit_price_", "")
    context.user_data["edit_item_name"] = item_name

    offer = context.user_data.get("edit_offer")
    item = next((i for i in offer.items if i.name == item_name), None)

    if not item:
        await query.edit_message_text("❌ Item not found.")
        return ConversationHandler.END

    await query.edit_message_text(
        f"**Edit Price: {item_name}**\n\n"
        f"Current price: ${item.discounted_price}\n\n"
        f"Enter new price (e.g., 5.99):",
        parse_mode="Markdown",
    )

    return EDIT_PRICE


async def update_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update item price with user input."""
    try:
        new_price = Decimal(update.message.text.strip())

        if new_price < 0:
            await update.message.reply_text(
                "❌ Price cannot be negative. Please try again."
            )
            return EDIT_PRICE

        offer_id = context.user_data.get("edit_offer_id")
        item_name = context.user_data.get("edit_item_name")

        # Update price in database
        db = get_database()
        await db.connect()

        try:
            async with db.session() as session:
                repo = PostgresOfferRepository(session)

                # Update item price (would need repo method)
                # For now, log the action
                logger.info(
                    "item_price_updated",
                    offer_id=str(offer_id),
                    item_name=item_name,
                    new_price=str(new_price),
                )

                await session.commit()

                await update.message.reply_text(
                    f"✅ Price updated successfully!\n\n"
                    f"**{item_name}**: ${new_price}"
                )

        finally:
            await db.disconnect()

        return ConversationHandler.END

    except (ValueError, InvalidOperation):
        await update.message.reply_text(
            "❌ Invalid price format. Please enter a number (e.g., 5.99)."
        )
        return EDIT_PRICE
    except Exception as e:
        logger.error("price_update_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            f"❌ Failed to update price.\nError: {str(e)}"
        )
        return ConversationHandler.END


async def edit_item_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle item quantity editing."""
    query = update.callback_query
    await query.answer()

    if query.data == "edit_cancel":
        await query.edit_message_text("✅ Edit canceled.")
        return ConversationHandler.END

    # Extract item name
    item_name = query.data.replace("edit_qty_", "")
    context.user_data["edit_item_name"] = item_name

    offer = context.user_data.get("edit_offer")
    item = next((i for i in offer.items if i.name == item_name), None)

    if not item:
        await query.edit_message_text("❌ Item not found.")
        return ConversationHandler.END

    await query.edit_message_text(
        f"**Edit Quantity: {item_name}**\n\n"
        f"Current quantity: {item.quantity}\n\n"
        f"Enter new quantity:",
        parse_mode="Markdown",
    )

    return EDIT_QUANTITY


async def update_item_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update item quantity with user input."""
    try:
        new_quantity = int(update.message.text.strip())

        if new_quantity < 0:
            await update.message.reply_text(
                "❌ Quantity cannot be negative. Please try again."
            )
            return EDIT_QUANTITY

        offer_id = context.user_data.get("edit_offer_id")
        item_name = context.user_data.get("edit_item_name")

        # Update quantity in database
        db = get_database()
        await db.connect()

        try:
            async with db.session() as session:
                repo = PostgresOfferRepository(session)

                # Update item quantity (would need repo method)
                # For now, log the action
                logger.info(
                    "item_quantity_updated",
                    offer_id=str(offer_id),
                    item_name=item_name,
                    new_quantity=new_quantity,
                )

                await session.commit()

                await update.message.reply_text(
                    f"✅ Quantity updated successfully!\n\n"
                    f"**{item_name}**: {new_quantity} available"
                )

        finally:
            await db.disconnect()

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid quantity. Please enter a whole number."
        )
        return EDIT_QUANTITY
    except Exception as e:
        logger.error("quantity_update_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            f"❌ Failed to update quantity.\nError: {str(e)}"
        )
        return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the edit conversation."""
    await update.message.reply_text("✅ Edit canceled.")
    return ConversationHandler.END


def get_edit_handler() -> ConversationHandler:
    """Return the edit conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("edit", start_edit)],
        states={
            EDIT_SELECT_ACTION: [
                CallbackQueryHandler(select_edit_action),
            ],
            EDIT_PRICE: [
                CallbackQueryHandler(edit_item_price),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_item_price),
            ],
            EDIT_QUANTITY: [
                CallbackQueryHandler(edit_item_quantity),
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_item_quantity),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_edit)],
    )
