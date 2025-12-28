"""Telegram bot startup and main application entry point."""

import asyncio
import os
import ssl
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Disable SSL verification for development (Windows SSL issues)
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'
ssl._create_default_https_context = ssl._create_unverified_context

from telegram.ext import Application

from src.bot.command_map import register_handlers
from src.config import load_settings
from src.logging import get_logger, setup_logging
from src.security.permissions import PermissionChecker
from src.security.rate_limit import RateLimiter
from src.services.discovery_ranking import DiscoveryRankingService
from src.services.expiration_job import ExpirationJob
from src.services.reservation_flow import ReservationFlowService
from src.services.scheduler import SchedulerService
from src.storage.database import Database
from src.storage.postgres_business_repo import PostgresBusinessRepository
from src.storage.postgres_offer_repo import PostgresOfferRepository
from src.storage.postgres_reservation_repo import PostgresReservationRepository
from src.storage.postgres_user_repo import PostgresUserRepository
from src.storage.redis_locks import RedisLockHelper


async def setup_bot_menu(application: Application) -> None:
    """Configure role-appropriate bot menu commands."""
    from telegram import BotCommand
    
    # Set default commands for all users
    # Note: Telegram doesn't support dynamic per-user menus, so we set a general menu
    # that includes both business and customer commands
    commands = [
        BotCommand("start", "Start or restart the bot"),
        BotCommand("help", "Show help and commands"),
        BotCommand("browse", "Browse available deals"),
        BotCommand("myreservations", "View your reservations"),
        BotCommand("newdeal", "Post a new deal (businesses only)"),
        BotCommand("myoffers", "Manage your offers (businesses only)"),
        BotCommand("settings", "Manage your settings"),
    ]
    
    await application.bot.set_my_commands(commands)
    
    logger = get_logger(__name__)
    logger.info("bot_menu_configured", command_count=len(commands))


async def main() -> None:
    """Initialize and start the Telegram bot."""
    settings = load_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)

    logger.info("Starting Telegram Marketplace Bot", environment=settings.environment)

    # Initialize database
    db = Database(settings)
    await db.connect()

    async with db.session() as session:
        # Initialize repositories
        user_repo = PostgresUserRepository(session)
        business_repo = PostgresBusinessRepository(session)
        offer_repo = PostgresOfferRepository(session)
        reservation_repo = PostgresReservationRepository(session)

    # Initialize Redis-backed services
    redis_locks = RedisLockHelper(settings.redis_url, ttl_seconds=settings.redis_lock_ttl_seconds)
    rate_limiter = RateLimiter(
        settings.redis_url,
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    await rate_limiter.connect()

    # Initialize security services
    permission_checker = PermissionChecker(admin_user_ids=settings.admin_user_ids)
    
    # Initialize discovery service
    discovery_service = DiscoveryRankingService(nearby_radius_km=settings.nearby_radius_km)
    
    # Initialize reservation flow service
    reservation_flow_service = ReservationFlowService(offer_repo, reservation_repo, redis_locks)

    # Initialize background scheduler
    scheduler = SchedulerService(offer_repo, interval_seconds=settings.expiration_check_interval_seconds)

    # Build application
    application = Application.builder().token(settings.bot_token).build()

    # Store services in bot_data for handler access
    application.bot_data["db"] = db
    application.bot_data["user_repo"] = user_repo
    application.bot_data["business_repo"] = business_repo
    application.bot_data["offer_repo"] = offer_repo
    application.bot_data["reservation_repo"] = reservation_repo
    application.bot_data["redis_locks"] = redis_locks
    application.bot_data["permission_checker"] = permission_checker
    application.bot_data["rate_limiter"] = rate_limiter
    application.bot_data["discovery_service"] = discovery_service
    application.bot_data["reservation_flow_service"] = reservation_flow_service
    application.bot_data["settings"] = settings

    # Register handlers
    register_handlers(application)
    
    # Configure bot menu
    await setup_bot_menu(application)

    logger.info("Bot initialization complete, starting polling")

    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=["message", "callback_query"])

    # Start background scheduler
    scheduler_task = asyncio.create_task(scheduler.start())

    # Run until stopped
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down bot")
    finally:
        await scheduler.stop()
        scheduler_task.cancel()
        await rate_limiter.disconnect()
        await db.disconnect()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
