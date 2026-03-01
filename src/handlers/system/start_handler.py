"""Startup and fallback handlers for casual users.

Provides a friendly /start command and a default text handler so that
users who send plain messages get a helpful response instead of no reply.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

from src.logging import get_logger
from src.models.user import UserInput, UserRole
from src.storage.postgres_user_repo import PostgresUserRepository
from src.i18n import t, get_lang, SUPPORTED_LANGUAGES

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message with role selection for new users or deep link handling."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user
    
    # Check for deep link parameters (format: /start <parameter>)
    if context.args and len(context.args) > 0:
        lang = context.user_data.get("lang", "en")
        param = context.args[0]
        
        # Handle deep link: offer_<offer_id>
        if param.startswith("offer_"):
            from uuid import UUID
            from src.handlers.discovery.list_offers_handler import view_offer_details
            
            offer_id = param.replace("offer_", "")
            try:
                # Create a mock callback query to reuse view_offer_details
                # Note: This is a simplified approach; ideally refactor view_offer_details
                # to accept both callback queries and direct calls
                await update.message.reply_text(
                    t("start_deep_link_loading", lang),
                )
                
                keyboard = [[
                    InlineKeyboardButton(t("btn_view_offer", lang), callback_data=f"view_offer:{offer_id}")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    t("start_deep_link_view", lang),
                    reply_markup=reply_markup
                )
                
                logger.info(
                    "deep_link_offer_accessed",
                    user_id=telegram_user.id,
                    offer_id=offer_id
                )
                return
            
            except Exception as e:
                logger.error("deep_link_offer_failed", error=str(e), exc_info=True)
                await update.message.reply_text(
                    t("start_deep_link_invalid", lang)
                )
                return
        
        # Handle deep link: business_invite_<token> (future feature)
        elif param.startswith("business_invite_"):
            token = param.replace("business_invite_", "")
            # TODO: Implement business invitation flow
            await update.message.reply_text(
                t("start_business_invite", lang)
            )
            logger.info(
                "deep_link_business_invite_accessed",
                user_id=telegram_user.id,
                token=token
            )
            return
    
    # Check if user already exists
    existing_user = await user_repo.get_by_telegram_id(telegram_user.id)
    
    if existing_user:
        lang = get_lang(existing_user)
        # Returning user - show personalized welcome
        if existing_user.role == UserRole.BUSINESS:
            text = t("start_welcome_back_business", lang, name=telegram_user.first_name)
        else:
            text = t("start_welcome_back_customer", lang, name=telegram_user.first_name)
        await update.message.reply_text(text)
        return
    
    # New user - prompt for role selection
    lang = context.user_data.get("lang", "en")
    keyboard = [
        [t("start_role_business", lang)],
        [t("start_role_customer", lang)],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    
    text = t("start_welcome_new", lang, name=telegram_user.first_name)
    
    # Add inline language button for quick language switch
    inline_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            t("start_btn_set_language", lang),
            callback_data="start_set_language:ru" if lang == "en" else "start_set_language:en",
        )
    ]])
    
    await update.message.reply_text(text, reply_markup=reply_markup)
    
    # Send language switch option as a follow-up with inline button
    await update.message.reply_text(
        t("settings_select_language", lang),
        reply_markup=inline_keyboard,
    )
    
    # Store state for next message handler
    context.user_data["awaiting_role_selection"] = True


async def default_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback for plain text messages — give a short helpful nudge."""
    lang = context.user_data.get("lang", "en")
    logger.info("received_plain_message", user_id=update.effective_user.id)
    await update.message.reply_text(
        t("start_default_message", lang)
    )


async def handle_start_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection from /start welcome for new users.

    Callback data format: start_set_language:{code}
    Sets language preference and re-renders the welcome message in the selected language.
    """
    query = update.callback_query
    await query.answer()

    code = query.data.split(":", 1)[1]
    if code not in SUPPORTED_LANGUAGES:
        await query.edit_message_text(t("settings_invalid_language", "en"))
        return

    telegram_user = update.effective_user

    # Check if user is already registered — update DB if so
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    existing_user = await user_repo.get_by_telegram_id(telegram_user.id)

    if existing_user:
        existing_user.language_code = code
        await user_repo.update(existing_user)
        lang = code
    else:
        # Not yet registered — store preference in user_data for registration flow
        context.user_data["lang"] = code
        lang = code

    # Re-render the language selection message in the new language
    new_button_code = "ru" if code == "en" else "en"
    inline_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            t("start_btn_set_language", lang),
            callback_data=f"start_set_language:{new_button_code}",
        )
    ]])

    language_name = "Русский" if code == "ru" else "English"
    await query.edit_message_text(
        t("settings_language_changed", lang, language_name=language_name),
        reply_markup=inline_keyboard,
    )

    logger.info(
        "start_language_set",
        user_id=telegram_user.id,
        language=code,
    )


def get_start_handler() -> CommandHandler:
    return CommandHandler("start", start_command)


def get_default_message_handler() -> MessageHandler:
    # Catch plain text messages that are not commands
    return MessageHandler(filters.TEXT & ~filters.COMMAND, default_message)
