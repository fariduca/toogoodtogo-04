# Research: Language Switching (English / Russian)

**Feature**: 004-language-switching  
**Date**: 2026-02-28  
**Status**: Complete — all unknowns resolved

## 1. Translation Approach: Dictionary-based vs gettext vs Third-party

**Decision**: Plain Python dictionary-based approach — zero new dependencies.

**Rationale**: 
- gettext is designed for large-scale projects with dozens of languages, `.po`/`.mo` compilation steps. Overkill for 2 languages and ~200 strings.
- Babel/python-i18n add pip dependencies. Babel's primary value (locale-aware date/number formatting) is explicitly excluded by spec (FR-006b: "single consistent format regardless of language"). python-i18n adds YAML/JSON loaders that are unnecessary.
- Dictionary-based: zero dependencies (YAGNI per constitution Principle V), full IDE support, trivially testable. A `dict[str, dict[str, str]]` with ~200 keys loads instantly.

**Alternatives considered**:

| Approach | Pros | Rejected because |
|----------|------|------------------|
| gettext | Industry standard, extractor tooling | Overkill for 2 languages; `.po` workflow overhead; plural forms not needed per spec |
| Babel | Locale-aware formatting | Spec prohibits locale formatting (FR-006b); adds dependency |
| python-i18n | Simple API, file-based | Adds dependency; YAML parsing unnecessary |

## 2. String Catalog Organization

**Decision**: Single file (`src/i18n/strings.py`), key-first nested dictionary. Each key maps to `{"en": "...", "ru": "..."}`.

**Rationale**:
- ~200 strings × 2 languages = ~400 entries → ~700 lines. Manageable in one file.
- Key-first structure makes missing translations visually obvious and grep-friendly.
- Adding a new string is a single block addition.
- Parity test is trivial: `assert set(en_keys) == set(ru_keys)`.

**Alternatives considered**:

| Option | Rejected because |
|--------|------------------|
| One file per language (`en.py`, `ru.py`) | Harder to verify parity; must diff two files to find missing keys |
| One file per handler domain | Fragments catalog into 6-8 files; cross-domain strings (common errors) need a shared file, creating import chains. Useful at 1000+ strings, not 200 |
| Enum-based keys | 200-member enum is verbose; adding a string requires touching both enum and dict. String keys with a CI parity test provide equivalent safety |

**Key naming convention**: `{domain}_{action}_{variant}` with prefixes `btn_` for buttons and `err_` for common errors.

## 3. Translation Function Signature

**Decision**: `t(key: str, lang: str, **kwargs) -> str` — module-level function with `.format()` interpolation and English fallback.

**Rationale**:
- Stateless: pure function, trivially testable without mocking.
- Single import from `src/i18n`.
- `.format(**kwargs)` handles dynamic values (user names, prices, counts) since templates are data, not f-string code.
- Fallback chain: requested lang → `"en"` → raw key. Never returns blank.
- Usage: `t("welcome_back", lang, name=user.first_name)`.

**Alternatives considered**:

| Option | Rejected because |
|--------|------------------|
| Service class injected via `bot_data` | Adds 10+ chars per call; no benefit over module function for stateless lookup |
| Direct dict access `msg[lang]["key"]` | No fallback mechanism; no interpolation; couples handlers to dict shape |
| Lazy translation (resolve at send time) | User language is always known at call site (user already fetched); unnecessary complexity |

## 4. Language Resolution in Handlers

**Decision**: Extract `language_code` from the User object that handlers already fetch. No middleware.

**Rationale**:
- 20+ handlers already call `user_repo.get_by_telegram_id()` — adding `lang = user.language_code if user else "en"` is 1 line per handler, zero new DB queries.
- python-telegram-bot has no official i18n support. Community pattern is per-handler resolution.
- A TypeHandler middleware at group -1 would duplicate the DB lookup that handlers already perform.
- For async notifications (FR-011), the sender already looks up the user for their chat ID — `.language_code` is free.
- Helper: `get_lang(user) -> str` function avoids repetition.

**Alternatives considered**:

| Option | Rejected because |
|--------|------------------|
| Middleware TypeHandler at group -1 | Extra DB query per update; duplicates user lookup already done in handlers |
| Decorator `@with_language` | Changes function signatures; complicates handler registration |
| `context.user_data` cache only | Cache can be stale; still needs DB as source of truth; handlers already have user object |

**Note**: `context.user_data["lang"]` may be used as a secondary cache to avoid re-extracting from user objects in callback chains, but the DB-persisted `language_code` is the authoritative source.

## 5. String Extraction Strategy

**Decision**: Semi-automated extraction — regex scan to identify call sites, then manual key assignment handler-by-handler, migrated one domain at a time.

**Rationale**:
- `grep -n "reply_text\|edit_message_text"` across handler files identifies ~200+ call sites — each maps to exactly one translatable string.
- Fully automated AST extraction would produce false positives (log messages, callback_data patterns, structural format strings).
- Domain-by-domain migration (system → discovery → purchasing → offer_posting → offer_management → lifecycle) allows incremental testing.

**Estimated string counts by domain**:

| Domain | Handler files | Estimated strings |
|--------|--------------|-------------------|
| system (start, help, settings) | 4 | ~30 |
| discovery (browse, list_offers) | 2 | ~25 |
| purchasing (reserve, cancel, purchase_*) | 5 | ~40 |
| offer_posting (create, register, verify) | 3 | ~45 |
| offer_management (edit, pause, end, list) | 4 | ~30 |
| lifecycle (registration, approval, edit, pause) | 4 | ~40 |
| **Total** | **22** | **~210** |

**Execution order**:
1. Create `src/i18n/strings.py` with all English strings extracted
2. Create `src/i18n/__init__.py` with `t()` function
3. Migrate handlers one domain at a time, running tests after each
4. Add Russian translations after all handlers are migrated
5. Write parity test: assert EN keys == RU keys

## 6. Existing Infrastructure Inventory

**Decision**: Leverage existing `language_code` field — no schema migration needed.

**Rationale**:
- `language_code` exists on: domain model (`User`), DB model (`UserTable`), creation DTO (`UserInput`), and repository `update()` method.
- `settings_handler.py` has a commented-out `"🌐 Change Language"` button at line 47 — ready to activate.
- `callback_map.py` has 14 registered patterns — `change_language` callback needs registration.
- `postgres_user_repo.update()` already writes `language_code` to DB.
