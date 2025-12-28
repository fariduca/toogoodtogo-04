"""Startup and fallback handlers for casual users.

Provides a friendly /start command and a default text handler so that
users who send plain messages get a helpful response instead of no reply.
"""

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

from src.logging import get_logger
from src.models.user import UserInput, UserRole
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message with role selection for new users or deep link handling."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Check for deep link parameters (format: /start <parameter>)
    if context.args and len(context.args) > 0:
        param = context.args[0]
        
        # Handle deep link: offer_<offer_id>
        if param.startswith("offer_"):
            from uuid import UUID
            from src.handlers.discovery.list_offers_handler import view_offer_details
            
            offer_id = param.replace("offer_", "")
            try:
                # Create a mock callback query to reuse view_offer_details
                # Note: This is a simplified approach; ideally refactor view_offer_details
                # to accept both callback queries and direct calls
                await update.message.reply_text(
                    f"📦 Loading offer details...\n\n"
                    f"Use /browse to see all available offers, or tap the button below:",
                )
                
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [[
                    InlineKeyboardButton("View Offer", callback_data=f"view_offer:{offer_id}")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "👆 Tap to view offer details",
                    reply_markup=reply_markup
                )
                
                logger.info(
                    "deep_link_offer_accessed",
                    user_id=telegram_user.id,
                    offer_id=offer_id
                )
                return
            
            except Exception as e:
                logger.error("deep_link_offer_failed", error=str(e), exc_info=True)
                await update.message.reply_text(
                    "❌ Invalid offer link. Use /browse to see available offers."
                )
                return
        
        # Handle deep link: business_invite_<token> (future feature)
        elif param.startswith("business_invite_"):
            token = param.replace("business_invite_", "")
            # TODO: Implement business invitation flow
            await update.message.reply_text(
                "🏪 Business invitation feature coming soon!\n\n"
                "Use /start to register manually."
            )
            logger.info(
                "deep_link_business_invite_accessed",
                user_id=telegram_user.id,
                token=token
            )
            return
    
    # Check if user already exists
    existing_user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if existing_user:
        # Returning user - show personalized welcome
        if existing_user.role == UserRole.BUSINESS:
            text = (
                f"👋 Welcome back, {telegram_user.first_name}!\n\n"
                "You're registered as a business. Here's what you can do:\n"
                "• /newdeal — Post a new excess-produce deal\n"
                "• /myoffers — View and manage your deals\n"
                "• /myreservations — View your reservations"
            )
        else:
            text = (
                f"👋 Welcome back, {telegram_user.first_name}!\n\n"
                "Here's what you can do:\n"
                "• /browse — Discover nearby deals\n"
                "• /myreservations — View your reservations"
            )
        await update.message.reply_text(text)
        return
    
    # New user - prompt for role selection
    keyboard = [
        ["🏪 I'm a Business Owner"],
        ["🛍️ I'm a Customer"],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    
    text = (
        f"👋 Welcome to TooGoodToGo, {telegram_user.first_name}!\n\n"
        "This bot helps businesses sell excess produce at discounted prices "
        "and helps customers discover great deals nearby.\n\n"
        "To get started, please select your role:"
    )
    
    await update.message.reply_text(text, reply_markup=reply_markup)
    
    # Store state for next message handler
    context.user_data["awaiting_role_selection"] = True


async def default_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback for plain text messages — give a short helpful nudge."""
    logger.info("received_plain_message", user_id=update.effective_user.id)
    await update.message.reply_text(
        "I didn't understand that. Try /offers or /newoffer to begin — or send /start for help."
    )


def get_start_handler() -> CommandHandler:
    return CommandHandler("start", start_command)


def get_default_message_handler() -> MessageHandler:
    # Catch plain text messages that are not commands
    return MessageHandler(filters.TEXT & ~filters.COMMAND, default_message)
