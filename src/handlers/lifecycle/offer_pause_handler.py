"""Offer pause handler.

Allows business owners to temporarily pause active offers,
preventing new purchases while keeping the offer visible.
Command: /pause <offer_id>
"""

from uuid import UUID
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.i18n import t
from src.logging import get_logger
from src.models.offer import OfferStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.database import get_database

logger = get_logger(__name__)


async def pause_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pause an active offer to prevent new purchases."""
    lang = context.user_data.get("lang", "en")
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            t("offer_pause_usage", lang)
        )
        return

    offer_id_str = context.args[0]

    try:
        # Validate UUID format
        try:
            offer_id = UUID(offer_id_str)
        except ValueError:
            await update.message.reply_text(
                f"❌ Invalid offer ID format: {offer_id_str}\n"
                "Please provide a valid UUID."
            )
            return

        # Get database connection
        db = get_database()
        await db.connect()

        try:
            async with db.session() as session:
                repo = PostgresOfferRepository(session)

                # Get offer
                offer = await repo.get_by_id(offer_id)

                if not offer:
                    await update.message.reply_text(
                        t("offer_lifecycle_edit_not_found", lang, offer_id=offer_id_str)
                    )
                    return

                # Check permission (business owns offer)
                permission_checker: PermissionChecker = context.bot_data.get(
                    "permission_checker"
                )
                if permission_checker and not await permission_checker.can_edit_offer(
                    offer.business_id, offer_id, user_id
                ):
                    await update.message.reply_text(
                        t("offer_pause_no_permission", lang)
                    )
                    return

                # Check current status
                if offer.status == OfferStatus.PAUSED:
                    await update.message.reply_text(
                        t("offer_pause_already", lang, title=offer.title)
                    )
                    return

                if offer.status != OfferStatus.ACTIVE:
                    await update.message.reply_text(
                        t("offer_pause_cannot_status", lang, title=offer.title, status=offer.status.value)
                    )
                    return

                # Update status to PAUSED
                await repo.update_status(offer_id, OfferStatus.PAUSED)
                await session.commit()

                logger.info(
                    "offer_paused",
                    offer_id=str(offer_id),
                    user_id=user_id,
                    offer_title=offer.title,
                )

                await update.message.reply_text(
                    t("offer_pause_success", lang, title=offer.title, offer_id=offer_id_str)
                )

        finally:
            await db.disconnect()

    except Exception as e:
        logger.error(
            "offer_pause_failed",
            offer_id=offer_id_str,
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            t("offer_pause_failed", lang, error=str(e))
        )


async def resume_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume a paused offer to allow purchases again."""
    lang = context.user_data.get("lang", "en")
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            t("offer_resume_usage", lang)
        )
        return

    offer_id_str = context.args[0]

    try:
        # Validate UUID format
        try:
            offer_id = UUID(offer_id_str)
        except ValueError:
            await update.message.reply_text(
                t("offer_resume_invalid_id", lang, offer_id=offer_id_str)
            )
            return

        # Get database connection
        db = get_database()
        await db.connect()

        try:
            async with db.session() as session:
                repo = PostgresOfferRepository(session)

                # Get offer
                offer = await repo.get_by_id(offer_id)

                if not offer:
                    await update.message.reply_text(
                        t("offer_lifecycle_edit_not_found", lang, offer_id=offer_id_str)
                    )
                    return

                # Check permission
                permission_checker: PermissionChecker = context.bot_data.get(
                    "permission_checker"
                )
                if permission_checker and not await permission_checker.can_edit_offer(
                    offer.business_id, offer_id, user_id
                ):
                    await update.message.reply_text(
                        t("offer_resume_no_permission", lang)
                    )
                    return

                # Check current status
                if offer.status == OfferStatus.ACTIVE:
                    await update.message.reply_text(
                        t("offer_resume_already_active", lang, title=offer.title)
                    )
                    return

                if offer.status != OfferStatus.PAUSED:
                    await update.message.reply_text(
                        t("offer_resume_cannot_status", lang, title=offer.title, status=offer.status.value)
                    )
                    return

                # Check if offer has expired
                if offer.is_expired:
                    await update.message.reply_text(
                        t("offer_resume_expired_msg", lang, title=offer.title)
                    )
                    return

                # Update status to ACTIVE
                await repo.update_status(offer_id, OfferStatus.ACTIVE)
                await session.commit()

                logger.info(
                    "offer_resumed",
                    offer_id=str(offer_id),
                    user_id=user_id,
                    offer_title=offer.title,
                )

                await update.message.reply_text(
                    t("offer_resume_success", lang, title=offer.title)
                )

        finally:
            await db.disconnect()

    except Exception as e:
        logger.error(
            "offer_resume_failed",
            offer_id=offer_id_str,
            user_id=user_id,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            t("offer_resume_failed", lang, error=str(e))
        )


def get_pause_handler() -> CommandHandler:
    """Return the pause command handler."""
    return CommandHandler("pause", pause_offer)


def get_resume_handler() -> CommandHandler:
    """Return the resume command handler."""
    return CommandHandler("resume", resume_offer)
