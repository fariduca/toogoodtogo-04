"""Integration tests for the language switching feature (004-language-switching).

Tests cover:
1. New user /start with language button
2. Language switch via settings
3. Settings persistence across sessions
4. Notification language per recipient (FR-011)
5. Fallback for missing translation key
"""

import re
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.i18n import t, get_lang, SUPPORTED_LANGUAGES
from src.i18n.strings import STRINGS


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_update(
    user_id: int = 12345,
    first_name: str = "TestUser",
    username: str = "testuser",
    text: str = "/start",
    callback_data: str | None = None,
):
    """Create a mock Update with effective_user and message/callback_query."""
    update = AsyncMock()
    user = Mock()
    user.id = user_id
    user.first_name = first_name
    user.username = username
    update.effective_user = user

    if callback_data:
        query = AsyncMock()
        query.data = callback_data
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        update.message = None
    else:
        update.message = AsyncMock()
        update.message.text = text
        update.message.reply_text = AsyncMock()
        update.callback_query = None

    return update


def _make_context(bot_data: dict | None = None, user_data: dict | None = None):
    """Create a mock context with bot_data and user_data."""
    context = MagicMock()
    context.bot_data = bot_data or {}
    context.user_data = user_data if user_data is not None else {}
    context.args = []
    context.bot = AsyncMock()
    return context


def _mock_user(
    user_id: str = "user-1",
    telegram_user_id: int = 12345,
    role: str = "CUSTOMER",
    language_code: str = "en",
):
    """Create a mock user domain object."""
    user = Mock()
    user.id = user_id
    user.telegram_user_id = telegram_user_id
    user.role = Mock()
    user.role.value = role
    user.role.__eq__ = lambda self, other: self.value == getattr(other, "value", other)
    user.language_code = language_code
    user.notifications_enabled = True
    return user


# ── Test 1: New user /start — welcome with language button ──────────────────


class TestNewUserStartLanguageButton:
    """Verify /start for new users shows an inline language button."""

    async def test_new_user_start_shows_language_button(self):
        """New user /start should send a follow-up message with language button."""
        from src.handlers.system.start_handler import start_command

        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=None)

        update = _make_update()
        context = _make_context(
            bot_data={"user_repo": user_repo},
            user_data={},
        )

        await start_command(update, context)

        # First call: welcome message with role keyboard
        # Second call: language selection with inline button
        assert update.message.reply_text.call_count == 2

        # Check the second call has "start_set_language" callback
        second_call = update.message.reply_text.call_args_list[1]
        reply_markup = second_call.kwargs.get("reply_markup") or second_call[1].get("reply_markup")
        assert reply_markup is not None

        # Verify inline button has start_set_language callback data
        buttons = reply_markup.inline_keyboard
        found = False
        for row in buttons:
            for btn in row:
                if "start_set_language:" in btn.callback_data:
                    found = True
        assert found, "Expected a start_set_language: callback button"


# ── Test 2: Switch language via /settings ────────────────────────────────────


class TestSettingsLanguageSwitch:
    """Verify language switching via /settings → Change Language → select language."""

    async def test_set_language_to_russian_via_settings(self):
        """Tapping set_language:ru should update user and confirm in Russian."""
        from src.handlers.system.settings_handler import handle_set_language

        user = _mock_user(language_code="en")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        user_repo.update = AsyncMock(return_value=user)

        update = _make_update(callback_data="set_language:ru")
        context = _make_context(bot_data={"user_repo": user_repo})

        await handle_set_language(update, context)

        # User language should be updated to "ru"
        assert user.language_code == "ru"
        user_repo.update.assert_called_once()

        # Confirmation message should be in Russian
        edit_text = update.callback_query.edit_message_text
        edit_text.assert_called()
        msg = edit_text.call_args[0][0] if edit_text.call_args[0] else edit_text.call_args.kwargs.get("text", "")
        # The confirmation should contain the Russian language-changed string
        assert "Русский" in msg or "изменён" in msg

    async def test_set_language_to_english_via_settings(self):
        """set_language:en should update user and confirm in English."""
        from src.handlers.system.settings_handler import handle_set_language

        user = _mock_user(language_code="ru")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)
        user_repo.update = AsyncMock(return_value=user)

        update = _make_update(callback_data="set_language:en")
        context = _make_context(bot_data={"user_repo": user_repo})

        await handle_set_language(update, context)

        assert user.language_code == "en"
        user_repo.update.assert_called_once()


# ── Test 3: Settings persistence across sessions ────────────────────────────


class TestLanguagePersistenceAcrossSessions:
    """Verify language persists: set RU → re-open /settings → renders in RU."""

    async def test_settings_renders_in_persisted_language(self):
        """After setting Russian, reopening /settings should show Russian text."""
        from src.handlers.system.settings_handler import settings_command

        user = _mock_user(language_code="ru")
        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=user)

        update = _make_update(text="/settings")
        context = _make_context(bot_data={"user_repo": user_repo})

        await settings_command(update, context)

        msg = update.message.reply_text.call_args[0][0]
        # Should contain Russian text from settings_header
        assert "Настройки" in msg, f"Expected Russian 'Настройки' in settings, got: {msg}"


