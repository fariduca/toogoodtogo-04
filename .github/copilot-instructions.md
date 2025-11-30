# toogoodtogo Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-30

## Active Technologies
- Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+ (002-ux-flow-implementation)
- PostgreSQL (persistent: businesses, offers, reservations), Redis (ephemeral: rate limiting, reservation locks) (002-ux-flow-implementation)

- Python 3.12 + `python-telegram-bot` (v21+), `structlog`, `pydantic` (models/validation), optional `redis` (rate limiting / ephemeral locks) (001-telegram-marketplace)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 002-ux-flow-implementation: Added Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+
- 002-ux-flow-implementation: Added Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+
- 002-ux-flow-implementation: Added Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, Stripe SDK v11+, structlog v24.4+


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
