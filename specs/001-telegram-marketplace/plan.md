# Implementation Plan: Telegram Marketplace for Excess Produce Deals

**Branch**: `001-telegram-marketplace` | **Date**: 2025-11-13 | **Spec**: `specs/001-telegram-marketplace/spec.md`
**Input**: Feature specification from `/specs/001-telegram-marketplace/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enable restaurants and shops to publish time-bound excess produce offers and allow customers to discover and purchase them via a Telegram bot. Architectural approach: event-driven minimal core routing Telegram updates to isolated plugin-style handlers; external Stripe Checkout for payment; atomic inventory reservation to prevent overselling; simple discovery (latest + popular) in MVP; Dockerized Python 3.12 service with structured logging and test-first development.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12
**Primary Dependencies**: `python-telegram-bot` (v21+), Stripe Checkout external link, `structlog`, `pydantic` (models/validation), optional `redis` (rate limiting / ephemeral locks)
**Storage**: PostgreSQL (offers, businesses, purchases); Redis (rate limit + inventory reservation locks); Local filesystem (temp image caching) – NEEDS CLARIFICATION: CDN usage later
**Testing**: pytest (unit/integration), mypy (strict), ruff (lint), contract tests for handler normalization
**Target Platform**: Linux container (Docker) running on standard x86_64 host
**Project Type**: Single service (library-first, plugin handlers)
**Performance Goals**: Publish offer < 2 min; handler median latency < 300ms; overselling incidents ≤ 0.1%
**Constraints**: p95 handler latency < 500ms; memory < 256MB/container; cold start < 5s; image size < 200MB
**Scale/Scope**: MVP: 100 businesses, 5k customers, 2k daily purchases; design for linear scale to 10x without refactor

**Outstanding Clarifications (to resolve in Phase 0)**:
- CDN/image hosting strategy for business pictures (Local vs S3-like) – NEEDS CLARIFICATION
- Discovery ranking beyond latest/popular (geo proximity vs category weighting) – NEEDS CLARIFICATION
- Observability enhancement (Sentry adoption vs logging-only) – NEEDS CLARIFICATION

## Constitution Check (Pre-Research Gate)

Principle I (Event-Driven Minimal Core): Plan uses core router + plugin handlers (PASS)
Principle II (Test-First & Contracted Handlers): Test stack defined; contract tests planned (PASS)
Principle III (Secure & Privacy-Conscious): External payment, minimal retention; structured logging w/out PII (PASS)
Principle V (Simplicity & Explicitness): Single service, clear modules (PASS)

Gate Result: PASS — proceed to Phase 0. No violations needing complexity tracking.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
  bot/                # Telegram update dispatcher & startup
  handlers/           # Feature plugins (offer_posting, purchasing, discovery, lifecycle)
  models/             # Pydantic domain models (Business, Offer, Purchase)
  services/           # Stripe checkout link generator, discovery ranking service
  storage/            # Repos/DB adapters (Postgres), cache (Redis), image storage abstraction
  security/           # Rate limiting, permission checks
  logging/            # Structured logging config
  config/             # Settings loading

tests/
  unit/               # Pure function & model validation tests
  integration/        # DB, redis, payment link, handler end-to-end
  contract/           # Handler input/output normalization, OpenAPI schema validation

contracts/            # Generated OpenAPI spec (Phase 1)
scripts/              # Utility scripts (DB migration, seed)
Dockerfile            # Container build (to be added later)
```

**Structure Decision**: Single service with library-style modular directories; no premature microservices; aligns with simplicity principle.

## Complexity Tracking

No violations; table omitted.

## Phase 0 Plan

For each outstanding clarification create research tasks. Output consolidated into `research.md`.

Research Tasks:
1. Image Hosting Strategy (local disk vs object storage/CDN)
2. Discovery Ranking Extension (geo proximity vs engagement-based)
3. Observability Enhancement (Sentry vs logging-only)

Each task will yield Decision, Rationale, Alternatives.

## Phase 1 Plan

Prerequisite: `research.md` resolves all clarifications.
Artifacts:
- `data-model.md` — Entities, fields, validations, state transitions
- `contracts/openapi.yaml` — Internal REST endpoints for admin/business ops & purchase flow
- `quickstart.md` — Docker build/run, env configuration, local bootstrap (DB + Redis)
- Update agent context with new technologies using update-agent-context script.

## Phase 2 (Not executed here)
Will derive task breakdown from finalized plan & design.

## Post-Design Constitution Re-evaluation

Artifacts generated (research.md, data-model.md, contracts/openapi.yaml, quickstart.md) reinforce principles:
- Principle I: Handlers isolated; data-model defines pure domain objects (PASS)
- Principle II: Testing strategy documented in quickstart (pytest, contract tests) (PASS)
- Principle III: External payment + clarified cancellation (no PII in logs) (PASS)
- Principle V: Single service, no premature microservices (PASS)

No new complexity introduced. Ready for Phase 2 task breakdown.
