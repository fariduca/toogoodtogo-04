"""Admin approval handlers for business verification."""

from uuid import UUID

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.business import VerificationStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def list_pending_businesses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all pending business registrations (admin only)."""
    telegram_user = update.effective_user
    permission_checker: PermissionChecker = context.bot_data["permission_checker"]
    
    # Check admin permission
    if not permission_checker.is_admin(telegram_user.id):
        await update.message.reply_text("❌ This command is only available to admins.")
        return
    
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    
    # Get pending businesses
    pending = await business_repo.get_by_verification_status(VerificationStatus.PENDING)
    
    if not pending:
        await update.message.reply_text("No pending business registrations.")
        return
    
    # Build list with approval buttons
    text = "📋 Pending Business Registrations:\n\n"
    
    for business in pending:
        text += (
            f"🏪 {business.business_name}\n"
            f"📍 {business.venue.street_address}, {business.venue.city} {business.venue.postal_code}\n"
            f"📞 {business.contact_phone or 'N/A'}\n"
            f"ID: {business.id}\n\n"
        )
    
    # Add inline keyboard for approval actions
    keyboard = []
    for business in pending:
        keyboard.append([
            InlineKeyboardButton(
                f"✅ Approve: {business.business_name[:20]}...",
                callback_data=f"approve_business:{business.id}",
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"❌ Reject: {business.business_name[:20]}...",
                callback_data=f"reject_business:{business.id}",
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_approve_business(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle business approval callback."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    permission_checker: PermissionChecker = context.bot_data["permission_checker"]
    
    # Check admin permission
    if not permission_checker.is_admin(telegram_user.id):
        await query.edit_message_text("❌ Unauthorized action.")
        return
    
    # Extract business ID from callback data
    _, business_id_str = query.data.split(":")
    business_id = UUID(business_id_str)
    
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Approve business
    business = await business_repo.approve_business(
        business_id,
        approved_by=telegram_user.id,
    )
    
    if not business:
        await query.edit_message_text("❌ Business not found.")
        return
    
    logger.info(
        "business_approved",
        business_id=str(business_id),
        business_name=business.business_name,
        approved_by=telegram_user.id,
    )
    
    # Notify business owner
    owner = await user_repo.get_by_id(business.owner_id)
    if owner:
        try:
            notification_text = (
                f"🎉 Great news! Your business '{business.business_name}' has been approved!\n\n"
                "You can now start posting deals:\n"
                "• /newdeal — Create your first deal\n"
                "• /mydeals — Manage your deals\n\n"
                "Welcome to TooGoodToGo! 🚀"
            )
            
            await context.bot.send_message(
                chat_id=owner.telegram_user_id,
                text=notification_text,
            )
        except Exception as e:
            logger.error(
                "failed_to_notify_owner",
                business_id=str(business_id),
                owner_id=owner.id,
                error=str(e),
            )
    
    await query.edit_message_text(
        f"✅ Business '{business.business_name}' has been approved!\n"
        f"Owner has been notified."
    )


async def handle_reject_business(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle business rejection callback."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    permission_checker: PermissionChecker = context.bot_data["permission_checker"]
    
    # Check admin permission
    if not permission_checker.is_admin(telegram_user.id):
        await query.edit_message_text("❌ Unauthorized action.")
        return
    
    # Extract business ID from callback data
    _, business_id_str = query.data.split(":")
    business_id = UUID(business_id_str)
    
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    
    # Get business and update status
    business = await business_repo.get_by_id(business_id)
    if not business:
        await query.edit_message_text("❌ Business not found.")
        return
    
    # Update to REJECTED status
    business.verification_status = VerificationStatus.REJECTED
    updated_business = await business_repo.update(business)
    
    logger.info(
        "business_rejected",
        business_id=str(business_id),
        business_name=business.business_name,
        rejected_by=telegram_user.id,
    )
    
    # Notify business owner
    owner = await user_repo.get_by_id(business.owner_id)
    if owner:
        try:
            notification_text = (
                f"Thank you for your interest in TooGoodToGo.\n\n"
                f"Unfortunately, your business registration for '{business.business_name}' "
                "could not be approved at this time.\n\n"
                "If you believe this is an error, please contact support."
            )
            
            await context.bot.send_message(
                chat_id=owner.telegram_user_id,
                text=notification_text,
            )
        except Exception as e:
            logger.error(
                "failed_to_notify_owner",
                business_id=str(business_id),
                owner_id=owner.id,
                error=str(e),
            )
    
    await query.edit_message_text(
        f"❌ Business '{business.business_name}' has been rejected.\n"
        f"Owner has been notified."
    )


def get_approval_handlers() -> list:
    """Return list of approval-related handlers."""
    return [
        CommandHandler("pending", list_pending_businesses),
        CallbackQueryHandler(handle_approve_business, pattern=r"^approve_business:"),
        CallbackQueryHandler(handle_reject_business, pattern=r"^reject_business:"),
    ]
