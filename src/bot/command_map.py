"""Command routing configuration for bot handlers.

Registers all command and conversation handlers with the bot application.
"""

from telegram.ext import Application

from src.bot.callback_map import register_callback_handlers
from src.handlers.discovery.list_offers_handler import get_discovery_handlers
from src.handlers.lifecycle.offer_pause_handler import (
    get_pause_handler,
    get_resume_handler,
)
from src.handlers.lifecycle.offer_edit_handler import get_edit_handler
from src.handlers.offer_posting.business_registration_handler import (
    get_registration_handler,
)
from src.handlers.offer_posting.business_verify_handler import (
    get_verification_handlers,
)
from src.handlers.offer_posting.offer_draft_handler import get_offer_draft_handler
from src.handlers.offer_posting.offer_publish_handler import get_publish_handler
from src.handlers.purchasing.purchase_cancel_handler import get_cancellation_handler
from src.handlers.system.start_handler import (
    get_default_message_handler,
    get_start_handler,
)
from src.logging import get_logger

logger = get_logger(__name__)


def register_handlers(app: Application) -> None:
    """
    Register all command and conversation handlers with the application.

    Args:
        app: Telegram bot Application instance
    """
    # Business registration flow (conversation)
    # System handlers - startup and fallback for plain text
    app.add_handler(get_start_handler())
    logger.info("handler_registered", handler="start")
    app.add_handler(get_default_message_handler())
    logger.info("handler_registered", handler="default_message")

    app.add_handler(get_registration_handler())
    logger.info("handler_registered", handler="registration_conversation")

    # Business verification commands (admin only)
    for handler in get_verification_handlers():
        app.add_handler(handler)
    logger.info("handler_registered", handler="business_verification")

    # Offer creation flow (conversation)
    app.add_handler(get_offer_draft_handler())
    logger.info("handler_registered", handler="offer_draft_conversation")

    # Offer publish command
    app.add_handler(get_publish_handler())
    logger.info("handler_registered", handler="offer_publish")

    # Discovery handlers (Phase 4)
    for handler in get_discovery_handlers():
        app.add_handler(handler)
    logger.info("handler_registered", handler="discovery")

    # Purchase cancellation
    app.add_handler(get_cancellation_handler())
    logger.info("handler_registered", handler="purchase_cancel")

    # Lifecycle management handlers (Phase 5)
    app.add_handler(get_pause_handler())
    logger.info("handler_registered", handler="offer_pause")

    app.add_handler(get_resume_handler())
    logger.info("handler_registered", handler="offer_resume")

    app.add_handler(get_edit_handler())
    logger.info("handler_registered", handler="offer_edit")

    # Callback query handlers for inline buttons
    register_callback_handlers(app)
    logger.info("handler_registered", handler="callbacks")

    logger.info("all_handlers_registered", total=10)
