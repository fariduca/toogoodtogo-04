# [PROJECT_NAME] Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Event-Driven Minimal Core
The bot core ONLY routes and normalizes incoming Telegram updates (messages, commands, callbacks) into internal events. All feature logic lives in isolated, testable handler modules ("plugins"). Each plugin:
- Declares its command(s)/trigger(s) and required permissions.
- Has zero implicit shared state (explicit dependency injection only).
- Exposes a pure function interface for business logic (IO abstracted so it can be unit tested without Telegram network calls).
No "misc" catch‑all modules allowed; every handler has a documented purpose.

### II. Test-First & Contracted Handlers (NON-NEGOTIABLE)
Before implementing a new handler or command:
1. Define its contract: expected update shape, normalized input DTO, output action(s) (reply text, edit, file send, etc.).
2. Write failing unit tests (mock Telegram client) + one integration test if it touches shared services (DB/cache).
3. Implement to make tests green; then refactor for clarity.
Every regression must add/adjust tests first. Red-Green-Refactor is enforced for all feature code. Handlers without tests cannot merge.

### III. Secure & Privacy-Conscious Interaction
Minimize data retention: do not persist raw message content unless strictly required. Secrets (bot token, API keys) come from environment variables only; never committed. Apply per-user + global rate limiting on sensitive/admin commands. Explicit role/permission checks precede any privileged action. PII scrubbed from logs; structured logging (JSON) for machine parsing while preserving trace IDs. Security patches and dependency updates treated as priority work.

### IV. Reserved for Future Expansion
Will be ratified when scaling requires cross-service coordination (e.g., sharding, multi-bot orchestration).

### V. Simplicity & Explicitness
Prefer a small, clear plugin list over complex meta-routing. YAGNI: no feature ships without at least one real user scenario and test coverage. Breaking changes to handler contracts require version bump + migration notes.

## Technical & Security Constraints

Python: 3.12+ (pinned in runtime config). Primary framework: `python-telegram-bot` (v21+ pinned via `requirements.txt`). Async usage preferred; blocking calls isolated.
Code Quality: ruff (lint) + mypy (strict optional) + pytest (unit/integration). Minimum test coverage target: 80% lines, 100% for handler normalization functions.
Configuration: `.env` for local only; production uses environment variables via deployment platform. No secrets in code or Git history.
Logging: Structured (JSON) via `structlog` or standard library with adapters; include correlation IDs per update.
Storage: Prefer ephemeral/cache (Redis) for rate limiting; persistent DB only when necessary (PostgreSQL recommended). Migrations managed with Alembic if DB introduced.
Performance: Average command handler latency < 300ms (excluding external API calls). External API interactions must implement timeouts and retries with exponential backoff.
Security: OWASP awareness; dependency scanning in CI (pip-audit). Regular token rotation schedule (at least quarterly).

## Development Workflow & Quality Gates

Branching: `main` (stable), feature branches `feat/<short-name>`, fixes `fix/<issue-id>`.
Pull Requests: Must reference issue/user story; include test additions; CI must be green (lint, type, tests, coverage threshold) before review.
CI Stages: (1) Install & cache deps; (2) Ruff & mypy; (3) Pytest w/ coverage; (4) Security scan (`pip-audit`); (5) Build artifact (Docker image) on tag.
Versioning: Semantic Versioning (MAJOR.MINOR.PATCH). MAJOR requires migration doc + CHANGELOG entry + governance approval. MINOR adds non-breaking features. PATCH for fixes/security.
Release: Tag `vX.Y.Z` triggers container build & push; changelog auto-generated from conventional commits.
Observability: Health command `/health` returns version, uptime, dependency status. Error monitoring via Sentry (if configured).
Breaking Changes: Announce in README and CHANGELOG; provide deprecation window when feasible.

## Governance
This constitution supersedes informal conventions. Any amendment requires:
1. Written proposal (Problem, Change, Impact, Migration Plan).
2. Review by at least two maintainers.
3. Version bump if contracts or workflows change materially.
Compliance: Each PR reviewer confirms adherence to Principles I–III and active sections. Complexity must be justified with documented user need or performance benefit. Emergency security fixes may bypass standard flow but must add tests within 48h.
Guidance: Use `RUNTIME_GUIDE.md` (to be added) for operational runbook (deploy, rotate tokens, troubleshoot).

**Version**: 1.0.0 | **Ratified**: 2025-11-13 | **Last Amended**: 2025-11-13
<!-- Initial ratification -->
