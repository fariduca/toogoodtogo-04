"""Reservation handlers for customers."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.reservation import ReservationStatus
from src.models.user import UserRole
from src.services.reservation_flow import ReservationFlowService
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def handle_reserve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle reservation initiation."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: reserve:{offer_id}:{quantity}
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.edit_message_text("❌ Invalid reservation request")
        return
    
    from uuid import UUID
    offer_id = UUID(parts[1])
    quantity = int(parts[2])
    
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        await query.edit_message_text("❌ Please use /start to register first.")
        return
    
    if user.role != UserRole.CUSTOMER:
        await query.edit_message_text("❌ Only customers can make reservations.")
        return
    
    # Get offer and business details
    offer = await offer_repo.get_by_id(offer_id)
    if not offer or not offer.available_for_reservation:
        await query.edit_message_text("❌ This offer is no longer available.")
        return
    
    business = await business_repo.get_by_id(offer.business_id)
    if not business:
        await query.edit_message_text("❌ Business not found.")
        return
    
    # Validate quantity
    if quantity > offer.quantity_remaining:
        await query.edit_message_text(
            f"❌ Only {offer.quantity_remaining} units available.\n"
            "Please try again with a lower quantity."
        )
        return
    
    # Calculate total
    total_price = float(offer.price_per_unit) * quantity
    
    # Show confirmation prompt
    text = (
        "📋 **Confirm Reservation**\n\n"
        f"**Deal:** {offer.title}\n"
        f"**Business:** {business.business_name}\n"
        f"**Quantity:** {quantity} unit{'s' if quantity > 1 else ''}\n"
        f"**Total:** ${total_price:.2f}\n\n"
        f"**Pickup at:**\n"
        f"{business.venue.street_address}\n"
        f"{business.venue.city}, {business.venue.postal_code}\n\n"
        f"**Pickup Window:**\n"
        f"{offer.pickup_start_time.strftime('%b %d, %H:%M')} - {offer.pickup_end_time.strftime('%H:%M')}\n\n"
        f"💳 **Payment on-site** (cash or card)\n\n"
        "Ready to reserve?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Reservation", callback_data=f"confirm_reserve:{offer_id}:{quantity}")],
        [InlineKeyboardButton("« Back", callback_data=f"offer_detail:{offer_id}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_confirm_reserve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle confirmed reservation with atomic inventory management."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: confirm_reserve:{offer_id}:{quantity}
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.edit_message_text("❌ Invalid confirmation request")
        return
    
    from uuid import UUID
    offer_id = UUID(parts[1])
    quantity = int(parts[2])
    
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    reservation_flow_service: ReservationFlowService = context.bot_data.get("reservation_flow_service")
    
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        await query.edit_message_text("❌ User not found.")
        return
    
    # Create reservation with atomic inventory management
    if not reservation_flow_service:
        # Fallback: create reservation directly (less safe)
        logger.warning("reservation_flow_service_not_available", using_fallback=True)
        
        reservation_repo: PostgresReservationRepository = context.bot_data["reservation_repo"]
        offer = await offer_repo.get_by_id(offer_id)
        
        if not offer or quantity > offer.quantity_remaining:
            await query.edit_message_text("❌ Reservation failed. Offer no longer available.")
            return
        
        # Decrement inventory
        success = await offer_repo.decrement_quantity(offer_id, quantity)
        if not success:
            await query.edit_message_text("❌ Failed to reserve. Please try again.")
            return
        
        # Create reservation
        from src.models.reservation import ReservationInput
        from decimal import Decimal
        
        total_price = Decimal(str(quantity)) * offer.price_per_unit
        reservation_input = ReservationInput(
            offer_id=offer_id,
            customer_id=user.id,
            quantity=quantity,
            unit_price=offer.price_per_unit,
            total_price=total_price,
            currency=offer.currency,
            pickup_start_time=offer.pickup_start_time,
            pickup_end_time=offer.pickup_end_time,
        )
        
        reservation = await reservation_repo.create(reservation_input)
        order_id = reservation.order_id
        success = True
        message = "Reservation confirmed!"
        
    else:
        # Use reservation flow service with Redis locks
        success, message, order_id = await reservation_flow_service.create_reservation(
            customer_id=user.id,
            offer_id=offer_id,
            quantity=quantity,
        )
    
    if not success:
        await query.edit_message_text(
            f"❌ {message}\n\n"
            "The deal may have just sold out or is locked by another customer. "
            "Please try again or browse other offers."
        )
        return
    
    # Get updated offer and business info
    offer = await offer_repo.get_by_id(offer_id)
    business = await business_repo.get_by_id(offer.business_id)
    
    total_price = float(offer.price_per_unit) * quantity
    
    # Send success message
    text = (
        "🎉 **Reservation Confirmed!**\n\n"
        f"**Order ID:** `{order_id}`\n"
        f"**Deal:** {offer.title}\n"
        f"**Quantity:** {quantity} unit{'s' if quantity > 1 else ''}\n"
        f"**Amount to Pay:** ${total_price:.2f}\n\n"
        "📍 **Pickup Location:**\n"
        f"{business.business_name}\n"
        f"{business.venue.street_address}\n"
        f"{business.venue.city}, {business.venue.postal_code}\n"
        f"📞 {business.contact_phone or 'N/A'}\n\n"
        "🕐 **Pickup Window:**\n"
        f"{offer.pickup_start_time.strftime('%b %d, %H:%M')} - {offer.pickup_end_time.strftime('%H:%M')}\n\n"
        "💳 **Payment:** Pay on-site (cash or card)\n\n"
        "📱 Show this Order ID when picking up your order.\n"
        "Use /myreservations to view all your reservations."
    )
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Browse More Deals", callback_data="browse:all:0")],
        [InlineKeyboardButton("📋 My Reservations", callback_data="my_reservations")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    logger.info(
        "reservation_confirmed",
        order_id=order_id,
        customer_id=user.id,
        offer_id=str(offer_id),
        quantity=quantity,
    )


async def my_reservations_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show customer's active reservations."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    reservation_repo: PostgresReservationRepository = context.bot_data["reservation_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start to register first.")
        return
    
    # Get active reservations
    reservations = await reservation_repo.get_active_by_customer(user.id)
    
    if not reservations:
        await update.message.reply_text(
            "📭 You don't have any active reservations.\n\n"
            "Use /browse to discover deals!"
        )
        return
    
    text = "📋 **Your Reservations**\n\n"
    
    for reservation in reservations:
        offer = await offer_repo.get_by_id(reservation.offer_id)
        business = await business_repo.get_by_id(offer.business_id) if offer else None
        
        if not offer or not business:
            continue
        
        # Build reservation card
        card_text = (
            f"**Order ID:** `{reservation.order_id}`\n"
            f"**Deal:** {offer.title}\n"
            f"**Business:** {business.business_name}\n"
            f"**Quantity:** {reservation.quantity}\n"
            f"**Total:** €{float(reservation.total_price):.2f}\n"
            f"**Pickup:** {reservation.pickup_start_time.strftime('%b %d, %H:%M')} - {reservation.pickup_end_time.strftime('%H:%M')}\n"
            f"**Location:** {business.street_address}, {business.city}\n"
            f"📞 {business.contact_phone or 'N/A'}\n"
        )
        
        # Add cancel button only if pickup_end_time hasn't passed
        from datetime import datetime
        now = datetime.utcnow()
        keyboard = []
        
        if now < reservation.pickup_end_time:
            keyboard.append([
                InlineKeyboardButton("🗑️ Cancel Reservation", callback_data=f"cancel_reservation:{reservation.id}")
            ])
        
        if keyboard:
            from telegram import InlineKeyboardMarkup
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(card_text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await update.message.reply_text(card_text, parse_mode="Markdown")
        
        text = ""  # Clear text since we're sending individual cards
    
    if text:  # If there's remaining text (shouldn't happen with new logic)
        await update.message.reply_text(text, parse_mode="Markdown")


async def handle_my_reservations_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle my_reservations callback from inline button."""
    query = update.callback_query
    await query.answer()
    
    # Reuse the command logic
    update.message = query.message
    await my_reservations_command(update, context)


def get_reservation_handlers() -> list:
    """Return list of reservation-related handlers."""
    return [
        CallbackQueryHandler(handle_reserve, pattern=r"^reserve:"),
        CallbackQueryHandler(handle_confirm_reserve, pattern=r"^confirm_reserve:"),
        CommandHandler("myreservations", my_reservations_command),
        CallbackQueryHandler(handle_my_reservations_callback, pattern=r"^my_reservations$"),
    ]
