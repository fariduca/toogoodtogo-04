# Tasks: Language Switching (English / Russian)

**Feature**: 004-language-switching
**Generated**: 2026-02-28
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Overview

- **Total tasks**: 22
- **User Stories**: US1 (P1), US2 (P2), US3 (P1), US4 (P2)
- **Phases**: 7 (Setup → Foundational → US1 → US3 → US2 → US4 → Polish)
- **Parallel opportunities**: 6 tasks across Phase 4 (US3) can run simultaneously
- **New files**: 4 (`src/i18n/__init__.py`, `src/i18n/strings.py`, 2 test files)
- **Modified files**: ~24 (22 handler files + `src/bot/callback_map.py` + `src/bot/run.py`)
- **No migration needed**: `language_code` already exists on User model and DB

---

## Phase 1: Setup

> Project initialization — create the i18n package and translation infrastructure.

- [X] T001 Create `src/i18n/__init__.py` with `t()`, `get_lang()`, and `SUPPORTED_LANGUAGES` per contract in `specs/004-language-switching/contracts/translation-api.md`
- [X] T002 Create `src/i18n/strings.py` with key-first `STRINGS` dict structure and initial placeholder entries (at least `err_register_first`, `start_welcome_back`) in English

**Checkpoint**: `from src.i18n import t, get_lang, SUPPORTED_LANGUAGES` imports without error. `t("err_register_first", "en")` returns the English string.

---

## Phase 2: Foundational

> Blocking prerequisites — translation infrastructure must be tested before any handler modifications.

- [X] T003 Create `tests/unit/test_translator.py` with tests for: English lookup, Russian lookup, fallback to English for unknown lang, raw key fallback for missing key, interpolation with kwargs, graceful handling of missing kwargs, EN/RU key parity assertion, and placeholder parity assertion per `specs/004-language-switching/quickstart.md` Step 2

**Checkpoint**: `pytest tests/unit/test_translator.py` passes. Key parity test will initially fail (no RU strings yet) — mark it `@pytest.mark.xfail` until Phase 4 adds Russian translations. All other tests green.

---

## Phase 3: User Story 1 — Switch Language from Settings (P1)

> **Story goal**: Registered users can change their language via /settings in under 3 taps.
> **Independent test**: Open /settings → tap "🌐 Change Language" → choose "Русский" → confirmation appears in Russian → subsequent settings view is in Russian.

- [X] T004 [US1] Extract all hardcoded strings from `src/handlers/system/settings_handler.py` into `src/i18n/strings.py` with `settings_` prefix keys and replace with `t()` calls; add `from src.i18n import t, get_lang` and resolve `lang = get_lang(user)` at handler entry
- [X] T005 [US1] Add `change_language` callback handler (displays language selection keyboard with "English 🇬🇧" and "Русский 🇷🇺" buttons) and `set_language:{code}` callback handler (validates code, updates `user.language_code` via `user_repo.update()`, confirms in new language, re-renders settings) in `src/handlers/system/settings_handler.py`
- [X] T006 [US1] Register `change_language` and `set_language:` callback patterns in `src/bot/callback_map.py` pointing to the new handlers in `settings_handler.py`
- [X] T007 [P] [US1] Add Russian translations for all `settings_*` and `btn_*` keys (change language, toggle notifications, settings header, language confirmation) in `src/i18n/strings.py`
- [X] T008 [US1] Create `tests/unit/test_settings_language.py` with tests for: change_language callback shows language keyboard, set_language:ru updates user and confirms in Russian, set_language:en updates user and confirms in English, invalid language code is rejected, settings view renders in user's language

**Checkpoint**: US1 is independently testable. `pytest tests/unit/test_settings_language.py` passes. Manual test: /settings → Change Language → Русский → confirmation in Russian.

---

## Phase 4: User Story 3 — All Bot Flows in Selected Language (P1)

> **Story goal**: Every system-generated message, button, and label across all 22 handler files respects the user's `language_code`.
> **Independent test**: Set language to Russian → exercise /browse, /newdeal, /help, reserve flow, error triggers → all system text in Russian.

