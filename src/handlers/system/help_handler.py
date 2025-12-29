"""Help command handler with role-specific feature explanations."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.user import UserRole
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show role-specific help information."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Get user to determine role
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user:
        # Show general help for unregistered users
        text = (
            "🆘 <b>Help &amp; Commands</b>\n\n"
            "Welcome to TooGoodToGo Bot! This bot connects businesses with excess produce "
            "to customers looking for great deals.\n\n"
            "<b>Getting Started:</b>\n"
            "• /start — Register as a business or customer\n\n"
            "<b>For more information, use /start to begin!</b>"
        )
        await update.message.reply_text(text, parse_mode="HTML")
        return
    
    if user.role == UserRole.BUSINESS:
        # Business help
        text = (
            "🆘 <b>Help for Businesses</b>\n\n"
            "<b>Post &amp; Manage Deals:</b>\n"
            "• /newdeal — Create a new offer for excess produce\n"
            "• /myoffers — View and manage your offers (pause, resume, edit, end)\n\n"
            "<b>How it Works:</b>\n"
            "1. Create an offer with details (title, description, price, quantity, pickup time)\n"
            "2. Customers browse and reserve items\n"
            "3. Customers pay on-site when picking up\n"
            "4. You can pause, edit, or end offers anytime\n\n"
            "<b>Tips:</b>\n"
            "• Set pickup times that work for your business hours\n"
            "• Add clear descriptions and photos for better visibility\n"
            "• Offers expire automatically at the pickup end time\n\n"
            "<b>Other Commands:</b>\n"
            "• /settings — Manage your preferences\n"
            "• /help — Show this help message\n\n"
            "Need support? Contact @toogoodtogo_support"
        )
    else:
        # Customer help
        text = (
            "🆘 <b>Help for Customers</b>\n\n"
            "<b>Discover &amp; Reserve:</b>\n"
            "• /browse — Discover available deals nearby\n"
            "• /myreservations — View your active reservations\n\n"
            "<b>How it Works:</b>\n"
            "1. Browse offers using /browse\n"
            "2. Select an offer to see details\n"
            "3. Reserve your items (payment is on-site)\n"
            "4. Pick up during the specified time window\n"
            "5. Pay in cash/card at the business location\n\n"
            "<b>Important:</b>\n"
            "• Reservations can be cancelled before pickup time ends\n"
            "• Each reservation has a unique Order ID for pickup\n"
            "• Bring your Order ID when picking up\n\n"
            "<b>Other Commands:</b>\n"
            "• /settings — Manage your preferences\n"
            "• /help — Show this help message\n\n"
            "Need support? Contact @toogoodtogo_support"
        )
    
    await update.message.reply_text(text, parse_mode="HTML")
    
    logger.info(
        "help_displayed",
        user_id=user.id,
        role=user.role.value
    )


def get_help_handler() -> CommandHandler:
    """Create the /help command handler."""
    return CommandHandler("help", help_command)
