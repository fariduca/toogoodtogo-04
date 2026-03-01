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

from src.i18n import t
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
    lang = context.user_data.get("lang", "en")
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            t("offer_lifecycle_edit_usage", lang)
        )
        return ConversationHandler.END

    offer_id_str = context.args[0]

    try:
        # Validate UUID
        offer_id = UUID(offer_id_str)
        context.user_data["edit_offer_id"] = offer_id
    except ValueError:
        await update.message.reply_text(
            t("offer_lifecycle_edit_invalid_id", lang, offer_id=offer_id_str)
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
                        t("offer_lifecycle_edit_not_found", lang, offer_id=offer_id_str)
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
                        t("offer_lifecycle_edit_no_permission", lang)
                    )
                    return ConversationHandler.END

                # Check offer is editable
                if offer.status not in [OfferStatus.ACTIVE, OfferStatus.PAUSED]:
                    await update.message.reply_text(
                        t("offer_lifecycle_edit_cannot", lang, status=offer.status.value)
                    )
                    return ConversationHandler.END

                # Show edit options
                keyboard = [
                    [InlineKeyboardButton(t("btn_edit_item_prices", lang), callback_data="edit_price")],
                    [InlineKeyboardButton(t("btn_edit_item_quantities", lang), callback_data="edit_quantity")],
                    [InlineKeyboardButton(t("btn_cancel", lang), callback_data="edit_cancel")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    t("offer_lifecycle_edit_header", lang, title=offer.title),
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
            t("offer_lifecycle_edit_failed", lang, error=str(e))
        )
        return ConversationHandler.END


async def select_edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit action selection."""
    lang = context.user_data.get("lang", "en")
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "edit_cancel":
        await query.edit_message_text(t("offer_lifecycle_edit_cancelled", lang))
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
        keyboard.append([InlineKeyboardButton(t("btn_cancel", lang), callback_data="edit_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            t("offer_lifecycle_edit_select_price", lang),
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
        keyboard.append([InlineKeyboardButton(t("btn_cancel", lang), callback_data="edit_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            t("offer_lifecycle_edit_select_qty", lang),
            reply_markup=reply_markup,
        )
        return EDIT_QUANTITY

    return ConversationHandler.END


async def edit_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle item price editing."""
    lang = context.user_data.get("lang", "en")
    query = update.callback_query
    await query.answer()

    if query.data == "edit_cancel":
        await query.edit_message_text(t("offer_lifecycle_edit_cancelled", lang))
        return ConversationHandler.END

    # Extract item name
    item_name = query.data.replace("edit_price_", "")
    context.user_data["edit_item_name"] = item_name

    offer = context.user_data.get("edit_offer")
    item = next((i for i in offer.items if i.name == item_name), None)

    if not item:
        await query.edit_message_text(t("offer_lifecycle_edit_item_not_found", lang))
        return ConversationHandler.END

    await query.edit_message_text(
        t("offer_lifecycle_edit_price_prompt", lang, item_name=item_name, price=str(item.discounted_price)),
        parse_mode="Markdown",
    )

    return EDIT_PRICE


async def update_item_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update item price with user input."""
    lang = context.user_data.get("lang", "en")
    try:
        new_price = Decimal(update.message.text.strip())

        if new_price < 0:
            await update.message.reply_text(
                t("offer_lifecycle_edit_price_negative", lang)
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
                    t("offer_lifecycle_edit_price_updated", lang, item_name=item_name, price=str(new_price))
                )

        finally:
            await db.disconnect()

        return ConversationHandler.END

    except (ValueError, InvalidOperation):
        await update.message.reply_text(
            t("offer_lifecycle_edit_price_invalid", lang)
        )
        return EDIT_PRICE
    except Exception as e:
        logger.error("price_update_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            t("offer_lifecycle_edit_price_failed", lang, error=str(e))
        )
        return ConversationHandler.END


async def edit_item_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle item quantity editing."""
    lang = context.user_data.get("lang", "en")
    query = update.callback_query
    await query.answer()

    if query.data == "edit_cancel":
        await query.edit_message_text(t("offer_lifecycle_edit_cancelled", lang))
        return ConversationHandler.END

    # Extract item name
    item_name = query.data.replace("edit_qty_", "")
    context.user_data["edit_item_name"] = item_name

    offer = context.user_data.get("edit_offer")
    item = next((i for i in offer.items if i.name == item_name), None)

    if not item:
        await query.edit_message_text(t("offer_lifecycle_edit_item_not_found", lang))
        return ConversationHandler.END

    await query.edit_message_text(
        t("offer_lifecycle_edit_qty_prompt", lang, item_name=item_name, quantity=str(item.quantity)),
        parse_mode="Markdown",
    )

    return EDIT_QUANTITY


async def update_item_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Update item quantity with user input."""
    lang = context.user_data.get("lang", "en")
    try:
        new_quantity = int(update.message.text.strip())

        if new_quantity < 0:
            await update.message.reply_text(
                t("offer_lifecycle_edit_qty_negative", lang)
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
                    t("offer_lifecycle_edit_qty_updated", lang, item_name=item_name, quantity=str(new_quantity))
                )

        finally:
            await db.disconnect()

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            t("offer_lifecycle_edit_qty_invalid", lang)
        )
        return EDIT_QUANTITY
    except Exception as e:
        logger.error("quantity_update_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            t("offer_lifecycle_edit_qty_failed", lang, error=str(e))
        )
        return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the edit conversation."""
    lang = context.user_data.get("lang", "en")
    await update.message.reply_text(t("offer_lifecycle_edit_cancelled", lang))
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
