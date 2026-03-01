"""Cancel reservation handler for customers."""

from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from uuid import UUID

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.reservation import ReservationStatus
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def handle_cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel reservation callback - show confirmation prompt."""
    query = update.callback_query
    await query.answer()
    
    reservation_repo: PostgresReservationRepository = context.bot_data["reservation_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract reservation_id from callback_data (format: "cancel_reservation:uuid")
    reservation_id_str = query.data.split(":")[1]
    reservation_id = UUID(reservation_id_str)
    
    # Get reservation
    reservation = await reservation_repo.get_by_id(reservation_id)
    
    if not reservation:
        await query.edit_message_text(t("err_reservation_not_found", lang))
        return
    
    # Validate reservation status
    if reservation.status != ReservationStatus.CONFIRMED:
        await query.edit_message_text(
            t("reserve_already_status", lang, status=reservation.status.value.lower())
        )
        return
    
    # Validate time - can only cancel before pickup_end_time
    now = datetime.utcnow()
    if now >= reservation.pickup_end_time:
        await query.edit_message_text(
            t("reserve_cancel_expired", lang, end_time=reservation.pickup_end_time.strftime('%H:%M'))
        )
        return
    
    # Get offer details
    offer = await offer_repo.get_by_id(reservation.offer_id)
    
    if not offer:
        await query.edit_message_text(t("err_reservation_not_found", lang))
        return
    
    # Show confirmation prompt
    keyboard = [
        [
            InlineKeyboardButton(t("btn_yes_cancel", lang), callback_data=f"confirm_cancel_reservation:{reservation_id}"),
            InlineKeyboardButton(t("btn_keep_reservation", lang), callback_data=f"keep_reservation:{reservation_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        t("reserve_cancel_prompt", lang,
          order_id=reservation.order_id,
          title=offer.title,
          quantity=reservation.quantity,
          total=f"€{reservation.total_price}"),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_confirm_cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmed cancel reservation action."""
    query = update.callback_query
    await query.answer()
    
    reservation_repo: PostgresReservationRepository = context.bot_data["reservation_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Resolve user language
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    # Extract reservation_id from callback_data (format: "confirm_cancel_reservation:uuid")
    reservation_id_str = query.data.split(":")[1]
    reservation_id = UUID(reservation_id_str)
    
    # Get reservation
    reservation = await reservation_repo.get_by_id(reservation_id)
    
    if not reservation:
        await query.edit_message_text(t("err_reservation_not_found", lang))
        return
    
    # Validate time again
    now = datetime.utcnow()
    if now >= reservation.pickup_end_time:
        await query.edit_message_text(
            t("reserve_cancel_expired_short", lang)
        )
        return
    
    try:
        # Cancel reservation and return units to inventory
        updated_reservation = await reservation_repo.cancel(
            reservation_id=reservation_id,
            reason="Customer requested cancellation"
        )
        
        await query.edit_message_text(
            t("reserve_cancelled_success", lang, order_id=reservation.order_id, quantity=reservation.quantity),
            parse_mode="Markdown"
        )
        
        logger.info(
            "reservation_cancelled",
            reservation_id=str(reservation_id),
            order_id=reservation.order_id,
            customer_id=reservation.customer_id,
            offer_id=str(reservation.offer_id),
            quantity_returned=reservation.quantity
        )
    
    except Exception as e:
        logger.error(
            "reservation_cancellation_failed",
            reservation_id=str(reservation_id),
            error=str(e),
            exc_info=True
        )
        await query.edit_message_text(t("reserve_cancel_failed", lang))


async def handle_keep_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle keep reservation action (cancelled cancel)."""
    query = update.callback_query
    await query.answer()
    
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    await query.edit_message_text(t("reserve_kept", lang))


def get_cancel_reservation_handler() -> CallbackQueryHandler:
    """Create cancel reservation callback handler."""
    return CallbackQueryHandler(handle_cancel_reservation, pattern=r"^cancel_reservation:")


def get_confirm_cancel_handler() -> CallbackQueryHandler:
    """Create confirm cancel callback handler."""
    return CallbackQueryHandler(handle_confirm_cancel_reservation, pattern=r"^confirm_cancel_reservation:")


def get_keep_reservation_handler() -> CallbackQueryHandler:
    """Create keep reservation callback handler."""
    return CallbackQueryHandler(handle_keep_reservation, pattern=r"^keep_reservation:")
