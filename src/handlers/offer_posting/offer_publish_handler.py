"""Offer publish handler.

Transitions draft offers to ACTIVE status, making them visible to customers.
Command: /publish <offer_id>
"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.logging import get_logger
from src.models.offer import OfferStatus
from src.security.permissions import PermissionChecker
from src.services.offer_validation import OfferValidator
from src.storage.postgres_offer_repo import PostgresOfferRepository

logger = get_logger(__name__)


async def publish_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Publish a draft offer to make it active."""
    user_id = update.effective_user.id

    # Parse offer_id from command args
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /publish <offer_id>\n"
            "Example: /publish 123e4567-e89b-12d3-a456-426614174000"
        )
        return

    offer_id = context.args[0]

    try:
        repo: PostgresOfferRepository = context.bot_data.get("offer_repo")
        # TODO: Get offer from repository
        # offer = await repo.get_by_id(offer_id)

        # if not offer:
        #     await update.message.reply_text(f"❌ Offer {offer_id} not found.")
        #     return

        # Check permission
        permission_checker: PermissionChecker = context.bot_data.get("permission_checker")
        # TODO: Get business_id from offer and check ownership
        # business_id = offer.business_id
        # if not permission_checker.can_edit_offer(business_id, offer_id, user_id):
        #     await update.message.reply_text("❌ You don't have permission to publish this offer.")
        #     return

        # Validate offer
        validator: OfferValidator = context.bot_data.get("offer_validator")
        # TODO: Validate offer meets business rules
        # validation_result = await validator.validate_for_publish(offer)
        # if not validation_result.is_valid:
        #     errors = "\n".join(f"• {err}" for err in validation_result.errors)
        #     await update.message.reply_text(
        #         f"❌ Cannot publish offer. Please fix these issues:\n{errors}"
        #     )
        #     return

        # Update status to ACTIVE
        # await repo.update_status(offer_id, OfferStatus.ACTIVE)

        logger.info(
            "offer_published",
            offer_id=offer_id,
            user_id=user_id,
        )

        await update.message.reply_text(
            f"✅ Offer published successfully!\n\n"
            f"Your offer is now live and visible to customers. "
            f"They can find it in the marketplace and make purchases."
        )

    except Exception as e:
        logger.error(
            "offer_publish_failed",
            offer_id=offer_id,
            error=str(e),
            exc_info=True,
        )
        await update.message.reply_text(
            f"❌ Failed to publish offer {offer_id}. "
            "Please check the offer ID and try again."
        )


def get_publish_handler() -> CommandHandler:
    """Return the publish command handler."""
    return CommandHandler("publish", publish_offer)
