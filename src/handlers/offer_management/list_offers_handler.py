"""List business's offers with management buttons - /myoffers command."""

from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.offer import OfferStatus
from src.models.user import UserRole
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def myoffers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myoffers command - show business's offers with management options."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    offer_repo: PostgresOfferRepository = context.bot_data["offer_repo"]
    
    telegram_user = update.effective_user
    
    # Get user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    lang = get_lang(user) if user else "en"
    
    if not user:
        await update.message.reply_text(
            t("err_register_first", lang)
        )
        return
    
    if user.role != UserRole.BUSINESS:
        await update.message.reply_text(
            t("offer_mgmt_business_only", lang)
        )
        return
    
    # Get user's business
    businesses = await business_repo.get_by_owner_id(user.id)
    
    if not businesses:
        await update.message.reply_text(
            t("offer_mgmt_no_business", lang)
        )
        return
    
    business = businesses[0]
    
    # Get offers for this business
    offers = await offer_repo.get_by_business_id(business.id)
    
    if not offers:
        await update.message.reply_text(
            t("offer_mgmt_empty", lang, business_name=business.business_name)
        )
        return
    
    # Sort offers: active first, then by creation date
    offers.sort(
        key=lambda o: (
            0 if o.state == OfferStatus.ACTIVE else
            1 if o.state == OfferStatus.PAUSED else
            2 if o.state == OfferStatus.SOLD_OUT else
            3,
            o.created_at
        ),
        reverse=True
    )
    
    message_lines = [t("offer_mgmt_header", lang, count=len(offers))]
    
    for offer in offers:
        # Status indicator
        status_emoji = {
            OfferStatus.ACTIVE: "✅",
            OfferStatus.PAUSED: "⏸️",
            OfferStatus.SOLD_OUT: "🔴",
            OfferStatus.EXPIRED: "⏰",
            OfferStatus.EXPIRED_EARLY: "🛑",
        }
        emoji = status_emoji.get(offer.state, "❓")
        
        # Time info
        now = datetime.utcnow()
        if offer.pickup_end_time > now:
            time_info = t("offer_mgmt_time_until", lang, time=offer.pickup_end_time.strftime('%H:%M'))
        else:
            time_info = t("offer_mgmt_expired", lang)
        
        # Build offer card
        message_lines.append(
            f"{emoji} **{offer.title}**\n"
            f"  {offer.quantity_remaining}/{offer.quantity_total} left · "
            f"€{offer.price_per_unit} · {time_info}\n"
            f"  Status: {offer.state.value}\n"
        )
        
        # Add management buttons
        keyboard = []
        
        if offer.state == OfferStatus.ACTIVE:
            keyboard.append([
                InlineKeyboardButton(t("btn_pause_offer", lang), callback_data=f"pause_offer:{offer.id}"),
                InlineKeyboardButton(t("btn_edit_offer", lang), callback_data=f"edit_offer:{offer.id}"),
            ])
            keyboard.append([
                InlineKeyboardButton(t("btn_end_offer", lang), callback_data=f"end_offer:{offer.id}"),
            ])
        elif offer.state == OfferStatus.PAUSED:
            keyboard.append([
                InlineKeyboardButton(t("btn_resume_offer", lang), callback_data=f"resume_offer:{offer.id}"),
                InlineKeyboardButton(t("btn_edit_offer", lang), callback_data=f"edit_offer:{offer.id}"),
            ])
            keyboard.append([
                InlineKeyboardButton(t("btn_end_offer", lang), callback_data=f"end_offer:{offer.id}"),
            ])
        
        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                message_lines[-1],
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            message_lines.pop()  # Remove last line since we sent it separately
    
    # Send remaining text if any
    if len(message_lines) > 1:
        await update.message.reply_text(
            "\n".join(message_lines),
            parse_mode="Markdown"
        )
    
    logger.info(
        "myoffers_displayed",
        user_id=user.id,
        business_id=str(business.id),
        offer_count=len(offers)
    )


def get_myoffers_handler() -> CommandHandler:
    """Create the /myoffers command handler."""
    return CommandHandler("myoffers", myoffers_command)
