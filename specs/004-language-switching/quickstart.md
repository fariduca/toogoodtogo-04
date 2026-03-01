# Quickstart: Language Switching (English / Russian)

**Feature**: 004-language-switching  
**Date**: 2026-02-28

## Prerequisites

- Python 3.12+
- Existing development environment set up (`pip install -r requirements.txt`)
- PostgreSQL database running (existing `users` table with `language_code` column)
- Bot token configured in `.env`

No new dependencies required. No database migration required.

## Implementation Order

### Step 1: Create translation infrastructure

Create `src/i18n/` package with:
- `__init__.py` — exports `t()`, `get_lang()`, `SUPPORTED_LANGUAGES`
- `strings.py` — string catalog with all EN + RU entries

```python
# src/i18n/__init__.py
from src.i18n.strings import STRINGS

SUPPORTED_LANGUAGES = ["en", "ru"]

def t(key: str, lang: str, **kwargs: object) -> str:
    translations = STRINGS.get(key, {})
    template = translations.get(lang) or translations.get("en", key)
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template

def get_lang(user) -> str:
    return user.language_code if user else "en"
```

### Step 2: Write tests for translation infrastructure

```python
# tests/unit/test_translator.py
from src.i18n import t, get_lang, SUPPORTED_LANGUAGES
from src.i18n.strings import STRINGS

def test_t_returns_english():
    assert t("err_register_first", "en") == "❌ Please use /start to register first."

def test_t_returns_russian():
    result = t("err_register_first", "ru")
    assert "регистрации" in result

def test_t_falls_back_to_english():
    assert t("err_register_first", "fr") == t("err_register_first", "en")

def test_t_returns_key_for_missing():
    assert t("nonexistent_key_xyz", "en") == "nonexistent_key_xyz"

def test_t_interpolates():
    result = t("start_welcome_back", "en", name="Alice")
    assert "Alice" in result

def test_all_languages_have_same_keys():
    en_keys = {k for k, v in STRINGS.items() if "en" in v}
    ru_keys = {k for k, v in STRINGS.items() if "ru" in v}
    assert en_keys == ru_keys, f"Missing in RU: {en_keys - ru_keys}, Missing in EN: {ru_keys - en_keys}"

def test_format_placeholders_match():
    import re
    for key, translations in STRINGS.items():
        en_placeholders = set(re.findall(r'\{(\w+)\}', translations.get("en", "")))
        ru_placeholders = set(re.findall(r'\{(\w+)\}', translations.get("ru", "")))
        assert en_placeholders == ru_placeholders, f"Key '{key}': EN {en_placeholders} != RU {ru_placeholders}"
```

### Step 3: Extract strings from handlers (domain by domain)

For each handler file:
1. Find all `reply_text()` and `edit_message_text()` calls
2. Extract the string into `strings.py` with an appropriate key
3. Replace the hardcoded string with `t(key, lang, ...)`
4. Add `lang = get_lang(user)` near the top of the handler function
5. Run tests after each file

Example transformation:
```python
# BEFORE
await update.message.reply_text(
    f"👋 Welcome back, {telegram_user.first_name}!\n\n"
)

# AFTER
from src.i18n import t, get_lang
lang = get_lang(user)
await update.message.reply_text(
    t("start_welcome_back", lang, name=telegram_user.first_name)
)
```

### Step 4: Activate language switching in settings

1. Uncomment the "🌐 Change Language" button in `settings_handler.py`
2. Add `change_language` callback handler
3. Add `set_language:{code}` callback handler
4. Register both in `callback_map.py`

### Step 5: Add language button to /start

1. Add inline "🌐 Русский" button to the welcome message in `start_handler.py`
2. Add `start_set_language:{code}` callback handler
3. Register in `callback_map.py`

### Step 6: Add Russian translations

Fill in all RU values in `strings.py`. Run the parity test to ensure completeness.

### Step 7: Integration testing

Test the full flow: /start → select Russian → /settings → verify Russian → /browse → verify Russian → switch back to English → verify English.

## Verification

```bash
# Run all tests
cd src && pytest

# Run only translation tests
cd src && pytest tests/unit/test_translator.py -v

# Check linting
cd src && ruff check .

# Manual test: start bot and exercise language switching
python -m src.bot.run
```

## Key Files to Create/Modify

| Action | File | Purpose |
|--------|------|---------|
| CREATE | `src/i18n/__init__.py` | `t()`, `get_lang()`, `SUPPORTED_LANGUAGES` |
| CREATE | `src/i18n/strings.py` | Translation catalog (~210 keys × 2 languages) |
| CREATE | `tests/unit/test_translator.py` | Translation function + catalog parity tests |
| MODIFY | `src/handlers/system/settings_handler.py` | Activate language button, add change handler |
| MODIFY | `src/handlers/system/start_handler.py` | Add language button to welcome message |
| MODIFY | `src/bot/callback_map.py` | Register `change_language`, `set_language:`, `start_set_language:` callbacks |
| MODIFY | `src/bot/run.py` | (Optional) Register translation service in `bot_data` |
| MODIFY | All 22 handler files | Replace hardcoded strings with `t()` calls |
| CREATE | `tests/unit/test_settings_language.py` | Language switching handler tests |
| CREATE | `tests/integration/test_language_flow.py` | End-to-end language flow test |
