"""Settings command handler for language and notification preferences."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.logging import get_logger
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user settings with options to modify."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Get user
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        await update.message.reply_text(
            "❌ Please use /start to register first."
        )
        return
    
    # Build settings message
    notification_status = "✅ Enabled" if user.notification_enabled else "❌ Disabled"
    language = user.language_code.upper()
    
    text = (
        "⚙️ **Settings**\n\n"
        f"**Language:** {language}\n"
        f"**Notifications:** {notification_status}\n"
    )
    
    # Build settings keyboard
    keyboard = [
        [InlineKeyboardButton(
            "🔔 Toggle Notifications",
            callback_data=f"toggle_notifications:{user.id}"
        )],
        # Future: Language selection
        # [InlineKeyboardButton("🌐 Change Language", callback_data="change_language")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    logger.info(
        "settings_viewed",
        user_id=user.id
    )


async def handle_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle notification toggle callback."""
    query = update.callback_query
    await query.answer()
    
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Extract user_id from callback_data
    user_id_str = query.data.split(":")[1]
    user_id = int(user_id_str)
    
    # Get user
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        await query.edit_message_text("❌ User not found.")
        return
    
    # Toggle notification setting
    user.notification_enabled = not user.notification_enabled
    updated_user = await user_repo.update(user)
    
    notification_status = "✅ Enabled" if updated_user.notification_enabled else "❌ Disabled"
    
    # Update message
    text = (
        "⚙️ **Settings**\n\n"
        f"**Language:** {updated_user.language_code.upper()}\n"
        f"**Notifications:** {notification_status}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton(
            "🔔 Toggle Notifications",
            callback_data=f"toggle_notifications:{user.id}"
        )],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    
    logger.info(
        "notifications_toggled",
        user_id=user.id,
        enabled=updated_user.notification_enabled
    )


def get_settings_handler() -> CommandHandler:
    """Create the /settings command handler."""
    return CommandHandler("settings", settings_command)


def get_settings_callback_handler() -> CallbackQueryHandler:
    """Create settings callback handlers."""
    return CallbackQueryHandler(handle_toggle_notifications, pattern=r"^toggle_notifications:")
