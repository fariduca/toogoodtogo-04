# Feature Specification: Language Switching (English / Russian)

**Feature Branch**: `004-language-switching`  
**Created**: 2026-02-28  
**Status**: Draft  
**Input**: User description: "I want a new feature in the application. It should be possible to switch the language of the application to Russian and English."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Switch Language from Settings (Priority: P1)

As any registered user (customer or business owner), I want to change the application language from English to Russian or vice versa through the settings menu, so that all bot messages, buttons, and prompts are displayed in my preferred language.

**Why this priority**: This is the core interaction that enables the entire feature. Without a way to select a language, no other localization functionality is usable. It delivers immediate value to Russian-speaking users who currently cannot use the bot comfortably.

**Independent Test**: Can be fully tested by opening /settings, tapping a language selection button, choosing Russian, and verifying that subsequent messages from the bot appear in Russian. Delivers the ability for Russian-speaking users to interact with the bot in their native language.

**Acceptance Scenarios**:

1. **Given** a registered user with language set to English, **When** the user opens /settings and selects "Change Language" then chooses "Русский", **Then** the bot confirms the change in Russian and all subsequent messages are displayed in Russian.
2. **Given** a registered user with language set to Russian, **When** the user opens /settings and selects the language change option then chooses "English", **Then** the bot confirms the change in English and all subsequent messages are displayed in English.
3. **Given** a registered user changes their language, **When** they close and reopen the bot at a later time, **Then** the bot continues to display messages in the previously selected language (the preference is persisted).

---

### User Story 2 - Default Language for New Users (Priority: P2)

As a new user starting the bot for the first time, I want the bot to begin in a sensible default language (English), so that I have a usable experience immediately and can switch to Russian if needed.

**Why this priority**: Ensures a smooth onboarding experience. New users must be able to understand the bot from the very first message and be aware that a Russian option exists.

**Independent Test**: Can be tested by initiating /start as a brand-new user and verifying that the welcome message is in English and includes a hint about language availability.

**Acceptance Scenarios**:

1. **Given** a new user who has never interacted with the bot, **When** they send /start, **Then** the welcome message is displayed in English (the default) and includes an inline button (e.g., "🌐 Русский") allowing immediate language switch before registration begins.
2. **Given** a new user who taps the "🌐 Русский" button on the welcome message, **When** the language switches, **Then** the registration flow proceeds entirely in Russian.
3. **Given** a new user who does not tap the language button, **When** they proceed with registration, **Then** the entire onboarding flow continues in English.

---

### User Story 3 - All Bot Flows in Selected Language (Priority: P1)

As a user who has selected Russian as their language, I want every bot interaction — browsing offers, creating offers, reserving, purchasing, notifications, error messages, and help text — to appear in Russian, so that I have a fully consistent experience.

**Why this priority**: Partial translation creates confusion and a poor experience. All user-facing text across every handler and flow must respect the user's language preference for the feature to be complete.

**Independent Test**: Can be tested by setting language to Russian and then exercising each major flow (browse, create offer, reserve, /help, /settings, error triggering) and verifying all text is in Russian.

**Acceptance Scenarios**:

1. **Given** a user with language set to Russian, **When** they use /browse to discover offers, **Then** all labels, buttons, result text, and pagination controls are in Russian.
2. **Given** a business user with language set to Russian, **When** they create a new offer via /newdeal, **Then** all prompts, validation messages, and confirmation text are in Russian.
3. **Given** a user with language set to Russian, **When** they encounter an error (e.g., rate limit, invalid input, expired offer), **Then** the error message is displayed in Russian.
4. **Given** a user with language set to Russian, **When** they use /help, **Then** the help text and command descriptions are in Russian.

---

### User Story 4 - User-Generated Content Remains Unchanged (Priority: P2)

As a user browsing offers, I want to see offer titles, descriptions, and business names in their original language (as entered by the business owner), while all system-generated text (labels, buttons, prompts) appears in my selected language.

**Why this priority**: User-generated content should not be auto-translated as this could introduce errors. The distinction between system text and user content must be clear.

**Independent Test**: Can be tested by having a business post an offer in English, then browsing it as a user with Russian selected, and confirming that system labels are in Russian while the offer title/description remain in English.

**Acceptance Scenarios**:

1. **Given** an offer created with an English title and description, **When** a Russian-language user views this offer, **Then** the system labels (e.g., "Price", "Available portions", "Pick-up time") appear in Russian but the offer title and description remain in English as entered.
2. **Given** a business user with Russian language preference, **When** they create an offer and type the title in Russian, **Then** the title is stored and displayed as-is to all users regardless of their language preference.

---

### Edge Cases

