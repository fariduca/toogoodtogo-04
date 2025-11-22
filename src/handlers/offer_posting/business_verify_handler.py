"""Business verification handler for admins.

Allows admins to approve or reject pending business registrations.
Commands:
- /verify <business_id> - Approve a business
- /reject <business_id> <reason> - Reject a business
- /pending - List pending businesses
"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.business import VerificationStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_business_repo import PostgresBusinessRepository

logger = get_logger(__name__)


async def list_pending_businesses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List all businesses pending verification."""
    user_id = update.effective_user.id

    # Check admin permission
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    if not permission_checker or not permission_checker.can_approve_business(user_id):
        await update.message.reply_text("❌ You don't have permission to view pending businesses.")
        return

    try:
        repo: PostgresBusinessRepository = context.bot_data.get("business_repo")
        # TODO: Implement repository method
        # pending = await repo.get_by_verification_status(VerificationStatus.PENDING)

        # Placeholder response
        await update.message.reply_text(
            "📋 Pending Businesses:\n\n"
            "Use /verify <business_id> to approve\n"
            "Use /reject <business_id> <reason> to reject\n\n"
            "Database query implementation pending."
        )

        logger.info("pending_businesses_listed", admin_id=user_id)

    except Exception as e:
        logger.error("list_pending_failed", error=str(e), exc_info=True)
        await update.message.reply_text("❌ Failed to retrieve pending businesses.")


async def approve_business(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve a pending business."""
    user_id = update.effective_user.id

    # Check admin permission
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    if not permission_checker or not permission_checker.can_approve_business(user_id):
        await update.message.reply_text("❌ You don't have permission to approve businesses.")
        return

    # Parse business_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /verify <business_id>\n"
            "Example: /verify 123e4567-e89b-12d3-a456-426614174000"
        )
        return

    business_id = context.args[0]

    try:
        repo: PostgresBusinessRepository = context.bot_data.get("business_repo")
        # TODO: Implement repository method
        # await repo.approve_business(business_id)

        logger.info(
            "business_approved",
            business_id=business_id,
            admin_id=user_id,
        )

        await update.message.reply_text(
            f"✅ Business {business_id} has been approved!\n\n"
            "The business owner will be notified and can now create offers."
        )

        # TODO: Send notification to business owner via Telegram

    except Exception as e:
        logger.error(
            "business_approval_failed",
            business_id=business_id,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ Failed to approve business {business_id}. "
            "Please check the business ID and try again."
        )


async def reject_business(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reject a pending business."""
    user_id = update.effective_user.id

    # Check admin permission
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    if not permission_checker or not permission_checker.can_approve_business(user_id):
        await update.message.reply_text("❌ You don't have permission to reject businesses.")
        return

    # Parse business_id and reason from command args
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /reject <business_id> <reason>\n"
            "Example: /reject 123e4567-e89b-12d3-a456-426614174000 Incomplete information"
        )
        return

    business_id = context.args[0]
    reason = " ".join(context.args[1:])

    try:
        repo: PostgresBusinessRepository = context.bot_data.get("business_repo")
        # TODO: Implement repository method with rejection reason
        # await repo.update_status(business_id, VerificationStatus.REJECTED, reason)

        logger.info(
            "business_rejected",
            business_id=business_id,
            admin_id=user_id,
            reason=reason,
        )

        await update.message.reply_text(
            f"❌ Business {business_id} has been rejected.\n\n"
            f"Reason: {reason}\n\n"
            "The business owner will be notified."
        )

        # TODO: Send rejection notification to business owner via Telegram

    except Exception as e:
        logger.error(
            "business_rejection_failed",
            business_id=business_id,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ Failed to reject business {business_id}. "
            "Please check the business ID and try again."
        )


def get_verification_handlers() -> list:
    """Return list of verification command handlers."""
    return [
        CommandHandler("pending", list_pending_businesses),
        CommandHandler("verify", approve_business),
        CommandHandler("reject", reject_business),
    ]
