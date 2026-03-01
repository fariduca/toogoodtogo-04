"""Settings command handler for language and notification preferences."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.i18n import t, get_lang, SUPPORTED_LANGUAGES
from src.logging import get_logger
from src.storage.postgres_user_repo import PostgresUserRepository

logger = get_logger(__name__)


def _build_settings_keyboard(user, lang: str) -> InlineKeyboardMarkup:
    """Build the settings inline keyboard."""
    keyboard = [
        [InlineKeyboardButton(
            t("btn_toggle_notifications", lang),
            callback_data=f"toggle_notifications:{user.id}",
        )],
        [InlineKeyboardButton(
            t("btn_change_language", lang),
            callback_data="change_language",
        )],
    ]
    return InlineKeyboardMarkup(keyboard)


def _build_settings_text(user, lang: str) -> str:
    """Build the settings message text."""
    notification_status = (
        t("settings_notification_enabled", lang)
        if user.notification_enabled
        else t("settings_notification_disabled", lang)
    )
    return t(
        "settings_header",
        lang,
        language=user.language_code.upper(),
        notification_status=notification_status,
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user settings with options to modify."""
    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user

    user = await user_repo.get_by_telegram_id(telegram_user.id)

    if not user:
        await update.message.reply_text(t("err_register_first", "en"))
        return

    lang = get_lang(user)
    text = _build_settings_text(user, lang)
    reply_markup = _build_settings_keyboard(user, lang)

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    logger.info("settings_viewed", user_id=user.id)


async def handle_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle notification toggle callback."""
    query = update.callback_query
    await query.answer()

    user_repo: PostgresUserRepository = context.bot_data["user_repo"]

    user_id_str = query.data.split(":")[1]
    user_id = int(user_id_str)

    user = await user_repo.get_by_id(user_id)

    if not user:
        await query.edit_message_text(t("err_user_not_found", "en"))
        return

    user.notification_enabled = not user.notification_enabled
    updated_user = await user_repo.update(user)

    lang = get_lang(updated_user)
    text = _build_settings_text(updated_user, lang)
    reply_markup = _build_settings_keyboard(updated_user, lang)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    logger.info(
        "notifications_toggled",
        user_id=user.id,
        enabled=updated_user.notification_enabled,
    )


async def handle_change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show language selection keyboard."""
    query = update.callback_query
    await query.answer()

    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user

    user = await user_repo.get_by_telegram_id(telegram_user.id)

    if not user:
        await query.edit_message_text(t("err_user_not_found", "en"))
        return

    lang = get_lang(user)
    keyboard = [
        [InlineKeyboardButton(
            t("btn_language_en", lang),
            callback_data="set_language:en",
        )],
        [InlineKeyboardButton(
            t("btn_language_ru", lang),
            callback_data="set_language:ru",
        )],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        t("settings_select_language", lang),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )

    logger.info("language_selection_shown", user_id=user.id)


async def handle_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set user language and re-render settings."""
    query = update.callback_query
    await query.answer()

    user_repo: PostgresUserRepository = context.bot_data["user_repo"]
    telegram_user = update.effective_user

    lang_code = query.data.split(":")[1]

    if lang_code not in SUPPORTED_LANGUAGES:
        await query.edit_message_text(t("settings_invalid_language", "en"))
        return

    user = await user_repo.get_by_telegram_id(telegram_user.id)

    if not user:
        await query.edit_message_text(t("err_user_not_found", "en"))
        return

    user.language_code = lang_code
    updated_user = await user_repo.update(user)

    lang = get_lang(updated_user)
    language_name = t(f"btn_language_{lang_code}", lang)

    # Confirm in new language, then re-render settings
    text = t("settings_language_changed", lang, language_name=language_name)
    text += "\n\n" + _build_settings_text(updated_user, lang)
    reply_markup = _build_settings_keyboard(updated_user, lang)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    logger.info(
        "language_changed",
        user_id=user.id,
        language_code=lang_code,
    )


def get_settings_handler() -> CommandHandler:
    """Create the /settings command handler."""
    return CommandHandler("settings", settings_command)


def get_settings_callback_handler() -> CallbackQueryHandler:
    """Create settings callback handlers."""
    return CallbackQueryHandler(handle_toggle_notifications, pattern=r"^toggle_notifications:")
