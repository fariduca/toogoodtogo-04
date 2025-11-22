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


async def main() -> None:
    """Initialize and start the Telegram bot."""
    settings = load_settings()
    setup_logging(settings.log_level)
    logger = get_logger(__name__)

    logger.info("Starting Telegram Marketplace Bot", environment=settings.environment)

    # Build application
    application = Application.builder().token(settings.bot_token).build()

    # Register handlers
    register_handlers(application)

    logger.info("Bot initialization complete, starting polling")

    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=["message", "callback_query"])

    # Run until stopped
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down bot")
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
