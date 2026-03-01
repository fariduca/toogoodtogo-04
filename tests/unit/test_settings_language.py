"""Tests for language switching via /settings.

Covers: change_language callback, set_language:ru, set_language:en,
invalid language rejection, and settings rendering in user's language.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from src.i18n import t


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_user(language_code: str = "en", notification_enabled: bool = True, user_id: int = 1):
    """Create a mock User with required attributes."""
    user = Mock()
    user.id = user_id
    user.language_code = language_code
    user.notification_enabled = notification_enabled
    return user


def _make_update_command():
    """Create a mock Update for a command (has message)."""
    update = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 12345
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    return update


def _make_update_callback(callback_data: str):
    """Create a mock Update for a callback query."""
    update = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 12345
    update.callback_query = AsyncMock()
    update.callback_query.data = callback_data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


def _make_context(user_repo=None):
    """Create a mock context with bot_data containing user_repo."""
    context = AsyncMock()
    context.bot_data = {"user_repo": user_repo or AsyncMock()}
    return context


# ── Tests ────────────────────────────────────────────────────────────────────

class TestSettingsCommand:
    @pytest.mark.asyncio
    async def test_settings_unregistered_user(self):
        from src.handlers.system.settings_handler import settings_command

        update = _make_update_command()
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=None)
        context = _make_context(user_repo)

        await settings_command(update, context)

        update.message.reply_text.assert_called_once()
        args = update.message.reply_text.call_args
        assert "register" in args[0][0].lower() or "/start" in args[0][0]

    @pytest.mark.asyncio
    async def test_settings_renders_in_user_language_en(self):
        from src.handlers.system.settings_handler import settings_command

        user = _make_user(language_code="en")
        update = _make_update_command()
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        context = _make_context(user_repo)

        await settings_command(update, context)

        call_args = update.message.reply_text.call_args
        text = call_args[0][0]
        assert "Settings" in text or "⚙️" in text
        # Should have change language button in reply_markup
        reply_markup = call_args[1].get("reply_markup") or call_args.kwargs.get("reply_markup")
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_settings_renders_in_user_language_ru(self):
        from src.handlers.system.settings_handler import settings_command

        user = _make_user(language_code="ru")
        update = _make_update_command()
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        context = _make_context(user_repo)

        await settings_command(update, context)

        call_args = update.message.reply_text.call_args
        text = call_args[0][0]
        # Should be in Russian
        assert "Настройки" in text or "⚙️" in text


class TestChangeLanguage:
    @pytest.mark.asyncio
    async def test_change_language_shows_keyboard(self):
        from src.handlers.system.settings_handler import handle_change_language

        user = _make_user(language_code="en")
        update = _make_update_callback("change_language")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        context = _make_context(user_repo)

        await handle_change_language(update, context)

        update.callback_query.answer.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        reply_markup = call_args[1].get("reply_markup") or call_args.kwargs.get("reply_markup")
        assert reply_markup is not None
        # Check buttons contain language options
        buttons = [btn for row in reply_markup.inline_keyboard for btn in row]
        callback_datas = [btn.callback_data for btn in buttons]
        assert "set_language:en" in callback_datas
        assert "set_language:ru" in callback_datas

    @pytest.mark.asyncio
    async def test_change_language_no_user(self):
        from src.handlers.system.settings_handler import handle_change_language

        update = _make_update_callback("change_language")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=None)
        context = _make_context(user_repo)

        await handle_change_language(update, context)

        call_args = update.callback_query.edit_message_text.call_args
        # Should show error
        assert "not found" in call_args[0][0].lower() or "❌" in call_args[0][0]


class TestSetLanguage:
    @pytest.mark.asyncio
    async def test_set_language_ru_updates_user(self):
        from src.handlers.system.settings_handler import handle_set_language

        user = _make_user(language_code="en")
        # After update, user has ru
        updated_user = _make_user(language_code="ru")
        update = _make_update_callback("set_language:ru")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        user_repo.update = AsyncMock(return_value=updated_user)
        context = _make_context(user_repo)

        await handle_set_language(update, context)

        # Verify user.language_code was set to "ru"
        assert user.language_code == "ru"
        user_repo.update.assert_called_once_with(user)
        # Confirmation should be in Russian
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "изменён" in text.lower() or "Русский" in text

    @pytest.mark.asyncio
    async def test_set_language_en_updates_user(self):
        from src.handlers.system.settings_handler import handle_set_language

        user = _make_user(language_code="ru")
        updated_user = _make_user(language_code="en")
        update = _make_update_callback("set_language:en")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        user_repo.update = AsyncMock(return_value=updated_user)
        context = _make_context(user_repo)

        await handle_set_language(update, context)

        assert user.language_code == "en"
        user_repo.update.assert_called_once_with(user)
        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "changed" in text.lower() or "Language" in text

    @pytest.mark.asyncio
    async def test_set_language_invalid_code_rejected(self):
        from src.handlers.system.settings_handler import handle_set_language

        update = _make_update_callback("set_language:xx")
        user_repo = AsyncMock()
        context = _make_context(user_repo)

        await handle_set_language(update, context)

        call_args = update.callback_query.edit_message_text.call_args
        text = call_args[0][0]
        assert "Invalid" in text or "❌" in text
        # user_repo.update should NOT have been called
        user_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_language_no_user(self):
        from src.handlers.system.settings_handler import handle_set_language

        update = _make_update_callback("set_language:ru")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=None)
        context = _make_context(user_repo)

        await handle_set_language(update, context)

        call_args = update.callback_query.edit_message_text.call_args
        assert "not found" in call_args[0][0].lower() or "❌" in call_args[0][0]
        user_repo.update.assert_not_called()
