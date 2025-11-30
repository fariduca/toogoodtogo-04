"""Browse handler for customer discovery of offers."""

from datetime import datetime
from math import ceil

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.models.user import UserRole
from src.services.discovery_ranking import DiscoveryRankingService
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)

OFFERS_PER_PAGE = 5


async def browse_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /browse command to show available offers."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Get or create user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        await update.message.reply_text(
            "Welcome! Please use /start to register first."
        )
        return
    
    # Show filter options
    keyboard = [
        [InlineKeyboardButton("🌍 All Offers", callback_data="browse:all:0")],
        [InlineKeyboardButton("📍 Nearby (5km)", callback_data="browse:nearby:0")],
        [InlineKeyboardButton("⏰ Ending Soon", callback_data="browse:ending:0")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 Browse Deals\n\n"
        "Choose how you'd like to discover deals:",
        reply_markup=reply_markup,
    )


async def handle_browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle browse filter and pagination callbacks."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: browse:{filter}:{page}
    parts = query.data.split(":")
    if len(parts) != 3:
        await query.edit_message_text("❌ Invalid request")
        return
    
    filter_type = parts[1]
    page = int(parts[2])
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    telegram_user = update.effective_user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    # Get all active offers
    offers = await offer_repo.get_active_offers()
    
    if not offers:
        await query.edit_message_text(
            "😔 No deals available right now.\n"
            "Check back soon for new offers!"
        )
        return
    
    # Apply filters
    filtered_offers = offers
    
    if filter_type == "nearby" and user and user.last_location_lat and user.last_location_lon:
        # Filter by location using discovery service
        discovery_service: DiscoveryRankingService = context.bot_data.get("discovery_service")
        if discovery_service:
            # Get business locations
            offers_with_location = []
            for offer in offers:
                business = await business_repo.get_by_id(offer.business_id)
                if business and business.venue.latitude and business.venue.longitude:
                    offers_with_location.append(
                        (offer, business.venue.latitude, business.venue.longitude)
                    )
            
            # Filter by proximity
            filtered_with_distance = discovery_service.filter_offers_by_location(
                offers_with_location,
                user.last_location_lat,
                user.last_location_lon,
            )
            filtered_offers = [offer for offer, _ in filtered_with_distance]
        else:
            await query.edit_message_text(
                "📍 Location-based filtering requires you to share your location.\n"
                "Use /browse to try other filters."
            )
            return
    
    elif filter_type == "ending":
        # Sort by pickup_end_time (soonest first)
        filtered_offers = sorted(filtered_offers, key=lambda o: o.pickup_end_time)
    
    if not filtered_offers:
        filter_name = {"all": "matching your criteria", "nearby": "nearby", "ending": "ending soon"}
        await query.edit_message_text(
            f"😔 No deals {filter_name.get(filter_type, 'available')} right now.\n"
            "Try a different filter or check back later!"
        )
        return
    
    # Pagination
    total_offers = len(filtered_offers)
    total_pages = ceil(total_offers / OFFERS_PER_PAGE)
    start_idx = page * OFFERS_PER_PAGE
    end_idx = min(start_idx + OFFERS_PER_PAGE, total_offers)
    page_offers = filtered_offers[start_idx:end_idx]
    
    # Build message with offer cards
    text = f"🛍️ **Available Deals** (Page {page + 1}/{total_pages})\n\n"
    
    keyboard = []
    
    for offer in page_offers:
        business = await business_repo.get_by_id(offer.business_id)
        
        if not business:
            continue
        
        # Format pickup time
        now = datetime.utcnow()
        time_until = offer.pickup_end_time - now
        hours_left = int(time_until.total_seconds() / 3600)
        
        card = (
            f"🏪 **{business.business_name}**\n"
            f"📦 {offer.title}\n"
            f"💰 ${offer.price_per_unit} per unit\n"
            f"📍 {business.venue.city}\n"
            f"⏰ Pickup: {offer.pickup_start_time.strftime('%b %d, %H:%M')} - {offer.pickup_end_time.strftime('%H:%M')}\n"
            f"📊 {offer.quantity_remaining}/{offer.quantity_total} left"
        )
        
        if hours_left <= 3:
            card += f" ⚡ Ends in {hours_left}h"
        
        text += card + "\n\n"
        
        # Add button for this offer
        keyboard.append([
            InlineKeyboardButton(
                f"View: {offer.title[:30]}...",
                callback_data=f"offer_detail:{offer.id}",
            )
        ])
    
    # Add pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"browse:{filter_type}:{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("➡️ Next", callback_data=f"browse:{filter_type}:{page + 1}")
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_offer_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed view of a specific offer."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: offer_detail:{offer_id}
    _, offer_id_str = query.data.split(":")
    
    from uuid import UUID
    offer_id = UUID(offer_id_str)
    
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    
    offer = await offer_repo.get_by_id(offer_id)
    
    if not offer or not offer.available_for_reservation:
        await query.edit_message_text("❌ This offer is no longer available.")
        return
    
    business = await business_repo.get_by_id(offer.business_id)
    
    if not business:
        await query.edit_message_text("❌ Business information not found.")
        return
    
    # Build detailed message
    text = (
        f"🏪 **{business.business_name}**\n\n"
        f"📦 **{offer.title}**\n"
        f"{offer.description}\n\n"
        f"💰 **Price:** ${offer.price_per_unit} per unit\n"
        f"📊 **Available:** {offer.quantity_remaining}/{offer.quantity_total} units\n"
        f"📍 **Location:** {business.venue.street_address}, {business.venue.city} {business.venue.postal_code}\n"
        f"📞 **Contact:** {business.contact_phone or 'N/A'}\n"
        f"🕐 **Pickup Window:**\n"
        f"   {offer.pickup_start_time.strftime('%B %d, %Y at %H:%M')} -\n"
        f"   {offer.pickup_end_time.strftime('%H:%M')}\n\n"
        f"💳 **Payment:** On-site (cash or card)\n"
    )
    
    # Quantity selector buttons
    keyboard = []
    
    # Add quick quantity buttons (1, 2, 3, 5, max)
    quantities = [1, 2, 3, 5]
    if offer.quantity_remaining not in quantities and offer.quantity_remaining <= 10:
        quantities.append(offer.quantity_remaining)
    
    quantity_buttons = []
    for qty in quantities:
        if qty <= offer.quantity_remaining:
            quantity_buttons.append(
                InlineKeyboardButton(
                    f"{qty} unit{'s' if qty > 1 else ''}",
                    callback_data=f"reserve:{offer_id}:{qty}",
                )
            )
    
    # Split into rows of 3
    for i in range(0, len(quantity_buttons), 3):
        keyboard.append(quantity_buttons[i:i+3])
    
    keyboard.append([
        InlineKeyboardButton("« Back to Browse", callback_data="browse:all:0")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


def get_browse_handlers() -> list:
    """Return list of browse-related handlers."""
    return [
        CommandHandler("browse", browse_command),
        CallbackQueryHandler(handle_browse_callback, pattern=r"^browse:"),
        CallbackQueryHandler(handle_offer_detail, pattern=r"^offer_detail:"),
    ]
