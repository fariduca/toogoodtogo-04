"""Business registration conversation handler.

Handles multi-step registration flow:
1. /register command initiates
2. Collect business name
3. Collect venue address (street, city)
4. Collect venue coordinates (lat, lon)
5. Upload business photo
6. Submit for verification
"""

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.i18n import t, get_lang
from src.logging import get_logger
from src.models.business import BusinessInput, Venue, VerificationStatus
from src.storage.image_store import ImageStoreProtocol
from src.storage.postgres_business_repo import PostgresBusinessRepository

logger = get_logger(__name__)

# Conversation states
NAME, ADDRESS, COORDINATES, PHOTO = range(4)


async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start business registration conversation."""
    user = update.effective_user
    lang = context.user_data.get("lang", "en")
    logger.info("registration_started", user_id=user.id, username=user.username)

    await update.message.reply_text(
        t("reg_welcome", lang)
    )
    return NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate business name."""
    lang = context.user_data.get("lang", "en")
    business_name = update.message.text.strip()

    if len(business_name) < 3 or len(business_name) > 100:
        await update.message.reply_text(
            t("reg_name_validation", lang)
        )
        return NAME

    context.user_data["business_name"] = business_name
    logger.info("business_name_received", name=business_name)

    await update.message.reply_text(
        t("reg_name_received", lang, name=business_name)
    )
    return ADDRESS


async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive venue address."""
    lang = context.user_data.get("lang", "en")
    address = update.message.text.strip()

    if len(address) < 5:
        await update.message.reply_text(
            t("reg_address_validation", lang)
        )
        return ADDRESS

    context.user_data["address"] = address
    logger.info("address_received", address=address)

    await update.message.reply_text(
        t("reg_ask_coordinates", lang)
    )
    return COORDINATES


async def receive_coordinates(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Receive venue coordinates from location or text."""
    lang = context.user_data.get("lang", "en")
    if update.message.location:
        # Location shared via Telegram
        lat = update.message.location.latitude
        lon = update.message.location.longitude
    else:
        # Text coordinates
        try:
            coords_text = update.message.text.strip()
            parts = [p.strip() for p in coords_text.split(",")]
            if len(parts) != 2:
                raise ValueError("Expected two coordinates")
            lat = float(parts[0])
            lon = float(parts[1])
        except (ValueError, IndexError):
            await update.message.reply_text(
                t("reg_coordinates_invalid", lang)
            )
            return COORDINATES

    # Validate coordinate ranges
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        await update.message.reply_text(
            t("reg_coordinates_range", lang)
        )
        return COORDINATES

    context.user_data["latitude"] = lat
    context.user_data["longitude"] = lon
    logger.info("coordinates_received", lat=lat, lon=lon)

    await update.message.reply_text(
        t("reg_coordinates_confirmed", lang, lat=lat, lon=lon)
    )
    return PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive business photo and complete registration."""
    lang = context.user_data.get("lang", "en")
    if not update.message.photo:
        await update.message.reply_text(
            t("reg_photo_prompt", lang)
        )
        return PHOTO

    # Get largest photo
    photo = update.message.photo[-1]
    file_id = photo.file_id

    # TODO: Download and store photo using ImageStore
    context.user_data["photo_file_id"] = file_id
    logger.info("photo_received", file_id=file_id)

    # Create business registration
    try:
        business_input = BusinessInput(
            name=context.user_data["business_name"],
            telegram_id=update.effective_user.id,
            venue=Venue(
                address=context.user_data["address"],
                latitude=context.user_data["latitude"],
                longitude=context.user_data["longitude"],
            ),
            verification_status=VerificationStatus.PENDING,
        )

        # TODO: Save to database via repository
        # repo = context.bot_data.get("business_repo")
        # await repo.create(business_input)

        logger.info(
            "business_registered",
            telegram_id=update.effective_user.id,
            name=business_input.name,
        )

        await update.message.reply_text(
            t("reg_complete", lang, name=business_input.name, address=business_input.venue.address)
        )

    except Exception as e:
        logger.error("registration_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            t("reg_failed", lang)
        )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel registration conversation."""
    lang = context.user_data.get("lang", "en")
    await update.message.reply_text(
        t("reg_cancelled", lang)
    )
    context.user_data.clear()
    return ConversationHandler.END


def get_registration_handler() -> ConversationHandler:
    """Build and return the registration conversation handler."""
    return ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            COORDINATES: [
                MessageHandler(filters.LOCATION, receive_coordinates),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_coordinates),
            ],
            PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
