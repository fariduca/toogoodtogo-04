# Data Model: Language Switching (English / Russian)

**Feature**: 004-language-switching  
**Date**: 2026-02-28

## Entities

### User (EXISTING — no changes required)

The `User` entity already contains the `language_code` field. No schema migration or model changes needed.

| Field | Type | Constraints | Default | Notes |
|-------|------|-------------|---------|-------|
| id | int | PK, auto-increment | — | — |
| telegram_user_id | int | unique, indexed, >0 | — | — |
| telegram_username | str \| None | max 100 chars | None | — |
| role | UserRole | enum: BUSINESS, CUSTOMER | — | — |
| **language_code** | **str** | **min 2, max 2 chars** | **"en"** | **Valid values: "en", "ru". Already exists.** |
| notification_enabled | bool | — | True | — |
| last_location_lat | float \| None | -90 to 90 | None | — |
| last_location_lon | float \| None | -180 to 180 | None | — |
| last_location_updated | datetime \| None | — | None | — |
| created_at | datetime | — | now | — |
| updated_at | datetime | — | now (auto-update) | — |

**State transitions for `language_code`**:
- Created with default `"en"` during registration
- Updated to `"en"` or `"ru"` when user changes language via settings or /start welcome button
- Read on every handler invocation to resolve translation language
- Read on async notification dispatch for per-recipient language resolution

### Translation Catalog (NEW — code artifact, not database entity)

The translation catalog is a Python dictionary, not a database table. It is loaded at import time and held in memory.

| Attribute | Type | Description |
|-----------|------|-------------|
| Structure | `dict[str, dict[str, str]]` | Key-first: `{string_key: {"en": "...", "ru": "..."}}` |
| Keys | ~210 string keys | Named with `{domain}_{action}_{variant}` convention |
| Languages | `"en"`, `"ru"` | English is source of truth; Russian must have parity |
| Interpolation | `.format(**kwargs)` placeholders | e.g., `"Welcome back, {name}!"` |

**Key prefixes**:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `start_` | /start flow | `start_welcome_back` |
| `help_` | /help text | `help_customer` |
| `settings_` | /settings display | `settings_header` |
| `browse_` | Offer browsing | `browse_no_results` |
| `offer_` | Offer creation/management | `offer_title_prompt` |
| `reserve_` | Reservation flow | `reserve_confirmed` |
| `purchase_` | Purchase flow | `purchase_cancelled` |
| `reg_` | Registration | `reg_choose_role` |
| `approval_` | Admin approval | `approval_pending` |
| `btn_` | Button labels | `btn_confirm_reserve` |
| `err_` | Shared error messages | `err_register_first` |
| `notif_` | Async notifications | `notif_reservation_received` |

## Relationships

```
User.language_code ──references──▶ Translation Catalog language keys ("en" | "ru")
```

No new database relationships. The translation catalog is an in-memory code artifact referenced by the user's `language_code` value at runtime.

## Validation Rules

| Rule | Description |
|------|-------------|
| `language_code` must be exactly 2 characters | Already enforced by pydantic `min_length=2, max_length=2` and DB `String(2)` |
| `language_code` must be `"en"` or `"ru"` | Enforced at the handler level when processing language change callbacks |
| All keys in EN catalog must exist in RU catalog | Enforced by CI test: `assert set(strings["en"]) == set(strings["ru"])` |
| Fallback to English if key missing | Enforced in `t()` function: returns EN string or raw key, never blank |
| Interpolation placeholders must match between languages | Enforced by CI test: extract `{...}` from both variants and compare |
