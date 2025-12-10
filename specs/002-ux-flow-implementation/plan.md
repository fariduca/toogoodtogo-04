# Implementation Plan: Telegram Marketplace Bot UX Flow Implementation

**Branch**: `002-ux-flow-implementation` | **Date**: 2025-11-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-ux-flow-implementation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement comprehensive UX flows for a Telegram marketplace bot enabling businesses to post excess-produce deals and customers to discover and reserve them for on-site payment. The implementation uses Telegram's native features (commands, reply keyboards, inline keyboards, menu button, deep linking) without external payment integration. Core flows include business onboarding with admin approval, offer posting and lifecycle management, customer discovery with geolocation filtering, reservation flow with immediate inventory decrement, and cancellation support. The system must handle real-time inventory updates, prevent overselling through atomic reservations, auto-expire offers, and provide structured logging for observability.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+  
**Storage**: PostgreSQL (persistent: businesses, offers, reservations), Redis (ephemeral: rate limiting, reservation locks)  
**Testing**: pytest with pytest-asyncio, pytest-cov (80% coverage target), pytest-mock for unit tests  
**Target Platform**: Linux server (async Python runtime), deployed via Docker  
**Project Type**: Single backend service (Telegram bot application)  
**Performance Goals**: <300ms handler latency, <2s offer state updates, 1-minute expiration checks  
**Constraints**: 99.9% uptime during operating hours, <0.1% overselling rate  
**Scale/Scope**: Initial single-market deployment, 30 functional requirements across 5 user stories, 10 success criteria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Event-Driven Minimal Core
✅ **PASS** - The bot core routes Telegram updates (commands, callbacks, messages) to isolated handler modules organized by feature area (business onboarding, offer posting, customer discovery, purchasing, lifecycle management). Each handler declares its commands and has explicit dependencies via dependency injection.

### Principle II: Test-First & Contracted Handlers
✅ **PASS** - Implementation will follow TDD: define handler contracts (input DTOs, output actions), write failing tests, implement to pass. Target 80% coverage with 100% for normalization functions. Contract tests will validate Telegram update handling, integration tests will verify DB/cache interactions.

### Principle III: Secure & Privacy-Conscious Interaction
✅ **PASS** - Minimal data retention (no raw message content stored), secrets from environment variables only, rate limiting on all commands, explicit permission checks for business/admin actions, and PII scrubbed from structured logs. The on-site payment model avoids handling sensitive payment data.

### Technical & Security Constraints
✅ **PASS** - Python 3.12+, python-telegram-bot v21+, async handlers, ruff + mypy + pytest, structured logging via structlog, PostgreSQL + Alembic migrations, Redis for ephemeral data, <300ms handler latency target, dependency scanning (pip-audit), token rotation schedule.

### Development Workflow & Quality Gates
✅ **PASS** - Feature branch `002-ux-flow-implementation`, PR will include tests and reference spec, CI runs lint/type/test/coverage/security before merge, semantic versioning for releases, health endpoint for observability.

**Overall Gate Status**: ✅ **PASS** - All constitution principles and constraints are satisfied. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/002-ux-flow-implementation/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (will be generated)
├── data-model.md        # Phase 1 output (will be generated)
├── quickstart.md        # Phase 1 output (will be generated)
├── contracts/           # Phase 1 output (will be generated)
│   ├── handlers.yaml    # Handler contracts (commands, callbacks, inputs, outputs)
│   └── events.yaml      # Internal event contracts for state transitions
├── checklists/          # Quality validation
│   └── requirements.md  # Completed requirements checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── bot/
│   ├── run.py                    # Bot entry point (existing)
│   ├── command_map.py            # Command routing (existing)
│   ├── callback_map.py           # Callback query routing (existing)
│   └── __init__.py
├── handlers/
│   ├── __init__.py
│   ├── system/                   # Global commands (/start, /help, /settings)
│   │   ├── start_handler.py
│   │   ├── help_handler.py
│   │   └── settings_handler.py
│   ├── lifecycle/                # Business registration & approval (existing structure)
│   │   ├── registration_handler.py
│   │   └── approval_handler.py
│   ├── offer_posting/            # Business offer creation (existing structure)
│   │   ├── new_offer_handler.py
│   │   ├── offer_edit_handler.py
│   │   └── offer_summary_handler.py
│   ├── discovery/                # Customer browse & search (existing structure)
│   │   ├── browse_handler.py
│   │   ├── filter_handler.py
│   │   └── offer_detail_handler.py
│   ├── purchasing/               # Customer purchase flow (existing structure)
│   │   ├── reservation_handler.py
│   │   ├── payment_handler.py
│   │   ├── confirmation_handler.py
│   │   └── my_purchases_handler.py
│   └── management/               # Business offer lifecycle (NEW)
│       ├── myoffers_handler.py
│       ├── pause_resume_handler.py
│       ├── edit_handler.py
│       └── end_offer_handler.py
├── models/                       # Domain models (existing)
│   ├── business.py
│   ├── offer.py
│   ├── purchase.py
│   ├── venue.py
│   └── __init__.py
├── services/                     # Business logic services (existing + new)
│   ├── stripe_checkout.py       # Telegram Payments + Stripe integration
│   ├── inventory_reservation.py # Atomic reservation logic
│   ├── expiration_job.py        # Scheduled expiration checks (1-minute interval)
│   ├── discovery_ranking.py     # Geolocation filtering (5km radius)
│   ├── payment_config.py        # Payment provider configuration
│   ├── offer_validation.py      # Offer field validation
│   ├── purchase_flow.py         # Purchase state machine
│   ├── sold_out_transition.py   # Zero-inventory state management
│   ├── scheduler.py             # Background job orchestration
│   ├── image_processing.py      # Photo upload handling
│   └── __init__.py
├── storage/                      # Data access layer (existing)
│   ├── database.py              # SQLAlchemy session management
│   ├── db_models.py             # ORM models
│   ├── postgres_business_repo.py
│   ├── postgres_offer_repo.py
│   ├── postgres_purchase_repo.py
│   ├── redis_locks.py           # Distributed locks for reservations
│   ├── repository_base.py
│   ├── image_store.py           # Cloud storage integration (S3/Cloudflare R2)
│   └── __init__.py
├── security/                     # Security & permissions (existing)
│   ├── permissions.py           # Role-based access control
│   ├── rate_limit.py            # Redis-backed rate limiting
│   └── __init__.py
├── logging/                      # Observability (existing)
│   ├── audit.py                 # Structured event logging (FR-030)
│   └── __init__.py
├── config/                       # Configuration (existing)
│   ├── settings.py              # Environment-based config
│   └── __init__.py
└── __init__.py