- What happens when a user's Telegram client language is neither English nor Russian? The bot defaults to English.
- What happens if a translation key is missing for a specific message in Russian? The system falls back to the English version of that message to avoid showing raw keys or blank text.
- What happens if a user switches language mid-conversation (e.g., during a multi-step offer creation)? The conversation continues in the newly selected language from the next message onward; already-sent messages are not retroactively changed.
- What happens when system notifications (e.g., reservation confirmations, expiration alerts) are sent asynchronously? They use the user's persisted language preference at the time the notification is sent.
- What happens if the user switches language very rapidly (toggling back and forth)? The system accepts the latest selection; no rate-limiting is needed for language changes specifically.

## Clarifications

### Session 2026-02-28

- Q: Should the system support Russian-specific plural forms (one/few/many) or use generic phrasing that avoids number-dependent word changes? → A: Use generic phrasing (e.g., "Portions: 3") to avoid Russian plural-form complexity.
- Q: Should cross-party notifications (e.g., reservation alerts sent to both customer and business) use each recipient's own language or a single language? → A: Each recipient receives the notification in their own preferred language.
- Q: Should language change events be logged for observability (user ID, old/new language)? → A: No specific logging; rely on general request logs only.
- Q: Should date/time and currency formatting change based on the user's language, or remain in a single consistent format? → A: Keep a single consistent format regardless of language; only translate labels.
- Q: Should the language option be presented as an inline button during the welcome message (before registration) or only mentioned after registration? → A: Show an inline language-switch button in the initial /start welcome message, before registration starts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support exactly two languages: English (`en`) and Russian (`ru`).
- **FR-002**: System MUST allow any registered user to change their language preference via the /settings menu.
- **FR-003**: System MUST present a clear language selection interface showing both available languages with their native names ("English", "Русский").
- **FR-004**: System MUST persist the user's language preference so it survives bot restarts and future sessions.
- **FR-005**: System MUST default to English for new users who have not explicitly selected a language.
- **FR-006**: System MUST display all system-generated text (menus, prompts, buttons, labels, error messages, help text, confirmations, and notifications) in the user's selected language.
- **FR-006a**: Translated strings that include numeric values MUST use label-colon-number formatting (e.g., "Portions: 3", "Порции: 3") rather than embedding numbers within grammatically inflected phrases, to avoid Russian plural-form complexity.
- **FR-006b**: Date/time and currency values MUST be displayed in a single consistent format regardless of the user's selected language. Only the surrounding labels are translated; numeric and temporal formatting does not change between English and Russian.
- **FR-007**: System MUST NOT translate user-generated content (offer titles, descriptions, business names, user messages). Only system-provided text is translated.
- **FR-008**: System MUST fall back to English if a translated string is missing for the selected language, ensuring no raw translation keys or blank messages are ever shown to users.
- **FR-009**: System MUST apply the language change immediately — all messages sent after the change use the new language.
- **FR-010**: System MUST confirm a successful language change with a message in the newly selected language.
- **FR-011**: System MUST use each recipient's own persisted language preference for asynchronous messages (notifications, alerts) sent outside of a direct conversation. When a single event triggers notifications to multiple parties (e.g., customer and business owner), each party receives the message in their own language.
- **FR-012**: System MUST cover all existing bot flows with translations: registration, browsing/discovery, offer creation, offer management, reservations, purchasing, settings, help, and system messages.

### Key Entities

- **User**: Existing entity. Has a `language_code` attribute (already present in the data model) representing the user's preferred display language. Valid values: `en`, `ru`. Default: `en`.
- **Translation Catalog**: A structured collection of all system-generated text strings, organized by language code, enabling lookup of the correct text variant for any given message and language.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can switch their language preference in under 10 seconds (3 taps or fewer: Settings → Change Language → Select language).
- **SC-002**: 100% of system-generated messages, buttons, and labels across all bot flows are displayed in the user's selected language.
- **SC-003**: Language preference persists across sessions — a user returning after any period sees the bot in their last selected language with no additional action needed.
- **SC-004**: When a translation is missing, 100% of affected messages fall back to English gracefully (no raw keys, no blank messages, no crashes).
- **SC-005**: Language switching does not increase average response time by more than 200 milliseconds compared to the current single-language experience.
- **SC-006**: Russian-speaking users can complete all core tasks (browse, reserve, purchase, create offer) entirely in Russian without encountering any English system text.

## Assumptions

- The existing `language_code` field on the User model and database schema is ready to use and does not require a data migration.
- English translations are simply the current hardcoded strings extracted into the translation catalog.
- Russian translations will be provided as part of the implementation (authored or reviewed by a Russian speaker).
- The bot targets a bilingual community where English and Russian are the two primary languages; no other languages are planned in the short term.
- Telegram's built-in `language_code` from the user's client is not used for automatic language detection — the user explicitly selects their preference.
- Adding additional languages in the future should be straightforward given the translation catalog structure, but is out of scope for this feature.
