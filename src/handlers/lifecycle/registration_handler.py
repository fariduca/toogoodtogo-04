"""Business registration flow handlers."""

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from src.i18n import t
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
    lang = context.user_data.get("lang", "en")
    if not context.user_data.get("awaiting_role_selection"):
        # Not in registration flow - don't handle this message
        # Returning None allows other handlers to process it
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
            t("reg_select_role", lang)
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
            t("reg_business_setup", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return BUSINESS_NAME
    else:
        # Customer registration complete
        await update.message.reply_text(
            t("reg_customer_complete", lang),
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


async def handle_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle business name input."""
    lang = context.user_data.get("lang", "en")
    business_name = update.message.text.strip()
    
    if len(business_name) < 2:
        await update.message.reply_text(
            t("reg_name_short", lang)
        )
        return BUSINESS_NAME
    
    context.user_data["business_name"] = business_name
    
    await update.message.reply_text(
        t("reg_name_confirm", lang, name=business_name)
    )
    return STREET_ADDRESS


async def handle_street_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle street address input."""
    lang = context.user_data.get("lang", "en")
    street_address = update.message.text.strip()
    
    if len(street_address) < 5:
        await update.message.reply_text(
            t("reg_address_short", lang)
        )
        return STREET_ADDRESS
    
    context.user_data["street_address"] = street_address
    
    await update.message.reply_text(t("reg_ask_city", lang))
    return CITY


async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle city input."""
    lang = context.user_data.get("lang", "en")
    city = update.message.text.strip()
    
    if len(city) < 2:
        await update.message.reply_text(
            t("reg_city_short", lang)
        )
        return CITY
    
    context.user_data["city"] = city
    
    await update.message.reply_text(t("reg_ask_postal", lang))
    return POSTAL_CODE


async def handle_postal_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle postal code input."""
    lang = context.user_data.get("lang", "en")
    postal_code = update.message.text.strip()
    
    if len(postal_code) < 3:
        await update.message.reply_text(
            t("reg_postal_short", lang)
        )
        return POSTAL_CODE
    
    context.user_data["postal_code"] = postal_code
    
    await update.message.reply_text(
        t("reg_ask_phone", lang)
    )
    return PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle phone number and complete registration."""
    lang = context.user_data.get("lang", "en")
    phone = update.message.text.strip()
    
    if len(phone) < 8:
        await update.message.reply_text(
            t("reg_phone_short", lang)
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
            t("reg_error", lang)
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
        country_code="TJ",  # Default, can be enhanced later
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
        t("reg_business_submitted", lang, business_name=business.business_name, address=business.venue.street_address, city=business.venue.city, postal=business.venue.postal_code, phone=business.contact_phone)
    )
    
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration flow."""
    lang = context.user_data.get("lang", "en")
    context.user_data.clear()
    
    await update.message.reply_text(
        t("reg_lifecycle_cancelled", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    
    return ConversationHandler.END


def get_registration_conversation_handler() -> ConversationHandler:
    """Create and return registration conversation handler.
    
    Note: This handler uses per_message=False (default) which means it tracks
    conversations per user. The entry point filter checks for 'awaiting_role_selection'
    flag set by /start command to avoid catching unrelated messages.
    """
    # Define a custom filter that only matches when user is awaiting role selection
    class AwaitingRoleFilter(filters.MessageFilter):
        def filter(self, message) -> bool:
            # We can't access context here, so we rely on the text patterns
            # that are expected for role selection
            if message.text:
                text = message.text.strip()
                return ("Business" in text or "🏪" in text or 
                        "Customer" in text or "🛍️" in text)
            return False
    
    awaiting_role_filter = AwaitingRoleFilter()
    
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                awaiting_role_filter & filters.TEXT & ~filters.COMMAND,
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
