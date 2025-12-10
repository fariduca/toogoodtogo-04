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
    logger.info("registration_started", user_id=user.id, username=user.username)

    await update.message.reply_text(
        "Welcome to business registration! 🏪\n\n"
        "Let's get your business set up to post offers.\n\n"
        "First, what is your business name?"
    )
    return NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and validate business name."""
    business_name = update.message.text.strip()

    if len(business_name) < 3 or len(business_name) > 100:
        await update.message.reply_text(
            "Business name must be between 3 and 100 characters. Please try again:"
        )
        return NAME

    context.user_data["business_name"] = business_name
    logger.info("business_name_received", name=business_name)

    await update.message.reply_text(
        f"Great! Business name: {business_name}\n\n"
        "Now, please provide your venue address.\n"
        "Format: Street Address, City\n"
        "Example: 123 Main St, Springfield"
    )
    return ADDRESS


async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive venue address."""
    address = update.message.text.strip()

    if len(address) < 5:
        await update.message.reply_text(
            "Please provide a valid address (minimum 5 characters):"
        )
        return ADDRESS

    context.user_data["address"] = address
    logger.info("address_received", address=address)

    await update.message.reply_text(
        "Perfect! Now I need the coordinates of your venue.\n\n"
        "Please send your location using Telegram's location sharing feature, "
        "or provide coordinates in the format: latitude, longitude\n"
        "Example: 37.7749, -122.4194"
    )
    return COORDINATES


async def receive_coordinates(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Receive venue coordinates from location or text."""
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
                "Invalid coordinates format. Please use: latitude, longitude\n"
                "Or share your location using Telegram's location feature."
            )
            return COORDINATES

    # Validate coordinate ranges
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        await update.message.reply_text(
            "Coordinates out of valid range.\n"
            "Latitude: -90 to 90, Longitude: -180 to 180"
        )
        return COORDINATES

    context.user_data["latitude"] = lat
    context.user_data["longitude"] = lon
    logger.info("coordinates_received", lat=lat, lon=lon)

    await update.message.reply_text(
        f"Location confirmed: {lat}, {lon}\n\n"
        "Finally, please upload a photo of your business.\n"
        "This helps customers recognize your venue."
    )
    return PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive business photo and complete registration."""
    if not update.message.photo:
        await update.message.reply_text(
            "Please send a photo of your business (not a file or other media)."
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
            "✅ Registration complete!\n\n"
            f"Business: {business_input.name}\n"
            f"Address: {business_input.venue.address}\n\n"
            "Your application is now pending admin verification.\n"
            "You'll be notified once approved. Thank you!"
        )

    except Exception as e:
        logger.error("registration_failed", error=str(e), exc_info=True)
        await update.message.reply_text(
            "❌ Registration failed. Please try again later or contact support."
        )

    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel registration conversation."""
    await update.message.reply_text(
        "Registration cancelled. Use /register to start again."
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