# ── Test 4: Notification language per recipient (FR-011) ─────────────────────


class TestNotificationLanguagePerRecipient:
    """Verify cross-party notifications use the recipient's language, not sender's."""

    async def test_approval_notification_uses_owner_language(self):
        """When admin (EN) approves a business, owner (RU) gets notification in Russian."""
        from src.handlers.lifecycle.approval_handler import handle_approve_business

        # Admin user (English)
        admin_user = _mock_user(
            user_id="admin-1",
            telegram_user_id=99999,
            language_code="en",
        )

        # Business owner (Russian)
        owner_user = _mock_user(
            user_id="owner-1",
            telegram_user_id=77777,
            language_code="ru",
        )

        # Business
        business = Mock()
        business.id = "00000000-0000-0000-0000-000000000001"
        business.business_name = "Тест Бизнес"
        business.owner_id = "owner-1"

        user_repo = AsyncMock()
        user_repo.get_by_telegram_id = AsyncMock(return_value=admin_user)
        user_repo.get_by_id = AsyncMock(return_value=owner_user)

        business_repo = AsyncMock()
        business_repo.approve_business = AsyncMock(return_value=business)

        permission_checker = Mock()
        permission_checker.is_admin = Mock(return_value=True)

        update = _make_update(
            user_id=99999,
            callback_data="approve_business:00000000-0000-0000-0000-000000000001",
        )
        context = _make_context(
            bot_data={
                "user_repo": user_repo,
                "business_repo": business_repo,
                "permission_checker": permission_checker,
            },
        )

        await handle_approve_business(update, context)

        # The bot.send_message should be called with Russian text for the owner
        context.bot.send_message.assert_called_once()
        call_kwargs = context.bot.send_message.call_args
        sent_text = call_kwargs.kwargs.get("text") or call_kwargs[1].get("text", "")
        
        # The notification to owner should be in Russian (FR-011)
        expected_ru = t("notif_business_approved", "ru", business_name="Тест Бизнес")
        assert sent_text == expected_ru, (
            f"Expected owner notification in Russian:\n{expected_ru}\n\nGot:\n{sent_text}"
        )


# ── Test 5: Fallback for missing translation key ────────────────────────────


class TestFallbackForMissingKey:
    """Verify graceful fallback when a translation key doesn't exist."""

    def test_missing_key_returns_raw_key(self):
        """t() with a non-existent key should return the key itself, not crash."""
        result = t("this_key_does_not_exist_12345", "en")
        assert result == "this_key_does_not_exist_12345"

    def test_missing_key_returns_raw_key_russian(self):
        """Same fallback for Russian."""
        result = t("this_key_does_not_exist_12345", "ru")
        assert result == "this_key_does_not_exist_12345"

    def test_unknown_lang_falls_back_to_english(self):
        """Unknown language code falls back to English."""
        en_result = t("err_register_first", "en")
        fr_result = t("err_register_first", "fr")
        assert en_result == fr_result

    def test_russian_translation_available(self):
        """Verify Russian translations are present and different from English."""
        en = t("err_register_first", "en")
        ru = t("err_register_first", "ru")
        assert en != ru, "Russian translation should differ from English"
        assert "регистрации" in ru.lower()


# ── Test 6: Full catalog parity ──────────────────────────────────────────────


class TestFullCatalogParity:
    """Cross-cutting validation of the entire translation catalog."""

    def test_all_keys_have_both_languages(self):
        """Every key in STRINGS must have both 'en' and 'ru' entries."""
        en_only = [k for k, v in STRINGS.items() if "en" in v and "ru" not in v]
        ru_only = [k for k, v in STRINGS.items() if "ru" in v and "en" not in v]
        assert en_only == [], f"Keys with EN but no RU: {en_only}"
        assert ru_only == [], f"Keys with RU but no EN: {ru_only}"

    def test_placeholder_parity(self):
        """All {placeholders} must match between EN and RU."""
        mismatches = []
        for key, val in STRINGS.items():
            en_text = val.get("en", "")
            ru_text = val.get("ru", "")
            en_ph = set(re.findall(r"\{(\w+)\}", en_text))
            ru_ph = set(re.findall(r"\{(\w+)\}", ru_text))
            if en_ph != ru_ph:
                mismatches.append(f"{key}: EN {en_ph} != RU {ru_ph}")
        assert mismatches == [], "Placeholder mismatches:\n" + "\n".join(mismatches)

    def test_supported_languages_list(self):
        """SUPPORTED_LANGUAGES must include en and ru."""
        assert "en" in SUPPORTED_LANGUAGES
        assert "ru" in SUPPORTED_LANGUAGES

    def test_get_lang_with_none_user(self):
        """get_lang(None) should return 'en' as default."""
        assert get_lang(None) == "en"

    def test_minimum_key_count(self):
        """The catalog should have at least 200 keys."""
        assert len(STRINGS) >= 200, f"Expected ≥200 keys, got {len(STRINGS)}"
