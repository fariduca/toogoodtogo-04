"""Business registration flow handlers."""

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from src.logging import get_logger
from src.models.business import BusinessInput, VerificationStatus
from src.models.user import UserInput, UserRole
from src.models.venue import Venue
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)

# Conversation states
ROLE_SELECTION, BUSINESS_NAME, STREET_ADDRESS, CITY, POSTAL_CODE, PHONE = range(6)


async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle role selection from /start command."""
    if not context.user_data.get("awaiting_role_selection"):
        return ConversationHandler.END
    
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    text = update.message.text
    
    # Determine role from selection
    if "Business" in text or "🏪" in text:
        role = UserRole.BUSINESS
    elif "Customer" in text or "🛍️" in text:
        role = UserRole.CUSTOMER
    else:
        await update.message.reply_text(
            "Please select a valid role using the keyboard buttons."
        )
        return ROLE_SELECTION
    
    # Create user record
    user_input = UserInput(
        telegram_user_id=telegram_user.id,
        telegram_username=telegram_user.username,
        role=role,
    )
    user = await user_repo.create(user_input)
    
    logger.info(
        "user_registered",
        user_id=user.id,
        telegram_id=telegram_user.id,
        role=role.value,
    )
    
    # Clear state
    context.user_data.pop("awaiting_role_selection", None)
    
    if role == UserRole.BUSINESS:
        # Start business registration flow
        await update.message.reply_text(
            "Great! Let's set up your business profile.\n\n"
            "Please enter your business name:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return BUSINESS_NAME
    else:
        # Customer registration complete
        await update.message.reply_text(
            "✅ You're all set!\n\n"
            "You can now:\n"
            "• /browse — Discover nearby deals\n"
            "• /myreservations — View your reservations\n\n"
            "Happy shopping! 🛍️",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


async def handle_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle business name input."""
    business_name = update.message.text.strip()
    
    if len(business_name) < 2:
        await update.message.reply_text(
            "Business name is too short. Please enter a valid business name:"
        )
        return BUSINESS_NAME
    
    context.user_data["business_name"] = business_name
    
    await update.message.reply_text(
        f"Business: {business_name}\n\n"
        "Now, please enter your street address:"
    )
    return STREET_ADDRESS


async def handle_street_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle street address input."""
    street_address = update.message.text.strip()
    
    if len(street_address) < 5:
        await update.message.reply_text(
            "Address seems too short. Please enter a complete street address:"
        )
        return STREET_ADDRESS
    
    context.user_data["street_address"] = street_address
    
    await update.message.reply_text("Please enter your city:")
    return CITY


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle city input."""
    city = update.message.text.strip()
    
    if len(city) < 2:
        await update.message.reply_text(
            "City name is too short. Please enter a valid city:"
        )
        return CITY
    
    context.user_data["city"] = city
    
    await update.message.reply_text("Please enter your postal code:")
    return POSTAL_CODE


async def handle_postal_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle postal code input."""
    postal_code = update.message.text.strip()
    
    if len(postal_code) < 3:
        await update.message.reply_text(
            "Postal code is too short. Please enter a valid postal code:"
        )
        return POSTAL_CODE
    
    context.user_data["postal_code"] = postal_code
    
    await update.message.reply_text(
        "Finally, please enter your phone number for customer contact:"
    )
    return PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle phone number and complete registration."""
    phone = update.message.text.strip()
    
    if len(phone) < 8:
        await update.message.reply_text(
            "Phone number seems too short. Please enter a valid phone number:"
        )
        return PHONE
    
    context.user_data["phone"] = phone
    
    # Get user and create business
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    business_repo: PostgresBusinessRepository = context.bot_data["business_repo"]
    telegram_user = update.effective_user
    
    user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if not user or user.role != UserRole.BUSINESS:
        await update.message.reply_text(
            "❌ Registration error. Please start again with /start"
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Create business with embedded venue
    business_input = BusinessInput(
        owner_id=user.id,
        business_name=context.user_data["business_name"],
        phone=context.user_data["phone"],
        street_address=context.user_data["street_address"],
        city=context.user_data["city"],
        postal_code=context.user_data["postal_code"],
        country_code="US",  # Default, can be enhanced later
    )
    
    business = await business_repo.create(business_input)
    
    logger.info(
        "business_registered",
        business_id=str(business.id),
        owner_id=user.id,
        business_name=business.business_name,
    )
    
    # Clear conversation data
    context.user_data.clear()
    
    await update.message.reply_text(
        "✅ Business registration submitted!\n\n"
        f"Business: {business.business_name}\n"
        f"Address: {business.venue.street_address}, {business.venue.city} {business.venue.postal_code}\n"
        f"Phone: {business.contact_phone}\n\n"
        "Your business is pending admin approval. You'll receive a notification "
        "once your business is verified and you can start posting deals.\n\n"
        "This usually takes 1-2 business days. Thank you for your patience! 🙏"
    )
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration flow."""
    context.user_data.clear()
    
    await update.message.reply_text(
        "Registration cancelled. You can start again anytime with /start",
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return ConversationHandler.END


def get_registration_conversation_handler() -> ConversationHandler:
    """Create and return registration conversation handler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handle_role_selection,
            )
        ],
        states={
            ROLE_SELECTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_role_selection)
            ],
            BUSINESS_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_business_name)
            ],
            STREET_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_street_address)
            ],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
            POSTAL_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postal_code)
            ],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
        },
        fallbacks=[MessageHandler(filters.Regex("^/cancel$"), cancel_registration)],
    )