- [X] T009 [P] [US3] Extract strings from `src/handlers/system/start_handler.py` and `src/handlers/system/help_handler.py` into `src/i18n/strings.py` with `start_` and `help_` prefix keys; replace hardcoded text with `t()` calls
- [X] T010 [P] [US3] Extract strings from `src/handlers/discovery/browse_handler.py` and `src/handlers/discovery/list_offers_handler.py` into `src/i18n/strings.py` with `browse_` prefix keys; replace hardcoded text with `t()` calls
- [X] T011 [P] [US3] Extract strings from `src/handlers/purchasing/reserve_handler.py`, `src/handlers/purchasing/cancel_reservation_handler.py`, `src/handlers/purchasing/purchase_initiate_handler.py`, `src/handlers/purchasing/purchase_cancel_handler.py`, and `src/handlers/purchasing/purchase_webhook_handler.py` into `src/i18n/strings.py` with `reserve_` and `purchase_` prefix keys; replace hardcoded text with `t()` calls. Note: notification strings sent to counterparties must use `get_lang(recipient_user)` per FR-011
- [X] T012 [P] [US3] Extract strings from `src/handlers/offer_posting/create_offer_handler.py`, `src/handlers/offer_posting/business_registration_handler.py`, and `src/handlers/offer_posting/business_verify_handler.py` into `src/i18n/strings.py` with `offer_` and `reg_` prefix keys; replace hardcoded text with `t()` calls
- [X] T013 [P] [US3] Extract strings from `src/handlers/offer_management/edit_handler.py`, `src/handlers/offer_management/end_offer_handler.py`, `src/handlers/offer_management/list_offers_handler.py`, and `src/handlers/offer_management/pause_resume_handler.py` into `src/i18n/strings.py` with `offer_` prefix keys; replace hardcoded text with `t()` calls
- [X] T014 [P] [US3] Extract strings from `src/handlers/lifecycle/registration_handler.py`, `src/handlers/lifecycle/approval_handler.py`, `src/handlers/lifecycle/offer_edit_handler.py`, and `src/handlers/lifecycle/offer_pause_handler.py` into `src/i18n/strings.py` with `reg_`, `approval_`, and `notif_` prefix keys; replace hardcoded text with `t()` calls
- [X] T015 [US3] Add Russian translations for ALL extracted string keys in `src/i18n/strings.py`; ensure every key in STRINGS has both `"en"` and `"ru"` entries (~210 strings total)
- [X] T016 [US3] Remove `@pytest.mark.xfail` from key parity and placeholder parity tests in `tests/unit/test_translator.py`; run full test suite to validate EN/RU catalog completeness

**Checkpoint**: US3 is independently testable. `pytest tests/unit/test_translator.py` passes (all parity tests green). No hardcoded user-facing strings remain in any handler file. `grep -r "reply_text\|edit_message_text" src/handlers/` shows only `t()` calls for system text.

---

## Phase 5: User Story 2 — Default Language for New Users (P2)

> **Story goal**: New users see an inline language button on /start before registration, enabling immediate Russian switch.
> **Independent test**: /start as new user → welcome message in English with "🌐 Русский" button → tap button → welcome re-renders in Russian → registration proceeds in Russian.

- [X] T017 [US2] Add inline "🌐 Русский" button to the welcome message for new (unregistered) users in `src/handlers/system/start_handler.py`; button callback_data is `start_set_language:ru`
- [X] T018 [US2] Add `start_set_language:{code}` callback handler in `src/handlers/system/start_handler.py` that sets language preference (update user if registered, or store in `context.user_data["lang"]` for pending registration) and re-renders welcome message in selected language
- [X] T019 [US2] Register `start_set_language:` callback pattern in `src/bot/callback_map.py` pointing to the handler in `start_handler.py`

**Checkpoint**: US2 is independently testable. New user /start shows language button. Tapping "🌐 Русский" switches welcome to Russian. Proceeding with registration uses Russian prompts throughout.

---

## Phase 6: User Story 4 — User-Generated Content Unchanged (P2)

> **Story goal**: Offer titles, descriptions, and business names display as-is regardless of viewer's language.
> **Independent test**: Business posts offer with English title → Russian-language user views it → system labels in Russian, title/description in original English.

- [X] T020 [US4] Review and verify that `src/handlers/discovery/browse_handler.py` and `src/handlers/discovery/list_offers_handler.py` only apply `t()` to system labels (e.g., "Price:", "Available:", "Pick-up:") and NOT to user-generated fields (offer.title, offer.description, business.name); add inline comments marking user-content fields as intentionally untranslated

**Checkpoint**: US4 verified. Offer display code clearly separates translated labels from user-generated content. No `t()` wrapping on `offer.title`, `offer.description`, or `business.name`.

---

## Phase 7: Polish & Cross-Cutting Concerns

> Final integration testing and validation.

