"""Offers listing handler for discovery.

Allows customers to browse available offers with ranking and filtering.
Command: /offers or /browse
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.offer import OfferStatus
from src.services.discovery_ranking import DiscoveryRankingService
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def list_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List active offers for browsing."""
    user_id = update.effective_user.id
    logger.info("offers_listing_requested", user_id=user_id)

    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    lang = get_lang(user)

    try:
        repo: PostgresOfferRepository = context.bot_data.get("offer_repo")
        ranking_service: DiscoveryRankingService = context.bot_data.get("ranking_service")

        # Get active offers
        # TODO: Implement pagination with context.args
        limit = 10
        active_offers = await repo.get_active_offers(limit=limit)

        if not active_offers:
            await update.message.reply_text(
                t("offers_empty", lang)
            )
            return

        # Rank offers
        ranked_offers = await ranking_service.rank_offers(active_offers)

        # Format offers list
        message_lines = [t("offers_header", lang)]

        for idx, offer in enumerate(ranked_offers, 1):
            # Calculate total available quantity
            remaining = offer.remaining_quantity

            # Format time range
            start_str = offer.start_time.strftime("%b %d, %H:%M")
            end_str = offer.end_time.strftime("%b %d, %H:%M")

            # Build offer summary
            message_lines.append(
                f"{idx}. **{offer.title}**\n"  # UGC: not translated (FR-007)
                f"   {t('offers_item_count', lang, remaining=remaining)}\n"
                f"   ⏰ {start_str} - {end_str}\n"
            )

        message_text = "\n".join(message_lines)
        message_text += "\n\n" + t("offers_tap_details", lang)

        # Create inline keyboard with offer buttons
        keyboard = []
        for offer in ranked_offers:
            button_text = f"{offer.title[:30]}..."  # UGC: not translated (FR-007)
            callback_data = f"view_offer:{offer.id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        logger.info(
            "offers_listed",
            user_id=user_id,
            count=len(ranked_offers),
        )

    except Exception as e:
        logger.error("offers_listing_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            t("offers_listing_failed", lang)
        )


async def view_offer_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed view of an offer (callback handler)."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    lang = get_lang(user)

    # Parse offer_id from callback data
    callback_data = query.data
    if not callback_data.startswith("view_offer:"):
        await query.edit_message_text(t("offers_invalid_selection", lang))
        return

    offer_id = callback_data.split(":", 1)[1]

    try:
        from uuid import UUID
        from src.storage.postgres_business_repo import PostgresBusinessRepository
        
        repo: PostgresOfferRepository = context.bot_data.get("offer_repo")
        business_repo: PostgresBusinessRepository = context.bot_data.get("business_repo")
        
        offer = await repo.get_by_id(UUID(offer_id))

        if not offer:
            await query.edit_message_text(t("err_offer_unavailable", lang))
            return
        
        # Get business details
        business = await business_repo.get_by_id(offer.business_id)
        
        # Status indicators
        status_indicator = ""
        if offer.state == OfferStatus.PAUSED:
            status_indicator = t("offers_detail_paused", lang) + "\n\n"
        elif offer.state == OfferStatus.SOLD_OUT:
            status_indicator = t("offers_detail_sold_out", lang) + "\n\n"
        elif offer.state == OfferStatus.EXPIRED:
            status_indicator = t("offers_detail_expired", lang) + "\n\n"
        elif offer.state == OfferStatus.EXPIRED_EARLY:
            status_indicator = t("offers_detail_ended", lang) + "\n\n"
        elif offer.is_expired:
            status_indicator = t("offers_detail_expired", lang) + "\n\n"

        # Format offer details
        message_text = (
            f"{status_indicator}"
            f"📦 **{offer.title}**\n\n"  # UGC: not translated (FR-007)
            f"{offer.description}\n\n"  # UGC: not translated (FR-007)
            f"💰 €{offer.price_per_unit} per unit\n"
            f"📦 {offer.quantity_remaining}/{offer.quantity_total} units available\n"
            f"⏰ Pickup: {offer.pickup_start_time.strftime('%H:%M')} - "
            f"{offer.pickup_end_time.strftime('%H:%M')}\n"
        )
        
        if business:
            message_text += (
                f"\n🏪 **{business.business_name}**\n"  # UGC: not translated (FR-007)
                f"📍 {business.street_address}, {business.city}\n"
            )

        # Create buttons based on offer state
        keyboard = []
        
        # Only show Reserve button if offer is available
        if offer.available_for_reservation:
            keyboard.append([
                InlineKeyboardButton(t("btn_reserve", lang), callback_data=f"reserve:{offer_id}")
            ])
        
        keyboard.append([
            InlineKeyboardButton(t("btn_back_list", lang), callback_data="back_to_offers")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

        logger.info("offer_details_viewed", user_id=user_id, offer_id=offer_id)

    except Exception as e:
        logger.error("offer_details_failed", offer_id=offer_id, error=str(e), exc_info=True)
        await query.edit_message_text(t("offers_detail_failed", lang))


def get_discovery_handlers() -> list:
    """Return list of discovery handlers."""
    return [
        CommandHandler("offers", list_offers),
        CommandHandler("browse", list_offers),
    ]
