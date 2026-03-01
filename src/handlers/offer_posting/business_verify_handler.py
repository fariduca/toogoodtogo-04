"""Business verification handler for admins.

Allows admins to approve or reject pending business registrations.
Commands:
- /verify <business_id> - Approve a business
- /reject <business_id> <reason> - Reject a business
- /pending - List pending businesses
"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.business import VerificationStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


async def list_pending_businesses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List all businesses pending verification."""
    user_id = update.effective_user.id
    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    lang = get_lang(user) if user else "en"

    # Check admin permission
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    if not permission_checker or not permission_checker.can_approve_business(user_id):
        await update.message.reply_text(t("approval_no_permission_view", lang))
        return

    try:
        repo: PostgresBusinessRepository = context.bot_data.get("business_repo")
        # TODO: Implement repository method
        # pending = await repo.get_by_verification_status(VerificationStatus.PENDING)

        # Placeholder response
        await update.message.reply_text(
            t("approval_pending_list", lang)
        )

        logger.info("pending_businesses_listed", admin_id=user_id)

    except Exception as e:
        logger.error("list_pending_failed", error=str(e), exc_info=True)
        await update.message.reply_text(t("approval_failed_list", lang))


async def approve_business(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve a pending business."""
    user_id = update.effective_user.id
    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    lang = get_lang(user) if user else "en"

    # Check admin permission
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    if not permission_checker or not permission_checker.can_approve_business(user_id):
        await update.message.reply_text(t("approval_no_permission", lang))
        return

    # Parse business_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            t("approval_verify_usage", lang)
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
            t("approval_approved", lang, business_id=business_id)
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
            t("approval_failed", lang, business_id=business_id)
        )


async def reject_business(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reject a pending business."""
    user_id = update.effective_user.id
    user_repo: PostgresUserRepository = context.bot_data.get("user_repo")
    user = await user_repo.get_by_telegram_id(user_id) if user_repo else None
    lang = get_lang(user) if user else "en"

    # Check admin permission
    permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
    if not permission_checker or not permission_checker.can_approve_business(user_id):
        await update.message.reply_text(t("approval_no_permission_reject", lang))
        return

    # Parse business_id and reason from command args
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            t("approval_reject_usage", lang)
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
            t("approval_rejected", lang, business_id=business_id, reason=reason)
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
            t("approval_reject_failed", lang, business_id=business_id)
        )


def get_verification_handlers() -> list:
    """Return list of verification command handlers."""
    return [
        CommandHandler("pending", list_pending_businesses),
        CommandHandler("verify", approve_business),
        CommandHandler("reject", reject_business),
    ]
