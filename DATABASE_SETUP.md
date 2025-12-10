# Database Setup Guide

## Current Issue
Alembic cannot connect to PostgreSQL because the database server is not running.

**Error:** `connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused`

## Solutions

### ✅ Option 1: Docker (RECOMMENDED - Easiest)

1. **Install Docker Desktop**
   - Download: https://www.docker.com/products/docker-desktop/
   - Install and restart your computer
   - Verify installation:
     ```powershell
     docker --version
     ```

2. **Start Database Services**
   ```powershell
   docker compose up -d
   ```

3. **Verify Services are Running**
   ```powershell
   docker compose ps
   ```

4. **Run Migrations**
   ```powershell
   alembic upgrade head
   ```

5. **Stop Services (when done)**
   ```powershell
   docker compose down
   ```

---

### Option 2: PostgreSQL Local Installation

1. **Download PostgreSQL**
   - Visit: https://www.postgresql.org/download/windows/
   - Download the installer (version 16 recommended)

2. **Install with These Settings**
   - Username: `toogoodtogo`
   - Password: `devpassword`
   - Port: `5432`
   - Create database: `telegram_marketplace`

3. **Verify Installation**
   ```powershell
   Get-Service -Name "postgresql*"
   ```

4. **Run Migrations**
   ```powershell
   alembic upgrade head
   ```

---

### Option 3: Skip Migrations for Now

If you want to test without a database, you can:

1. **Mock the database in tests** (already configured in test fixtures)
2. **Use in-memory repositories** for development
3. **Come back to database setup later**

Note: The bot handlers will need a working database to function properly.

---

## After Database is Running

Once PostgreSQL is running (either via Docker or local install):

```powershell
# Apply all migrations
alembic upgrade head

# Verify tables were created
# (Connect with pgAdmin or psql)

# Run integration tests
pytest tests/integration/

# Start the bot
python -m src.bot.run
```

## Quick Status Check

Check if PostgreSQL is running:
```powershell
# Test connection
Test-NetConnection -ComputerName localhost -Port 5432
```

## Database Credentials (from .env)

```
DATABASE_URL=postgresql://toogoodtogo:devpassword@localhost:5432/telegram_marketplace
```

## Next Steps

1. Choose one of the setup options above
2. Start the database service
3. Run `alembic upgrade head` to create tables
4. Test with `pytest tests/integration/test_db_bootstrap.py`
