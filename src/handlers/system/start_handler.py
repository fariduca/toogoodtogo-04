"""Startup and fallback handlers for casual users.

Provides a friendly /start command and a default text handler so that
users who send plain messages get a helpful response instead of no reply.
"""

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

from src.logging import get_logger

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple welcome/intro message for the /start command."""
    text = (
        "👋 Hello! Welcome to the Telegram Marketplace Bot.\n\n"
        "Try one of these commands to get started:\n"
        "• /offers — Browse available offers\n"
        "• /newoffer — Create a new offer (business owners)\n"
        "• /register — Register your business\n\n"
        "If you need help, just type one of the commands above or contact the team."
    )
    await update.message.reply_text(text)


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
