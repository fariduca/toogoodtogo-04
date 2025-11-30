"""Command routing configuration for bot handlers.

Registers all command and conversation handlers with the bot application.
"""

from telegram.ext import Application

from src.bot.callback_map import register_callback_handlers
from src.handlers.discovery.browse_handler import get_browse_handlers
from src.handlers.discovery.list_offers_handler import get_discovery_handlers
from src.handlers.lifecycle.approval_handler import get_approval_handlers
from src.handlers.lifecycle.offer_pause_handler import (
    get_pause_handler,
    get_resume_handler,
)
from src.handlers.lifecycle.offer_edit_handler import get_edit_handler
from src.handlers.lifecycle.registration_handler import (
    get_registration_conversation_handler,
)
from src.handlers.offer_posting.create_offer_handler import get_newdeal_handler
from src.handlers.offer_posting.business_registration_handler import (
    get_registration_handler,
)
from src.handlers.offer_posting.business_verify_handler import (
    get_verification_handlers,
)
from src.handlers.offer_posting.offer_draft_handler import get_offer_draft_handler
from src.handlers.offer_posting.offer_publish_handler import get_publish_handler
from src.handlers.purchasing.purchase_cancel_handler import get_cancellation_handler
from src.handlers.purchasing.reserve_handler import get_reservation_handlers
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
    # System handlers - startup and fallback
    app.add_handler(get_start_handler())
    logger.info("handler_registered", handler="start")
    
    # Registration conversation flow (Phase 2)
    app.add_handler(get_registration_conversation_handler())
    logger.info("handler_registered", handler="registration_conversation")
    
    # Admin approval handlers (Phase 2)
    for handler in get_approval_handlers():
        app.add_handler(handler)
    logger.info("handler_registered", handler="business_approval")
    
    # New deal creation (Phase 3)
    app.add_handler(get_newdeal_handler())
    logger.info("handler_registered", handler="newdeal_conversation")

    # Old business registration flow (to be deprecated)
    app.add_handler(get_registration_handler())
    logger.info("handler_registered", handler="old_registration_conversation")

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

    # Discovery & Browse handlers (Phase 4)
    for handler in get_browse_handlers():
        app.add_handler(handler)
    logger.info("handler_registered", handler="browse")
    
    # Reservation handlers (Phase 4)
    for handler in get_reservation_handlers():
        app.add_handler(handler)
    logger.info("handler_registered", handler="reservations")

    # Old discovery handlers
    for handler in get_discovery_handlers():
        app.add_handler(handler)
    logger.info("handler_registered", handler="old_discovery")

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
    
    # Default message handler (must be last)
    app.add_handler(get_default_message_handler())
    logger.info("handler_registered", handler="default_message")

    logger.info("all_handlers_registered")
