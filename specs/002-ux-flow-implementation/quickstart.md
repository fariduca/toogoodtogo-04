# Quickstart Guide

**Feature**: 002-ux-flow-implementation  
**Purpose**: Developer onboarding guide for UX flow implementation  
**Target Audience**: New developers joining the project

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Running the Bot](#running-the-bot)
6. [Testing](#testing)
7. [Development Workflow](#development-workflow)
8. [Common Issues](#common-issues)
9. [Next Steps](#next-steps)

---

## Prerequisites

Before starting, ensure you have:

### Required Software

- **Python 3.12+** (required per constitution)
  - Check: `python --version`
  - Install: Download from [python.org](https://www.python.org/downloads/)

- **PostgreSQL 14+** (database)
  - Check: `psql --version`
  - Install: [PostgreSQL Downloads](https://www.postgresql.org/download/)

- **Redis 5.2+** (ephemeral storage)
  - Check: `redis-cli --version`
  - Install: [Redis Downloads](https://redis.io/download) or Docker

- **Git** (version control)
  - Check: `git --version`

### Required Accounts & API Keys

1. **Telegram Bot Token**
   - Create bot via [@BotFather](https://t.me/botfather)
   - Commands: `/newbot` → follow prompts
   - Save token (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Mapbox Account**
   - Sign up at [mapbox.com](https://www.mapbox.com)
   - Create token: Account → Tokens → Create token
   - Scopes needed: Geocoding API access

3. **Azure Blob Storage** (for images)
   - Create Azure account at [portal.azure.com](https://portal.azure.com)
   - Create storage account → Containers → Create `offer-images` container
   - Get connection string: Storage account → Access keys

---

## Installation

### 1. Clone Repository

```powershell
git clone <repository-url>
cd toogoodtogo
```

### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Command Prompt)
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```powershell
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (testing, linting)
pip install pytest pytest-asyncio pytest-cov ruff black
```

### 4. Verify Installation

```powershell
# Check Python packages
pip list | Select-String -Pattern "telegram|sqlalchemy|redis|structlog"

# Expected output:
# python-telegram-bot    21.x
# sqlalchemy             2.x
# redis                  5.x
# structlog              24.4.x
```

---

## Configuration

### 1. Environment Variables

Create `.env` file in project root:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/toogoodtogo_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_LOCK_TIMEOUT=5  # 5 seconds for transactional locks

# Mapbox Configuration
MAPBOX_ACCESS_TOKEN=pk.eyJ1...

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=offer-images

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
NEARBY_RADIUS_KM=5  # Per FR-004 clarification

# Security Settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
```

### 2. Load Configuration

The bot automatically loads `.env` via `python-dotenv`:

```python
# In src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str
    database_url: str
    # ... other settings
    
    class Config:
        env_file = ".env"
```

---

## Database Setup

### 1. Create PostgreSQL Database

```powershell
# Connect to PostgreSQL
psql -U postgres

# In psql prompt:
CREATE DATABASE toogoodtogo_dev;
CREATE USER toogoodtogo WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE toogoodtogo_dev TO toogoodtogo;
\q
```

### 2. Run Alembic Migrations

```powershell
# Check current migration status
alembic current

# Run all migrations (creates tables)
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
# INFO  [alembic.runtime.migration] Running upgrade 001 -> 002_ux_flow_tables
```

### 3. Verify Database Schema

```powershell
# Connect to database
psql -U toogoodtogo -d toogoodtogo_dev

# List tables
\dt

# Expected tables:
# users
# businesses
# offers
# purchases
# alembic_version
```

### 4. Seed Test Data (Optional)

```powershell
# Run seed script (if exists)
python scripts/seed_test_data.py

# Creates:
# - 2 test businesses (one approved, one pending)
# - 5 test offers (various states)
# - 3 test purchases (confirmed)
```

---

## Running the Bot

### 1. Start Redis

```powershell
# Option 1: Native Redis
redis-server

# Option 2: Docker
docker run -d -p 6379:6379 redis:7-alpine

# Verify Redis running
redis-cli ping
# Expected: PONG
```

### 2. Start Bot (Development Mode)

```powershell
# Ensure virtual environment is active
.\venv\Scripts\Activate.ps1

# Run bot
python src/bot/run.py

# Expected output:
# 2025-11-30 10:00:00 [INFO] Bot starting...
# 2025-11-30 10:00:00 [INFO] Registered 15 handlers
# 2025-11-30 10:00:00 [INFO] Connected to PostgreSQL
# 2025-11-30 10:00:00 [INFO] Connected to Redis
# 2025-11-30 10:00:00 [INFO] Bot is running! Press Ctrl+C to stop.
```

### 3. Start Bot (PowerShell Script)

```powershell
# Use provided script (handles error recovery)
.\scripts\run_bot.ps1

# Script features:
# - Auto-activates virtual environment
# - Validates .env file
# - Restarts on crash (development mode)
# - Structured logging to console + file
```

### 4. Test Bot Connection

1. Open Telegram
2. Search for your bot (@YourBotName)
3. Send `/start` command
4. Expected response: Welcome message with role selection

---

## Testing

### 1. Run Unit Tests

```powershell
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_offer_model.py -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### 2. Run Integration Tests

```powershell
# Requires running PostgreSQL and Redis
pytest tests/integration/ -v

# Skip slow tests
pytest tests/integration/ -m "not slow"
```

### 3. Run Contract Tests

```powershell
# Verify handler contracts match spec
pytest tests/contract/ -v

# Test specific handler
pytest tests/contract/test_offer_posting_handlers.py -v
```

### 4. Run All Tests

```powershell
# Full test suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Target: 80% coverage per success criteria SC-009
```

### 5. Check Code Quality

```powershell
# Linting with Ruff
ruff check src/

# Fix auto-fixable issues
ruff check src/ --fix

# Format code with Black
black src/

# Type checking (if using mypy)
mypy src/
```

---

## Development Workflow

### 1. Feature Branch Strategy

```powershell
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Work on feature...

# Commit with conventional commits
git commit -m "feat: add offer pause functionality"
git commit -m "fix: resolve race condition in reservation"
git commit -m "test: add unit tests for inventory service"
```

### 2. Pre-Commit Checklist

Before committing code:

```powershell
# 1. Format code
black src/

# 2. Run linter
ruff check src/ --fix

# 3. Run tests
pytest tests/unit/ tests/integration/

# 4. Check coverage
pytest tests/ --cov=src --cov-report=term-missing

# 5. Verify no lint errors
ruff check src/
```

### 3. Database Migrations

When changing models:

```powershell
# Generate migration
alembic revision --autogenerate -m "Add cancellation_reason to purchases"

# Review generated migration in scripts/alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 4. Testing New Handlers

```powershell
# 1. Write handler tests first (TDD)
# Create tests/integration/test_your_feature.py

# 2. Implement handler
# Create/modify src/handlers/your_feature/

# 3. Register handler in callback/command map
# Edit src/bot/callback_map.py or command_map.py

# 4. Run tests
pytest tests/integration/test_your_feature.py -v

# 5. Test manually in Telegram
python src/bot/run.py
```

### 5. Debugging

```powershell
# Enable debug logging
$env:LOG_LEVEL="DEBUG"
python src/bot/run.py

# View structured logs
Get-Content logs/bot.log -Tail 50 | ConvertFrom-Json | Format-Table

# Connect to Redis and inspect keys
redis-cli
> KEYS reservation:*
> GET reservation:<purchase_id>
> TTL reservation:<purchase_id>

# Inspect database
psql -U toogoodtogo -d toogoodtogo_dev
SELECT * FROM offers WHERE state='ACTIVE' ORDER BY created_at DESC LIMIT 10;
```

---

## Common Issues

### Issue 1: Bot Won't Start - Invalid Token

**Symptoms**: `telegram.error.InvalidToken: Invalid token`

**Solution**:
```powershell
# Verify token format in .env
# Should be: TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Test token manually
curl -X GET "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### Issue 2: Database Connection Failed

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```powershell
# 1. Check PostgreSQL is running
Get-Process postgres

# 2. Verify DATABASE_URL in .env
# Format: postgresql://user:password@host:port/database

# 3. Test connection
psql -U toogoodtogo -d toogoodtogo_dev
```

### Issue 3: Redis Connection Error

**Symptoms**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution**:
```powershell
# 1. Check Redis is running
redis-cli ping

# 2. If not running, start Redis
redis-server

# 3. Verify REDIS_URL in .env (default: redis://localhost:6379/0)
```

### Issue 4: Alembic Migration Conflicts

**Symptoms**: `alembic.util.exc.CommandError: Multiple head revisions`

**Solution**:
```powershell
# View current heads
alembic heads

# Merge heads
alembic merge -m "merge heads" head_1 head_2

# Apply merged migration
alembic upgrade head
```

### Issue 5: Image Upload Fails (Azure Blob)

**Symptoms**: `azure.core.exceptions.ResourceNotFoundError`

**Solution**:
```powershell
# 1. Verify container exists in Azure Portal
# Storage Account → Containers → "offer-images"

# 2. Check connection string in .env
# Should include AccountName, AccountKey, and EndpointSuffix

# 3. Test connection with Azure CLI
az storage container list --connection-string $env:AZURE_STORAGE_CONNECTION_STRING
```

---

## Next Steps

After completing quickstart:

### For Feature Implementation

1. **Read Full Specification**
   - File: `specs/002-ux-flow-implementation/spec.md`
   - Review user stories, functional requirements, success criteria

2. **Study Data Model**
   - File: `specs/002-ux-flow-implementation/data-model.md`
   - Understand entities, relationships, state machines

3. **Review Handler Contracts**
   - File: `specs/002-ux-flow-implementation/contracts/handlers.yaml`
   - Learn input/output specifications for each handler

4. **Check Task Breakdown**
   - File: `specs/002-ux-flow-implementation/tasks.md` (when created)
   - Pick task from backlog and start coding

### For Testing

1. **Run Full Test Suite**
   ```powershell
   pytest tests/ -v --cov=src --cov-report=html
   open htmlcov/index.html
   ```

2. **Review Test Patterns**
   - File: `tests/conftest.py` (pytest fixtures)
   - Example: `tests/integration/test_offer_publish_flow.py`

3. **Write New Tests**
   - Follow existing patterns
   - Aim for 80%+ coverage per SC-009

### For Deployment

1. **Review Security Checklist**
   - File: `docs/security-checklist.md`
   - Ensure all items addressed before production

- **Set Up CI/CD Pipeline**
   - Configure GitHub Actions (or similar)
   - Run tests on every commit
   - Auto-deploy to staging environment

3. **Configure Production Environment**
   - Use environment-specific `.env` files
   - Set `ENVIRONMENT=production`

---

## Additional Resources

- **Project Documentation**: `README.md`, `MVP_SUMMARY.md`, `REMAINING_WORK.md`
- **Database Management**: `DATABASE_SETUP.md`
- **Security Guidelines**: `docs/security-checklist.md`
- **Telegram Bot API**: [core.telegram.org/bots/api](https://core.telegram.org/bots/api)
- **python-telegram-bot Docs**: [docs.python-telegram-bot.org](https://docs.python-telegram-bot.org/)
- **SQLAlchemy 2.0**: [docs.sqlalchemy.org](https://docs.sqlalchemy.org/)

---

## Getting Help

- **Issues**: Check `REMAINING_WORK.md` for known issues
- **Questions**: Review handler contracts and data model first
- **Bugs**: Check logs in `logs/` directory with structured format
- **Community**: (Add team Slack/Discord link if applicable)

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-30  
**Maintainer**: Development Team
