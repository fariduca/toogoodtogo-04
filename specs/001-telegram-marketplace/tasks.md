# Tasks: Telegram Marketplace for Excess Produce Deals

Date: 2025-11-13
Branch: 001-telegram-marketplace
Spec: specs/001-telegram-marketplace/spec.md
Plan: specs/001-telegram-marketplace/plan.md

## Overview
Tasks organized by phases to support independent delivery of each user story. Each task uses required checklist format:
`- [ ] T### [P] [USn] Description with file path`.

## Phase 1: Setup (Project Initialization)
- [x] T001 Initialize repository structure per plan (create `src/`, `tests/`, `contracts/`, `scripts/`)  
- [x] T002 Add Python project scaffolding (`pyproject.toml` or `requirements.txt`) in repo root  
- [x] T003 Create `requirements.txt` with pinned versions (python-telegram-bot, structlog, pydantic, redis, psycopg2-binary, stripe, alembic)  
- [x] T004 Create base config loader `src/config/settings.py`  
- [x] T005 [P] Draft Dockerfile for Python 3.12 slim image at `Dockerfile`  
- [x] T006 [P] Add `src/logging/__init__.py` with structured logging setup (structlog config)  
- [x] T007 Add `.env.example` enumerating required environment variables  
- [x] T008 [P] Create initial Alembic migration setup in `scripts/alembic/`  
- [x] T009 Add pre-commit config `.pre-commit-config.yaml` for ruff + mypy checks  
- [x] T010 Create test harness `tests/conftest.py` for fixtures (db, redis, stripe mock)  
- [x] T011 Add `scripts/run_bot.ps1` convenience launcher  
- [x] T012 [P] Implement `src/bot/run.py` basic startup (load settings, set up updater/dispatcher)  
- [x] T013 Add `README.md` with high-level feature intro and quickstart pointer  

## Phase 2: Foundational (Blocking Prerequisites)
- [x] T014 Implement domain models (Pydantic) `src/models/business.py`  
- [x] T015 [P] Implement domain models `src/models/venue.py`  
- [x] T016 [P] Implement domain models `src/models/offer.py` (Offer + Item nested)  
- [x] T017 [P] Implement domain models `src/models/purchase.py` (Purchase + PurchaseItem)  
- [x] T018 Implement repository interface `src/storage/repository_base.py`  
- [x] T019 Implement Postgres repositories `src/storage/postgres_business_repo.py`  
- [x] T020 [P] Implement Postgres repositories `src/storage/postgres_offer_repo.py`  
- [x] T021 [P] Implement Postgres repositories `src/storage/postgres_purchase_repo.py`  
- [x] T022 Implement Redis lock helper `src/storage/redis_locks.py`  
- [x] T023 [P] Implement image storage abstraction `src/storage/image_store.py`  
- [x] T024 Implement rate limiter `src/security/rate_limit.py`  
- [x] T025 [P] Implement permission checks `src/security/permissions.py`  
- [x] T026 Add mapping config for Stripe `src/services/payment_config.py`  
- [x] T027 [P] Implement Stripe checkout session service `src/services/stripe_checkout.py`  
- [x] T028 Implement discovery ranking service (latest + popularity) `src/services/discovery_ranking.py`  
- [x] T029 Implement scheduler stub for lifecycle `src/services/scheduler.py`  
- [x] T030 Add integration test DB bootstrap `tests/integration/test_db_bootstrap.py`  
- [x] T031 [P] Add model validation tests `tests/unit/test_offer_model.py`  
- [x] T032 [P] Add model validation tests `tests/unit/test_purchase_model.py`  
- [x] T033 Add repository tests `tests/integration/test_offer_repository.py`  
- [x] T034 [P] Add stripe service test `tests/unit/test_stripe_checkout.py`  
- [x] T035 Add discovery ranking test `tests/unit/test_discovery_ranking.py`  
- [x] T036 Implement OpenAPI contract loader validator `tests/contract/test_openapi_schema.py`  

## Phase 3: User Story 1 – Business posts a deal (P1)
- [x] T037 [US1] Implement business registration handler `src/handlers/offer_posting/business_registration_handler.py`  
- [x] T038 [P] [US1] Implement business verification admin command handler `src/handlers/offer_posting/business_verify_handler.py`  
- [x] T039 [US1] Implement offer draft creation handler `src/handlers/offer_posting/offer_draft_handler.py`  
- [x] T040 [P] [US1] Implement publish offer handler `src/handlers/offer_posting/offer_publish_handler.py`  
- [x] T041 [US1] Add image upload + resize workflow `src/services/image_processing.py`  
- [x] T042 [US1] Implement offer validation utilities `src/services/offer_validation.py`  
- [x] T043 [US1] Add command routing entries `src/bot/command_map.py` for /newoffer /publish  
- [x] T044 [US1] Contract tests for handlers `tests/contract/test_offer_posting_handlers.py`  
- [x] T045 [US1] Integration test: create & publish offer `tests/integration/test_offer_publish_flow.py`  
- [x] T046 [US1] Implement expiration scheduler effect (mark expired) `src/services/expiration_job.py`  
- [x] T047 [US1] Test expiration scheduler `tests/integration/test_expiration_job.py`  

