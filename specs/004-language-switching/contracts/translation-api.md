# Contract: Translation API

**Feature**: 004-language-switching  
**Date**: 2026-02-28  
**Type**: Internal Python API (not HTTP)

## Overview

The translation API is an internal module providing string localization for the Telegram bot. It consists of a translation function `t()` and the string catalog it reads from. This is a Python module contract, not a REST/HTTP endpoint.

## Module: `src/i18n`

### Function: `t(key, lang, **kwargs) -> str`

Resolve a translated string by key and language code, with optional parameter interpolation.

**Signature**:
```python
def t(key: str, lang: str, **kwargs: object) -> str
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | `str` | Yes | Translation key (e.g., `"start_welcome_back"`) |
| `lang` | `str` | Yes | ISO 639-1 language code: `"en"` or `"ru"` |
| `**kwargs` | `object` | No | Named values for `.format()` interpolation |

**Return**: `str` — The translated, interpolated string. Never empty, never raises.

**Fallback chain**:
1. Look up `key` in catalog for requested `lang`
2. If missing → look up `key` for `"en"` (English fallback)
3. If missing → return `key` as-is (raw key, ensures never blank)

**Examples**:

```python
from src.i18n import t

# Simple lookup
t("err_register_first", "ru")
# → "❌ Пожалуйста, используйте /start для регистрации."

# With interpolation
t("start_welcome_back", "en", name="Alice")
# → "👋 Welcome back, Alice!"

# Fallback: key exists in EN but missing in RU
t("some_untranslated_key", "ru")
# → Returns English version

# Fallback: key doesn't exist at all
t("nonexistent_key", "en")
# → "nonexistent_key"

# Invalid interpolation (graceful)
t("start_welcome_back", "en")  # missing 'name' kwarg
# → "👋 Welcome back, {name}!"  (template returned as-is)
```

### Function: `get_lang(user) -> str`

Extract language code from a User object with English fallback.

**Signature**:
```python
def get_lang(user: User | None) -> str
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user` | `User \| None` | Yes | The domain User object, or None for unauthenticated contexts |

**Return**: `str` — `user.language_code` if user is not None, otherwise `"en"`.

### Constant: `SUPPORTED_LANGUAGES`

```python
SUPPORTED_LANGUAGES: list[str] = ["en", "ru"]
```

### Constant: `STRINGS`

```python
STRINGS: dict[str, dict[str, str]]
```

Key-first dictionary containing all translation entries. Structure:

```python
{
    "key_name": {
        "en": "English text with optional {placeholder}",
        "ru": "Русский текст с {placeholder}",
    },
    ...
}
```

## Contract: Language Change Callback

### Callback: `change_language`

**Trigger**: User presses "🌐 Change Language" button in /settings  
**Callback data**: `"change_language"`  
**Action**: Display language selection keyboard with both options

### Callback: `set_language:{code}`

**Trigger**: User selects a specific language from the selection keyboard  
**Callback data**: `"set_language:en"` or `"set_language:ru"`  
**Action**:
1. Parse language code from callback data
2. Validate code is in `SUPPORTED_LANGUAGES`
3. Update `user.language_code` via `user_repo.update()`
4. Respond with confirmation in the newly selected language
5. Re-render settings view in the new language

### Callback: `start_set_language:{code}`

**Trigger**: New user presses "🌐 Русский" button on /start welcome message  
**Callback data**: `"start_set_language:ru"`  
**Action**:
1. Set language for the user (update if already registered, or store in `context.user_data` for pending registration)
2. Re-render the welcome message in the selected language
3. Continue registration flow in the selected language

## Contract: Settings View Update

### Current settings display (to be modified)

**Before** (existing):
```
⚙️ Settings
Language: EN
Notifications: ✅ Enabled

[🔔 Toggle Notifications]
```

**After** (with language switching):
```
⚙️ Settings                    |  ⚙️ Настройки
Language: English 🇬🇧            |  Язык: Русский 🇷🇺
Notifications: ✅ Enabled       |  Уведомления: ✅ Включены

[🌐 Change Language]            |  [🌐 Сменить язык]
[🔔 Toggle Notifications]      |  [🔔 Переключить уведомления]
```

## Invariants

1. `t()` MUST never return an empty string
2. `t()` MUST never raise an exception
3. All keys present in EN catalog MUST be present in RU catalog (enforced by tests)
4. All `.format()` placeholders in EN MUST match those in RU for the same key (enforced by tests)
5. `language_code` on User MUST only be set to values in `SUPPORTED_LANGUAGES`
6. Language change MUST be persisted to database immediately (no deferred writes)
7. Language change confirmation MUST be displayed in the newly selected language (not the old one)
