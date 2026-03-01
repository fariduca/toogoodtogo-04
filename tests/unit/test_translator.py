"""Tests for the translation infrastructure (i18n module).

Covers: English lookup, Russian lookup, fallback behaviour, interpolation,
graceful handling of missing kwargs, EN/RU key parity, and placeholder parity.
"""

import re
from unittest.mock import Mock

import pytest

from src.i18n import t, get_lang, SUPPORTED_LANGUAGES
from src.i18n.strings import STRINGS


# ── Basic lookup ─────────────────────────────────────────────────────────────

class TestBasicLookup:
    def test_t_returns_english(self):
        assert t("err_register_first", "en") == "❌ Please use /start to register first."

    def test_t_returns_russian(self):
        result = t("err_register_first", "ru")
        assert "регистрации" in result.lower() or result != t("err_register_first", "en")

    def test_t_falls_back_to_english_for_unknown_lang(self):
        """Unknown language code falls back to English."""
        assert t("err_register_first", "fr") == t("err_register_first", "en")

    def test_t_returns_raw_key_for_missing_key(self):
        """Completely unknown key returns the key itself."""
        assert t("nonexistent_key_xyz", "en") == "nonexistent_key_xyz"

    def test_t_returns_raw_key_for_missing_key_non_english(self):
        assert t("nonexistent_key_xyz", "ru") == "nonexistent_key_xyz"


# ── Interpolation ────────────────────────────────────────────────────────────

class TestInterpolation:
    def test_t_interpolates_kwargs(self):
        result = t("start_welcome_back_business", "en", name="Alice")
        assert "Alice" in result

    def test_t_interpolates_multiple_kwargs(self):
        result = t("settings_header", "en", language="English", notification_status="Enabled")
        assert "English" in result
        assert "Enabled" in result

    def test_t_graceful_missing_kwargs(self):
        """Missing kwargs should NOT raise — template is returned with placeholders."""
        result = t("start_welcome_back_business", "en")
        # Should return the template string (with {name} still in it) rather than crashing
        assert isinstance(result, str)
        assert len(result) > 0

    def test_t_extra_kwargs_ignored(self):
        """Extra kwargs that aren't in the template are silently ignored."""
        result = t("err_register_first", "en", extra_param="ignored")
        assert result == "❌ Please use /start to register first."


# ── get_lang helper ──────────────────────────────────────────────────────────

class TestGetLang:
    def test_get_lang_returns_user_language(self):
        user = Mock()
        user.language_code = "ru"
        assert get_lang(user) == "ru"

    def test_get_lang_returns_en_for_none(self):
        assert get_lang(None) == "en"

    def test_get_lang_returns_en_default(self):
        user = Mock()
        user.language_code = "en"
        assert get_lang(user) == "en"


# ── SUPPORTED_LANGUAGES constant ─────────────────────────────────────────────

class TestSupportedLanguages:
    def test_contains_en_and_ru(self):
        assert "en" in SUPPORTED_LANGUAGES
        assert "ru" in SUPPORTED_LANGUAGES

    def test_en_is_first(self):
        assert SUPPORTED_LANGUAGES[0] == "en"


# ── Catalog integrity ────────────────────────────────────────────────────────

class TestCatalogIntegrity:
    def test_all_keys_have_english(self):
        """Every key in STRINGS must have an English translation."""
        missing_en = [k for k, v in STRINGS.items() if "en" not in v]
        assert missing_en == [], f"Keys without English: {missing_en}"

    def test_en_ru_key_parity(self):
        """Every key must exist in both EN and RU."""
        en_keys = {k for k, v in STRINGS.items() if "en" in v}
        ru_keys = {k for k, v in STRINGS.items() if "ru" in v}
        assert en_keys == ru_keys, (
            f"Missing in RU: {en_keys - ru_keys}, "
            f"Missing in EN: {ru_keys - en_keys}"
        )

    def test_format_placeholders_match(self):
        """EN and RU translations must have identical {placeholder} names."""
        ru_count = sum(1 for v in STRINGS.values() if "ru" in v)
        assert ru_count == len(STRINGS), (
            f"Only {ru_count}/{len(STRINGS)} keys have RU translations"
        )
        mismatches = []
        for key, translations in STRINGS.items():
            en_text = translations.get("en", "")
            ru_text = translations.get("ru", "")
            en_ph = set(re.findall(r"\{(\w+)\}", en_text))
            ru_ph = set(re.findall(r"\{(\w+)\}", ru_text))
            if en_ph != ru_ph:
                mismatches.append(f"{key}: EN {en_ph} != RU {ru_ph}")
        assert mismatches == [], "\n".join(mismatches)

    def test_no_empty_english_values(self):
        """No English value should be an empty string."""
        empty = [k for k, v in STRINGS.items() if v.get("en", "") == ""]
        assert empty == [], f"Empty English values: {empty}"

    def test_string_count_minimum(self):
        """Catalog should have a reasonable number of entries."""
        assert len(STRINGS) >= 50, f"Only {len(STRINGS)} strings — expected ~210"