tests/
├── contract/                     # Handler contract tests
│   ├── test_lifecycle_handlers.py
│   ├── test_offer_posting_handlers.py
│   ├── test_purchase_handlers.py
│   ├── test_management_handlers.py  # NEW
│   └── test_openapi_schema.py
├── integration/                  # DB + Redis integration tests
│   ├── test_db_bootstrap.py
│   ├── test_offer_repository.py
│   ├── test_expiration_job.py
│   ├── test_purchase_race_condition.py
│   ├── test_purchase_success_flow.py
│   ├── test_offer_publish_flow.py
│   ├── test_offer_edit_flow.py
│   ├── test_offer_pause_flow.py
│   └── test_geolocation_filtering.py  # NEW
└── unit/                         # Pure business logic tests
    ├── test_offer_model.py
    ├── test_purchase_model.py
    ├── test_inventory_reservation.py
    ├── test_discovery_ranking.py
    ├── test_sold_out_transition.py
    ├── test_cancellation_policy.py
    └── test_reservation_timeout.py  # NEW

scripts/                          # Operational scripts
├── alembic/                     # DB migrations
└── backup_db.ps1

alembic/                         # Migration management
├── versions/                    # Migration files
└── env.py
```

**Structure Decision**: Single project structure (Option 1 from template) selected because this is a backend-only Telegram bot application. All features are implemented as isolated handler modules following the constitution's event-driven plugin architecture. The existing structure from `001-telegram-marketplace` is preserved and extended with new management handlers for offer lifecycle operations.

## Complexity Tracking

> **No violations to justify** - All requirements align with constitution principles and existing patterns.

---

## Phase 1 Complete ✓

All Phase 1 deliverables have been created:

### Research Artifacts (Phase 0)
- ✅ **research.md** (899 lines)
  - On-site payment model (no payment integration)
  - Geolocation filtering (Mapbox API + Haversine formula for 5km radius)
  - Redis-based reservation system (SETNX with 300-second TTL)
  - Image storage (Azure Blob Storage with SAS tokens)
  - Background scheduler (custom asyncio loop for 1-minute expiration checks)
  - **Critical finding**: Bug identified in redis_locks.py (5s vs 300s TTL)

### Design Artifacts (Phase 1)
- ✅ **data-model.md** (4 core entities)
  - User entity with role tracking and location permissions
  - Business entity with verification workflow and geocoding
  - Offer entity with 5-state machine (ACTIVE/PAUSED/EXPIRED/SOLD_OUT)
  - Reservation entity with state management for on-site pickup
  - Complete validation rules and Alembic migration requirements

- ✅ **contracts/handlers.yaml** (15+ handlers)
  - Global commands: /start, /help, /settings
  - Business handlers: /register_business, /newdeal, /myoffers
  - Customer handlers: /browse, offer details, reservation flow, /my_reservations
  - (No webhook handlers for payments)
  - Full specifications for inputs, outputs, state transitions, error responses

- ✅ **contracts/events.yaml** (30+ event types)
  - Business lifecycle events (registered, approved, rejected)
  - Offer lifecycle events (created, published, paused, resumed, expired, sold_out)
  - Reservation flow events (created, confirmed, cancelled, fulfilled)
  - Inventory management events (reserved, released, sold)
  - Error domain events (reservation failures, race conditions, job failures)
  - Security events (permission denied, rate limit exceeded)

- ✅ **quickstart.md** (comprehensive developer guide)
  - Prerequisites and required accounts (Telegram, Mapbox, Azure)
  - Installation steps and dependency management
  - Configuration with complete .env template
  - Database setup with Alembic migrations
  - Running the bot in development mode
  - Testing workflows (unit, integration, contract tests)
  - Common issues and troubleshooting
  - Development workflow guidelines

- ✅ **Agent Context Updated**
  - Ran update-agent-context.ps1 successfully
  - Added Python 3.12+, python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+
  - Added PostgreSQL and Redis database details
  - Updated .github/copilot-instructions.md

---

## Phase 2: Task Breakdown

⏸️ **Phase 2 is not part of /speckit.plan**.  
Run `/speckit.tasks` to generate tasks.md after planning is complete.
