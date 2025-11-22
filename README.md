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

### 🚧 Deferred (Post-MVP)
- Online payment via Stripe Checkout
- Offer editing and pause functionality  
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

## License

[Specify License]
