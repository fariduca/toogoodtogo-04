"""Cancel reservation handler for customers."""

from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from uuid import UUID

from src.logging import get_logger
from src.models.reservation import ReservationStatus
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


async def handle_cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel reservation callback - show confirmation prompt."""
    query = update.callback_query
    await query.answer()
    
    reservation_repo: PostgresReservationRepository = context.bot_data["reservation_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract reservation_id from callback_data (format: "cancel_reservation:uuid")
    reservation_id_str = query.data.split(":")[1]
    reservation_id = UUID(reservation_id_str)
    
    # Get reservation
    reservation = await reservation_repo.get_by_id(reservation_id)
    
    if not reservation:
        await query.edit_message_text("❌ Reservation not found.")
        return
    
    # Validate reservation status
    if reservation.status != ReservationStatus.CONFIRMED:
        await query.edit_message_text(
            f"❌ This reservation has already been {reservation.status.value.lower()}."
        )
        return
    
    # Validate time - can only cancel before pickup_end_time
    now = datetime.utcnow()
    if now >= reservation.pickup_end_time:
        await query.edit_message_text(
            "❌ Cannot cancel reservation after the pickup window has ended.\n\n"
            f"Pickup window ended at {reservation.pickup_end_time.strftime('%H:%M')}."
        )
        return
    
    # Get offer details
    offer = await offer_repo.get_by_id(reservation.offer_id)
    
    if not offer:
        await query.edit_message_text("❌ Associated offer not found.")
        return
    
    # Show confirmation prompt
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, cancel", callback_data=f"confirm_cancel_reservation:{reservation_id}"),
            InlineKeyboardButton("❌ Keep reservation", callback_data=f"keep_reservation:{reservation_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🗑️ **Cancel Reservation?**\n\n"
        f"**Order ID:** `{reservation.order_id}`\n"
        f"**Deal:** {offer.title}\n"
        f"**Quantity:** {reservation.quantity} units\n"
        f"**Total:** €{reservation.total_price}\n\n"
        "⚠️ Cancelling will return the items to inventory for others to reserve.\n\n"
        "Are you sure you want to cancel?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def handle_confirm_cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmed cancel reservation action."""
    query = update.callback_query
    await query.answer()
    
    reservation_repo: PostgresReservationRepository = context.bot_data["reservation_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    # Extract reservation_id from callback_data (format: "confirm_cancel_reservation:uuid")
    reservation_id_str = query.data.split(":")[1]
    reservation_id = UUID(reservation_id_str)
    
    # Get reservation
    reservation = await reservation_repo.get_by_id(reservation_id)
    
    if not reservation:
        await query.edit_message_text("❌ Reservation not found.")
        return
    
    # Validate time again
    now = datetime.utcnow()
    if now >= reservation.pickup_end_time:
        await query.edit_message_text(
            "❌ Cannot cancel reservation after the pickup window has ended."
        )
        return
    
    try:
        # Cancel reservation and return units to inventory
        updated_reservation = await reservation_repo.cancel(
            reservation_id=reservation_id,
            reason="Customer requested cancellation"
        )
        
        await query.edit_message_text(
            f"✅ **Reservation Cancelled**\n\n"
            f"Order ID `{reservation.order_id}` has been cancelled.\n"
            f"{reservation.quantity} units have been returned to inventory.\n\n"
            "Use /browse to find other deals!",
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
        await query.edit_message_text(
            "❌ Failed to cancel reservation. Please try again or contact support."
        )


async def handle_keep_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle keep reservation action (cancelled cancel)."""
    query = update.callback_query
    await query.answer("Reservation kept")
    
    await query.edit_message_text(
        "✅ Reservation kept. Use /myreservations to view your reservations."
    )


def get_cancel_reservation_handler() -> CallbackQueryHandler:
    """Create cancel reservation callback handler."""
    return CallbackQueryHandler(handle_cancel_reservation, pattern=r"^cancel_reservation:")


def get_confirm_cancel_handler() -> CallbackQueryHandler:
    """Create confirm cancel callback handler."""
    return CallbackQueryHandler(handle_confirm_cancel_reservation, pattern=r"^confirm_cancel_reservation:")


def get_keep_reservation_handler() -> CallbackQueryHandler:
    """Create keep reservation callback handler."""
    return CallbackQueryHandler(handle_keep_reservation, pattern=r"^keep_reservation:")
