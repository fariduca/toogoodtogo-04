# toogoodtogo Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-30

## Active Technologies
- Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+ (002-ux-flow-implementation)
- PostgreSQL (persistent: businesses, offers, reservations), Redis (ephemeral: rate limiting, reservation locks) (002-ux-flow-implementation)
- Python 3.12+ (pinned in pyproject.toml) + python-telegram-bot 21.7, pydantic 2.9.2, pydantic-settings 2.6.1, SQLAlchemy 2.0.36, structlog 24.4.0, redis 5.2.0 (004-language-switching)
- PostgreSQL (via asyncpg 0.30.0, psycopg2-binary 2.9.11; Alembic 1.14.0 for migrations). `language_code` column already exists on `users` table. (004-language-switching)

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
- 004-language-switching: Added Python 3.12+ (pinned in pyproject.toml) + python-telegram-bot 21.7, pydantic 2.9.2, pydantic-settings 2.6.1, SQLAlchemy 2.0.36, structlog 24.4.0, redis 5.2.0
- 002-ux-flow-implementation: Added Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+
- 002-ux-flow-implementation: Added Python 3.12+ + python-telegram-bot v21+, pydantic v2.9+, SQLAlchemy 2.0+, structlog v24.4+


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
