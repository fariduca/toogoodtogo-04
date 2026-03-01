"""Help command handler with role-specific feature explanations."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.user import UserRole
from src.storage.postgres_user_repo import PostgresUserRepository
from src.i18n import t, get_lang

logger = get_logger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show role-specific help information."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Get user to determine role
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        # Show general help for unregistered users
        lang = context.user_data.get("lang", "en")
        text = t("help_unregistered", lang)
        await update.message.reply_text(text, parse_mode="HTML")
        return
    
    lang = get_lang(user)
    if user.role == UserRole.BUSINESS:
        text = t("help_business", lang)
    else:
        text = t("help_customer", lang)
    
    await update.message.reply_text(text, parse_mode="HTML")
    
    logger.info(
        "help_displayed",
        user_id=user.id,
        role=user.role.value
    )


def get_help_handler() -> CommandHandler:
    """Create the /help command handler."""
    return CommandHandler("help", help_command)