Independent Test Criterion: A newly registered & verified business can create and publish an offer; test passes if published offer appears in list endpoint.

## Phase 4: User Story 2 – Customer views and purchases a deal (P1)
- [x] T048 [US2] Implement offers listing handler `src/handlers/discovery/list_offers_handler.py`  
- [x] T049 [P] [US2] Implement purchase initiation handler `src/handlers/purchasing/purchase_initiate_handler.py`  
- [x] T050 [US2] Implement purchase confirmation webhook processing `src/handlers/purchasing/purchase_webhook_handler.py`  
- [x] T051 [US2] Implement cancellation handler `src/handlers/purchasing/purchase_cancel_handler.py`  
- [x] T052 [US2] Implement inventory reservation logic `src/services/inventory_reservation.py`  
- [x] T053 [US2] Add overselling prevention lock usage `src/services/purchase_flow.py`  
- [x] T054 [US2] Add command/button mapping for purchase actions `src/bot/callback_map.py`  
- [x] T055 [US2] Contract tests purchasing handlers `tests/contract/test_purchase_handlers.py`  
- [x] T056 [US2] Integration test successful purchase `tests/integration/test_purchase_success_flow.py`  
- [ ] T057 [US2] Integration test oversell attempt race condition `tests/integration/test_purchase_race_condition.py`  
- [ ] T058 [US2] Unit test inventory reservation `tests/unit/test_inventory_reservation.py`  
- [ ] T059 [US2] Unit test cancellation logic `tests/unit/test_cancellation_policy.py`  

Independent Test Criterion: Customer can list offers, initiate purchase, complete payment, and receive confirmation with updated remaining quantity reflected.

## Phase 5: User Story 3 – Offer lifecycle management (P2)
- [ ] T060 [US3] Implement pause offer handler `src/handlers/lifecycle/offer_pause_handler.py`  
- [ ] T061 [P] [US3] Implement edit offer handler (price/quantity change) `src/handlers/lifecycle/offer_edit_handler.py`  
- [ ] T062 [US3] Implement sold-out state transition logic `src/services/sold_out_transition.py`  
- [ ] T063 [US3] Integration test pause behavior `tests/integration/test_offer_pause_flow.py`  
- [ ] T064 [US3] Integration test edit update impacts discovery listing `tests/integration/test_offer_edit_flow.py`  
- [ ] T065 [US3] Unit test sold-out transition `tests/unit/test_sold_out_transition.py`  
- [ ] T066 [US3] Contract test lifecycle handlers `tests/contract/test_lifecycle_handlers.py`  
- [ ] T067 [US3] Update command routing `/pause` `/edit` in `src/bot/command_map.py`  

Independent Test Criterion: Business can pause, edit, and force sold-out transitions; customer view updates immediately and purchasing is blocked accordingly.

## Final Phase: Polish & Cross-Cutting
- [ ] T068 Add structured audit logging for key actions `src/logging/audit.py`  
- [ ] T069 [P] Add ruff/mypy CI pipeline config `.github/workflows/ci.yml`  
- [ ] T070 Add performance smoke test `tests/integration/test_performance_smoke.py`  
- [ ] T071 Add Sentry integration toggle `src/logging/sentry_integration.py`  
- [ ] T072 [P] Add README section for deployment & env hardening `README.md`  
- [ ] T073 Add security review checklist `docs/security-checklist.md`  
- [ ] T074 [P] Optimize Docker image (multi-stage) `Dockerfile`  
- [ ] T075 Add backup & migration script `scripts/backup_db.ps1`  
- [ ] T076 Final constitution compliance verification `specs/001-telegram-marketplace/tasks.md`  

## Dependency Graph (Stories)
US1 (posting) → US2 (purchase) → US3 (lifecycle)
Rationale: Purchase needs published offers; lifecycle edits depend on purchase & posting flows existing.

## Parallel Execution Examples
During Foundational Phase:
- T015, T016, T017 (models) in parallel
- T020, T021 (repos) in parallel after T018
- T027 (stripe), T028 (discovery), T023 (image store) parallel

Story Phases:
- US1: T038 & T040 can parallelize after T037 skeleton exists.
- US2: T049 & T050 parallel after listing (T048) in place.
- US3: T061 parallel with T060 after pause handler base ready.

## Implementation Strategy
MVP Scope: Complete Phase 3 (US1) + minimal subset of Phase 4 (listing + purchase initiation + confirmation T048–T056) to enable end-to-end posting and buying.
Incremental Delivery:
1. Setup + Foundational core (Phases 1–2)
2. US1 publish flow (Phase 3)
3. Basic purchasing (subset Phase 4 up to confirmation)
4. Full purchasing robustness (race condition, cancellation)
5. Lifecycle management (Phase 5)
6. Polish & hardening.

## Task Counts
- Total Tasks: 76
- Setup: 13
- Foundational: 23
- US1: 11
- US2: 12
- US3: 8
- Polish: 9

## Independent Test Criteria Summary
- US1: Publish path yields visible active offer.
- US2: Purchase path updates inventory & returns confirmation.
- US3: Lifecycle operations reflect in customer view & block actions.

## Format Validation
All tasks follow required format with IDs, optional [P], and story labels only where appropriate.
