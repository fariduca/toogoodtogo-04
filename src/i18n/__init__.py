"""Internationalization module for the Telegram bot.

Provides string localization via a dictionary-based translation catalog.
Exports:
    t(key, lang, **kwargs) -> str: Translate a string by key and language.
    get_lang(user) -> str: Extract language code from a User object.
    SUPPORTED_LANGUAGES: List of supported language codes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.i18n.strings import STRINGS

if TYPE_CHECKING:
    from src.models.user import User

SUPPORTED_LANGUAGES: list[str] = ["en", "ru"]


def t(key: str, lang: str, **kwargs: object) -> str:
    """Resolve a translated string by key and language code.

    Fallback chain:
        1. Look up key in catalog for requested lang.
        2. If missing → look up key for "en" (English fallback).
        3. If missing → return key as-is (raw key, ensures never blank).

    Interpolation via str.format(**kwargs) is applied when kwargs are
    provided.  If a placeholder is missing from kwargs, the template
    is returned as-is (no crash).

    Args:
        key: Translation key (e.g. "err_register_first").
        lang: ISO 639-1 language code ("en" or "ru").
        **kwargs: Named values for .format() interpolation.

    Returns:
        The translated, interpolated string.  Never empty, never raises.
    """
    translations = STRINGS.get(key, {})
    template = translations.get(lang) or translations.get("en", key)
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError, ValueError):
        return template


def get_lang(user: User | None) -> str:
    """Extract language code from a User object with English fallback.

    Args:
        user: The domain User object, or None for unauthenticated contexts.

    Returns:
        user.language_code if user is not None, otherwise "en".
    """
    if user is not None:
        return user.language_code
    return "en"
