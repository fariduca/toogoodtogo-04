# Quickstart: Telegram Marketplace Bot

## Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional)
- PostgreSQL 14+
- Redis 7+
- Stripe account (Checkout enabled)
- Telegram Bot Token (via @BotFather)

## Environment Variables
| Name | Description |
|------|-------------|
| BOT_TOKEN | Telegram bot token |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection URI |
| STRIPE_SECRET_KEY | Stripe API secret |
| STRIPE_PRICE_MAPPING | JSON mapping for price codes (optional) |
| LOG_LEVEL | Logging level (info/debug) |

## Local Development (Pure Python)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/bot/run.py
```

## Docker Build & Run
```powershell
# Build image
docker build -t telegram-marketplace:dev .
# Run (example with env file)
docker run --rm -p 8080:8080 --env-file .env telegram-marketplace:dev
```

## Database Bootstrap
```powershell
# Example using alembic (to be added when migrations exist)
alembic upgrade head
```

## Redis Usage
- Rate limiting & purchase locking use Redis keys prefixed `tmkt:`.
- TTL for locks: 5 seconds.

## Payment Flow
1. Customer chooses items.
2. Bot requests internal API purchase initiation.
3. Internal service creates Stripe Checkout session; returns checkout_url.
4. Bot sends URL; upon webhook confirmation, purchase status -> confirmed.

## Offer Lifecycle
- Scheduler task scans for expired offers every minute.
- Sold out determined when remaining quantity == 0.

## Testing
```powershell
pytest -q
```

## Next Steps
- Implement handlers incrementally: posting, publishing, purchasing, lifecycle.
- Add Sentry integration post-pilot if error volume justifies.
