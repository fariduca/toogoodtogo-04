"""Offer pause handler.

Allows business owners to temporarily pause active offers,
preventing new purchases while keeping the offer visible.
Command: /pause <offer_id>
"""

from uuid import UUID
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.security.permissions import PermissionChecker
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.database import get_database

logger = get_logger(__name__)


async def pause_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pause an active offer to prevent new purchases."""
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /pause <offer_id>\n"
            "Example: /pause 123e4567-e89b-12d3-a456-426614174000\n\n"
            "This will temporarily pause your offer, preventing new purchases "
            "while keeping it visible to customers."
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
                        f"❌ Offer not found: {offer_id_str}"
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
                        "❌ You don't have permission to pause this offer."
                    )
                    return

                # Check current status
                if offer.status == OfferStatus.PAUSED:
                    await update.message.reply_text(
                        f"ℹ️ Offer '{offer.title}' is already paused."
                    )
                    return

                if offer.status != OfferStatus.ACTIVE:
                    await update.message.reply_text(
                        f"❌ Cannot pause offer '{offer.title}'.\n"
                        f"Current status: {offer.status.value}\n"
                        f"Only active offers can be paused."
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
                    f"⏸️ Offer paused successfully!\n\n"
                    f"**{offer.title}**\n\n"
                    f"Your offer is now paused. Customers can still view it, "
                    f"but they cannot make new purchases.\n\n"
                    f"To resume, use: /resume {offer_id_str}"
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
            f"❌ Failed to pause offer.\n"
            f"Error: {str(e)}\n\n"
            "Please try again later."
        )


async def resume_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume a paused offer to allow purchases again."""
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /resume <offer_id>\n"
            "Example: /resume 123e4567-e89b-12d3-a456-426614174000\n\n"
            "This will resume your paused offer, allowing customers to purchase again."
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
                        f"❌ Offer not found: {offer_id_str}"
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
                        "❌ You don't have permission to resume this offer."
                    )
                    return

                # Check current status
                if offer.status == OfferStatus.ACTIVE:
                    await update.message.reply_text(
                        f"ℹ️ Offer '{offer.title}' is already active."
                    )
                    return

                if offer.status != OfferStatus.PAUSED:
                    await update.message.reply_text(
                        f"❌ Cannot resume offer '{offer.title}'.\n"
                        f"Current status: {offer.status.value}\n"
                        f"Only paused offers can be resumed."
                    )
                    return

                # Check if offer has expired
                if offer.is_expired:
                    await update.message.reply_text(
                        f"❌ Cannot resume offer '{offer.title}'.\n"
                        f"This offer has expired and can no longer be resumed."
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
                    f"▶️ Offer resumed successfully!\n\n"
                    f"**{offer.title}**\n\n"
                    f"Your offer is now active again. Customers can browse and purchase."
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
            f"❌ Failed to resume offer.\n"
            f"Error: {str(e)}\n\n"
            "Please try again later."
        )


def get_pause_handler() -> CommandHandler:
    """Return the pause command handler."""
    return CommandHandler("pause", pause_offer)


def get_resume_handler() -> CommandHandler:
    """Return the resume command handler."""
    return CommandHandler("resume", resume_offer)
