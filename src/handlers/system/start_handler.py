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
    """Welcome message with role selection for new users."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Check if user already exists
    existing_user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if existing_user:
        # Returning user - show personalized welcome
        if existing_user.role == UserRole.BUSINESS:
            text = (
                f"👋 Welcome back, {telegram_user.first_name}!\n\n"
                "You're registered as a business. Here's what you can do:\n"
                "• /newdeal — Post a new excess-produce deal\n"
                "• /mydeals — View and manage your deals\n"
                "• /mybusiness — View business details"
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
