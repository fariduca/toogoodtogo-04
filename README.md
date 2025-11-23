# Telegram Marketplace Bot

A Telegram bot marketplace for restaurants and shops to post excess produce deals and enable customers to discover and purchase them.

## Features

### ✅ Implemented (MVP Ready)

**Phase 1-2: Foundation**
- Project structure with Python 3.12
- PostgreSQL persistence + Alembic migrations
- Redis for distributed locks and rate limiting
- Structured logging with correlation IDs
- Domain models with Pydantic validation

**Phase 3: Business Posting**
- `/register` - Business registration with venue details and photos
- Admin verification workflow (`/pending`, `/verify`, `/reject`)
- `/newoffer` - Multi-step offer creation (title, items, pricing, time range)
- `/publish <offer_id>` - Publish draft offers to marketplace
- Image upload, resize, and validation
- Automatic offer expiration scheduler

**Phase 4: Customer Purchase (MVP)**
- `/offers` or `/browse` - View active offers with ranking
- Inline button navigation for offer details
- Cash-at-venue purchase flow (no online payment required)
- Inventory reservation with Redis distributed locks
- Overselling prevention
- `/cancel <purchase_id>` - Cancel purchase before pickup

**Phase 5: Lifecycle Management**
- `/pause <offer_id>` - Temporarily pause active offers
- `/resume <offer_id>` - Resume paused offers
- `/edit <offer_id>` - Edit offer prices and quantities
- Automatic sold-out transition when inventory depleted
- Manual force sold-out capability

### 🚧 Deferred (Post-MVP)
- Online payment via Stripe Checkout
- Geographic filtering and distance-based ranking
- Customer ratings and popularity scoring
- S3 image storage
- Performance optimizations

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Redis 7+
- Telegram Bot Token (from @BotFather)

### Installation

1. **Clone and navigate:**
```powershell
cd toogoodtogo
```

2. **Create virtual environment:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

4. **Configure environment:**
```powershell
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `BOT_TOKEN` - Your Telegram bot token
- `DATABASE_URL` - PostgreSQL connection string  
- `REDIS_URL` - Redis connection string
- `STRIPE_SECRET_KEY` - Stripe API key (optional for MVP)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)

5. **Run database migrations:**
```powershell
alembic upgrade head
```

6. **Start the bot:**
```powershell
python -m src.bot.run
```

Or use the convenience script:
```powershell
.\scripts\run_bot.ps1
```

## Commands

### For Customers
- `/offers` or `/browse` - View available offers
- `/cancel <purchase_id>` - Cancel a purchase

### For Businesses
- `/register` - Register business with venue details
- `/newoffer` - Create new offer (multi-step conversation)
- `/publish <offer_id>` - Publish draft offer to marketplace
- `/pause <offer_id>` - Temporarily pause an active offer
- `/resume <offer_id>` - Resume a paused offer
- `/edit <offer_id>` - Edit offer prices or quantities

### For Admins
- `/pending` - List pending business verifications
- `/verify <business_id>` - Approve business
- `/reject <business_id> <reason>` - Reject business

## Testing

Run all tests:
```powershell
pytest
```

Run with coverage:
```powershell
pytest --cov=src --cov-report=html
```

Lint code:
```powershell
ruff check .
```

Type checking:
```powershell
mypy src
```

## Architecture

**Event-driven core**: Minimal bot routing with isolated handler plugins  
**Repository pattern**: Clean separation between domain models and persistence  
**Distributed locking**: Redis-based locks prevent race conditions in inventory management  
**Cash-first MVP**: Simple cash-at-venue payments (Stripe integration ready for future)

## Project Structure

```
src/
  bot/                # Bot application and command routing
  handlers/           # Command and callback handlers
    offer_posting/    # Business registration, verification, offer creation
    discovery/        # Offer browsing and listing
    purchasing/       # Purchase flow and cancellation
  models/             # Pydantic domain models
  services/           # Business logic services
  storage/            # Repository implementations
  security/           # Permissions and rate limiting
  config/             # Configuration management
  logging/            # Structured logging setup

tests/
  unit/               # Unit tests
  integration/        # Integration tests  
  contract/           # OpenAPI contract tests
```

## Documentation

- [Feature Specification](specs/001-telegram-marketplace/spec.md)
- [Implementation Plan](specs/001-telegram-marketplace/plan.md)
- [Data Model](specs/001-telegram-marketplace/data-model.md)
- [API Contracts](specs/001-telegram-marketplace/contracts/openapi.yaml)
- [Tasks](specs/001-telegram-marketplace/tasks.md)

## Contributing

1. Follow test-first development approach
2. Use structured logging with correlation IDs
3. Run linters before committing: `ruff check .` and `mypy src`
4. Keep handlers thin - business logic belongs in services
5. Use distributed locks for all inventory operations

## Deployment

### Docker Deployment

1. **Build the image:**
```powershell
docker build -t telegram-marketplace:latest .
```

2. **Run with Docker Compose:**
```powershell
docker-compose up -d
```

3. **View logs:**
```powershell
docker-compose logs -f bot
```

### Environment Hardening

**Production Checklist:**

1. **Security:**
   - [ ] Enable HTTPS for all external connections
   - [ ] Use secrets management (Azure Key Vault, AWS Secrets Manager)
   - [ ] Never commit `.env` files or secrets to git
   - [ ] Enable rate limiting for all user-facing endpoints
   - [ ] Implement audit logging for critical actions
   - [ ] Use separate database users with minimal privileges

2. **Performance:**
   - [ ] Configure connection pooling for PostgreSQL (max 20 connections)
   - [ ] Set Redis maxmemory policy to `allkeys-lru`
   - [ ] Enable database query logging and monitor slow queries (>100ms)
   - [ ] Set up health checks on `/health` endpoint
   - [ ] Monitor memory usage (keep below 256MB per container)

3. **Reliability:**
   - [ ] Configure automatic restarts with exponential backoff
   - [ ] Set up database backups (daily snapshots, 7-day retention)
   - [ ] Enable structured logging with centralized aggregation
   - [ ] Implement circuit breakers for external services (Stripe, etc.)
   - [ ] Set up alerting for critical errors (>10 errors/minute)

4. **Monitoring:**
   - [ ] Track key metrics: offers_published, purchases_completed, errors_rate
   - [ ] Monitor Redis memory usage and eviction rate
   - [ ] Set up uptime monitoring (expected: 99.9% uptime)
   - [ ] Configure Sentry for error aggregation (post-MVP)

**Environment Variables for Production:**

```env
# Bot
BOT_TOKEN=<your_bot_token>
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50

# Security
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Optional integrations
STRIPE_SECRET_KEY=<your_stripe_key>
SENTRY_DSN=<your_sentry_dsn>
```

**Docker Resource Limits:**

```yaml
# docker-compose.yml example
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### Backup and Recovery

**Database Backup Script:**
```powershell
.\scripts\backup_db.ps1
```

Creates timestamped backup in `backups/` directory with automatic 7-day rotation.

**Recovery:**
```powershell
psql -U user -d dbname < backups/backup_2025-11-23.sql
```

## License

[Specify License]
