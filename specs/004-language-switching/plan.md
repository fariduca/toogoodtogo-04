# Implementation Plan: Language Switching (English / Russian)

**Branch**: `004-language-switching` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-language-switching/spec.md`

## Summary

Add English/Russian language switching to the Telegram marketplace bot. Users select their preferred language via /settings (or an inline button on first /start). All system-generated text across ~28 handler files is extracted into a dictionary-based translation catalog with English and Russian variants. The existing `language_code` field on the User model and database is already persisted and round-tripped — no schema migration needed. A lightweight translation module resolves strings by key + language code, falling back to English for missing keys. Date/time/currency formatting remains constant across languages; only labels are translated. Numeric values use label-colon-number format to avoid Russian plural complexity.

## Technical Context

**Language/Version**: Python 3.12+ (pinned in pyproject.toml)
**Primary Dependencies**: python-telegram-bot 21.7, pydantic 2.9.2, pydantic-settings 2.6.1, SQLAlchemy 2.0.36, structlog 24.4.0, redis 5.2.0
**Storage**: PostgreSQL (via asyncpg 0.30.0, psycopg2-binary 2.9.11; Alembic 1.14.0 for migrations). `language_code` column already exists on `users` table.
**Testing**: pytest 8.3.3, ruff 0.7.4 (lint). Constitution requires ≥80% line coverage, 100% for handler normalization functions.
**Target Platform**: Linux server (Docker container), Telegram Bot API
**Project Type**: Single project — `src/` + `tests/`
**Performance Goals**: Average command handler latency <300ms (per constitution). Language switching must add <200ms (per SC-005).
**Constraints**: No new external dependencies for i18n (dictionary-based approach). All ~200+ hardcoded strings must be extracted. Russian translations must cover 100% of system text.
**Scale/Scope**: ~28 handler files, ~14 callback patterns, ~15 command handlers. Two languages: `en`, `ru`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| I. Event-Driven Minimal Core | Feature logic in isolated handler modules; zero implicit shared state; explicit DI | **PASS** | Translation catalog will be injected via `bot_data` (same pattern as existing services). Language resolution is a pure function (key + lang → string). No shared mutable state. |
| II. Test-First & Contracted | Define contracts first; write failing tests; ≥80% coverage, 100% for normalization | **PASS** | Translation catalog has a clear contract (key lookup with fallback). Each handler's string extraction is independently testable. Tests will verify key completeness and fallback behavior. |
| III. Secure & Privacy-Conscious | Minimize data retention; secrets from env; PII scrubbed from logs | **PASS** | `language_code` is not PII. No new secrets introduced. No raw message content stored. No sensitive data in translation strings. |
| V. Simplicity & Explicitness | YAGNI; no feature without user scenario and test coverage | **PASS** | Only two languages (en, ru) per spec. No over-engineering (no gettext, no ICU, no third-party i18n lib). Dictionary-based lookup is the simplest viable approach. |
| Technical Constraints | Python 3.12+, async, ruff + pytest, structured logging, <300ms latency | **PASS** | Dictionary lookup is O(1), adds negligible latency. No new dependencies needed. Async compatibility maintained. |
| Quality Gates | CI green (lint, type, tests, coverage) before merge | **PASS** | All new code will include tests. String catalog completeness can be validated in CI. |

**Gate result: ALL PASS** — no violations, no justifications needed. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-language-switching/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── translation-api.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── i18n/                    # NEW — translation infrastructure
│   ├── __init__.py
│   ├── translator.py        # get_text(key, lang) function + TranslationService
│   └── strings/
│       ├── __init__.py
│       ├── en.py            # English string catalog (extracted from existing handlers)
│       └── ru.py            # Russian string catalog
├── models/
│   └── user.py              # EXISTING — language_code field already present
├── config/
│   └── settings.py          # EXISTING — no changes needed
├── handlers/
│   ├── system/
│   │   ├── settings_handler.py   # MODIFY — activate language button, add change_language callback
│   │   ├── start_handler.py      # MODIFY — add inline language button to welcome message
│   │   └── help_handler.py       # MODIFY — extract strings
│   ├── discovery/                # MODIFY — extract strings from browse/list handlers
│   ├── lifecycle/                # MODIFY — extract strings from registration/approval/edit/pause
│   ├── offer_posting/            # MODIFY — extract strings from create/business_registration/verify
│   ├── offer_management/         # MODIFY — extract strings from list/pause_resume/end/edit
│   └── purchasing/               # MODIFY — extract strings from reserve/cancel/purchase handlers
├── bot/
│   ├── run.py              # MODIFY — register TranslationService in bot_data
│   └── callback_map.py     # MODIFY — register change_language callback handler
├── storage/
│   └── postgres_user_repo.py    # EXISTING — language_code already wired in update()
└── services/                    # NO CHANGES — business services don't contain UI strings

tests/
├── unit/
│   ├── test_translator.py       # NEW — translation catalog tests (fallback, completeness, key lookup)
│   └── test_settings_language.py # NEW — language switching handler tests
├── contract/                    # EXISTING — no changes
└── integration/
    └── test_language_flow.py    # NEW — end-to-end language switching integration test
```

**Structure Decision**: Single project layout (matching existing structure). New `src/i18n/` package for translation infrastructure. All handler modifications are in-place string extraction — no structural changes to handler packages.

## Complexity Tracking

> No constitution violations found — this section is intentionally empty.

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design completion.*

| Principle | Post-Design Status | Notes |
|-----------|-------------------|-------|
| I. Event-Driven Minimal Core | **PASS** | `src/i18n/` is a stateless utility module, not a handler. Pure functions (`t()`, `get_lang()`), zero shared mutable state. Handlers remain isolated plugins. |
| II. Test-First & Contracted | **PASS** | Contract defined in `contracts/translation-api.md`. Tests: catalog parity (EN==RU), fallback chain, interpolation, placeholder matching between languages. |
| III. Secure & Privacy-Conscious | **PASS** | No PII in translations. No new secrets. `language_code` is not sensitive data. No raw message content stored. |
| V. Simplicity & Explicitness | **PASS** | Simplest viable approach: dict lookup, no external deps, no plural engine, no locale formatting. Only 2 languages per spec. |
| Technical Constraints | **PASS** | O(1) dict lookup adds negligible latency. No new pip dependencies. Async-compatible (stateless). |
| Quality Gates | **PASS** | CI tests enforce key completeness, placeholder parity, and fallback behavior. Ruff + pytest coverage maintained. |

**Post-design gate result: ALL PASS** — design introduces no constitution violations.