- [X] T021 Create `tests/integration/test_language_flow.py` with end-to-end tests: new user /start with language button, switch language via settings, verify settings persistence across sessions, verify notification language per recipient, verify fallback for missing translation key
- [X] T022 Run full validation: `pytest` (all tests green), `ruff check src/` (no lint errors), verify quickstart walkthrough from `specs/004-language-switching/quickstart.md` works end-to-end

**Checkpoint**: All tests pass. Lint clean. Feature is complete and ready for review.

---

## Dependencies

```
Phase 1 (Setup)
  └──▶ Phase 2 (Foundational)
         └──▶ Phase 3 (US1: Settings language switch)
                └──▶ Phase 4 (US3: All bot flows)
                       ├──▶ Phase 5 (US2: New user language button)
                       └──▶ Phase 6 (US4: UGC verification)
                              └──▶ Phase 7 (Polish)
```

### User Story Completion Order

1. **US1** (P1) — Must complete first: provides the language switching mechanism
2. **US3** (P1) — Must complete second: extracts all strings so the switch has effect across all flows
3. **US2** (P2) — Can start after US3 Phase 4 T009 completes (start_handler strings extracted)
4. **US4** (P2) — Can start after US3 extraction tasks complete (needs browse_handler migrated)

### Cross-Story Dependencies

| Task | Depends on | Reason |
|------|-----------|--------|
| T004–T008 (US1) | T001–T003 | i18n module and tests must exist |
| T009–T016 (US3) | T004 | Settings strings pattern established; follow same approach |
| T015 (Russian translations) | T009–T014 | All English strings must be extracted first |
| T017–T019 (US2) | T009 | start_handler.py must be migrated to t() first |
| T020 (US4) | T010 | browse/list handlers must be migrated to verify UGC separation |
| T021–T022 (Polish) | T004–T020 | All stories must be complete |

---

## Parallel Execution Examples

### Phase 4 (US3): String extraction — 6 tasks in parallel

All handler domains can be extracted simultaneously since each task modifies different handler files. The shared `src/i18n/strings.py` receives additive key entries (no conflicts).

```
T009  [system/start + help]         ──┐
T010  [discovery/browse + list]     ──┤
T011  [purchasing/5 handlers]       ──┼──▶ T015 (Russian translations)
T012  [offer_posting/3 handlers]    ──┤       └──▶ T016 (parity validation)
T013  [offer_management/4 handlers] ──┤
T014  [lifecycle/4 handlers]        ──┘
```

### Phase 3 (US1): Partial parallelism

After T004 completes, T005 and T007 can run in parallel (different files):

```
T004 (extract strings) ──┬──▶ T005 (callbacks in settings_handler.py) ──▶ T006 (register in callback_map.py)
                         └──▶ T007 (Russian translations in strings.py)
                                                                          └──▶ T008 (tests)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 (T004–T008)
4. **STOP and VALIDATE**: Language switching works in /settings with Russian settings text
5. This delivers: Russian-speaking users can switch language and see settings in Russian

### Incremental Delivery

1. Setup + Foundational → i18n infrastructure ready
2. US1 → Language switch works (settings only) → **MVP**
3. US3 → All flows translated → Full Russian experience
4. US2 → New user onboarding with language choice
5. US4 → Verified UGC separation
6. Each story adds value without breaking previous stories

### Estimated String Counts by Domain

| Domain | Handler files | Est. strings | Task |
|--------|--------------|-------------|------|
| system/settings | 1 | ~10 | T004 |
| system/start + help | 2 | ~20 | T009 |
| discovery | 2 | ~25 | T010 |
| purchasing | 5 | ~40 | T011 |
| offer_posting | 3 | ~45 | T012 |
| offer_management | 4 | ~30 | T013 |
| lifecycle | 4 | ~40 | T014 |
| **Total** | **21** | **~210** | — |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks within the same phase
- [US*] label maps each task to its user story for traceability
- `health.py` in system/ is excluded — it is a system health endpoint with no user-facing translatable strings
- `purchase_webhook_handler.py` may have minimal user-facing text (webhook responses are server-to-server); include it in T011 extraction pass and skip if no translatable strings found
- Notification strings (FR-011): when extracting purchasing/lifecycle handlers, ensure cross-party notifications use `get_lang(recipient_user)` not the current user's language
- Numeric formatting (FR-006a): use `"Label: {value}"` pattern (e.g., `"Portions: {count}"`) — no Russian plural forms
- Date/currency formatting (FR-006b): do NOT translate numeric/temporal formats; only translate surrounding labels
- Commit after each task or logical group; run `ruff check src/` after each handler migration
