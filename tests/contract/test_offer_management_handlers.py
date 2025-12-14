"""Contract tests for offer management handlers (Phase 5).

Validates myoffers, pause, resume, edit, and end handlers conform to
expected input/output contracts and error handling patterns.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID

from src.models.offer import OfferStatus
from src.models.user import UserRole


class MockUpdate:
    """Mock Telegram Update object."""
    
    def __init__(self, user_id=12345, has_message=True, callback_data=None):
        self.effective_user = Mock()
        self.effective_user.id = user_id
        self.effective_user.first_name = "TestUser"
        
        if has_message:
            self.message = Mock()
            self.message.reply_text = AsyncMock()
        else:
            self.message = None
        
        self.callback_query = Mock()
        self.callback_query.data = callback_data
        self.callback_query.answer = AsyncMock()
        self.callback_query.edit_message_text = AsyncMock()
        self.callback_query.message = Mock()


class MockContext:
    """Mock Telegram Context object."""
    
    def __init__(self):
        self.bot_data = {
            "business_repo": AsyncMock(),
            "offer_repo": AsyncMock(),
        }
        self.user_data = {}
        self.bot = Mock()


class MockUser:
    """Mock User model."""
    
    def __init__(self, user_id=1, role=UserRole.BUSINESS):
        self.id = user_id
        self.telegram_user_id = 12345
        self.role = role


class MockBusiness:
    """Mock Business model."""
    
    def __init__(self):
        self.id = uuid4()
        self.business_name = "Test Bakery"
        self.owner_id = 1


class MockOffer:
    """Mock Offer model."""
    
    def __init__(self, state=OfferStatus.ACTIVE):
        from datetime import datetime, timedelta
        self.id = uuid4()
        self.business_id = uuid4()
        self.title = "Test Offer"
        self.description = "Test description"
        self.price_per_unit = 5.00
        self.quantity_total = 10
        self.quantity_remaining = 5
        self.state = state
        self.is_expired = False
        self.available_for_reservation = state == OfferStatus.ACTIVE
        self.pickup_start_time = datetime.utcnow()
        self.pickup_end_time = datetime.utcnow() + timedelta(hours=3)


# Phase 5: Offer Management Tests

@pytest.mark.asyncio
async def test_myoffers_requires_user_registration():
    """Test /myoffers requires user to be registered."""
    from src.handlers.offer_management.list_offers_handler import myoffers_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock user repo returning None (not registered)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=None)
    context.bot_data["user_repo"] = user_repo_mock
    
    await myoffers_command(update, context)
    
    # Should prompt to register
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "register" in call_args.lower() or "/start" in call_args


@pytest.mark.asyncio
async def test_myoffers_requires_business_role():
    """Test /myoffers requires business role."""
    from src.handlers.offer_management.list_offers_handler import myoffers_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock customer user
    user = MockUser(role=UserRole.CUSTOMER)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=user)
    context.bot_data["user_repo"] = user_repo_mock
    
    await myoffers_command(update, context)
    
    # Should reject customer
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "business" in call_args.lower()


@pytest.mark.asyncio
async def test_myoffers_shows_empty_state():
    """Test /myoffers shows helpful message when no offers exist."""
    from src.handlers.offer_management.list_offers_handler import myoffers_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock business user with no offers
    user = MockUser(role=UserRole.BUSINESS)
    business = MockBusiness()
    
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=user)
    
    business_repo_mock = AsyncMock()
    business_repo_mock.get_by_owner_id = AsyncMock(return_value=[business])
    
    offer_repo_mock = AsyncMock()
    offer_repo_mock.get_by_business_id = AsyncMock(return_value=[])
    
    context.bot_data["user_repo"] = user_repo_mock
    context.bot_data["business_repo"] = business_repo_mock
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await myoffers_command(update, context)
    
    # Should show empty state with /newdeal suggestion
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "/newdeal" in call_args


@pytest.mark.asyncio
async def test_pause_offer_validates_state():
    """Test pause offer validates offer is ACTIVE."""
    from src.handlers.offer_management.pause_resume_handler import handle_pause_offer
    
    offer_id = uuid4()
    update = MockUpdate(has_message=False, callback_data=f"pause_offer:{offer_id}")
    context = MockContext()
    
    # Mock paused offer (invalid state for pause)
    offer = MockOffer(state=OfferStatus.PAUSED)
    offer.id = offer_id
    
    offer_repo_mock = AsyncMock()
    offer_repo_mock.get_by_id = AsyncMock(return_value=offer)
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_pause_offer(update, context)
    
    # Should reject with error
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "Cannot pause" in call_args or "PAUSED" in call_args


@pytest.mark.asyncio
async def test_resume_offer_checks_expiration():
    """Test resume offer checks if offer is expired."""
    from src.handlers.offer_management.pause_resume_handler import handle_resume_offer
    
    offer_id = uuid4()
    update = MockUpdate(has_message=False, callback_data=f"resume_offer:{offer_id}")
    context = MockContext()
    
    # Mock expired offer
    offer = MockOffer(state=OfferStatus.PAUSED)
    offer.id = offer_id
    offer.is_expired = True
    
    offer_repo_mock = AsyncMock()
    offer_repo_mock.get_by_id = AsyncMock(return_value=offer)
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_resume_offer(update, context)
    
    # Should reject expired offer
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "expired" in call_args.lower() or "Cannot resume" in call_args


@pytest.mark.asyncio
async def test_end_offer_shows_confirmation():
    """Test end offer shows confirmation prompt."""
    from src.handlers.offer_management.end_offer_handler import handle_end_offer
    
    offer_id = uuid4()
    update = MockUpdate(has_message=False, callback_data=f"end_offer:{offer_id}")
    context = MockContext()
    
    # Mock active offer
    offer = MockOffer(state=OfferStatus.ACTIVE)
    offer.id = offer_id
    
    offer_repo_mock = AsyncMock()
    offer_repo_mock.get_by_id = AsyncMock(return_value=offer)
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_end_offer(update, context)
    
    # Should show confirmation with buttons
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args
    
    # Check text has confirmation prompt
    text = call_args[0][0]
    assert "End" in text and "cannot be undone" in text.lower()
    
    # Check has reply markup with buttons
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio
async def test_confirm_end_transitions_to_expired_early():
    """Test confirming end transitions offer to EXPIRED_EARLY."""
    from src.handlers.offer_management.end_offer_handler import handle_confirm_end
    
    offer_id = uuid4()
    update = MockUpdate(has_message=False, callback_data=f"confirm_end:{offer_id}")
    context = MockContext()
    
    # Mock active offer
    offer = MockOffer(state=OfferStatus.ACTIVE)
    offer.id = offer_id
    
    updated_offer = MockOffer(state=OfferStatus.EXPIRED_EARLY)
    updated_offer.id = offer_id
    
    offer_repo_mock = AsyncMock()
    offer_repo_mock.get_by_id = AsyncMock(return_value=offer)
    offer_repo_mock.update_state = AsyncMock(return_value=updated_offer)
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_confirm_end(update, context)
    
    # Should update to EXPIRED_EARLY
    offer_repo_mock.update_state.assert_called_once_with(offer_id, OfferStatus.EXPIRED_EARLY)
    
    # Should show success message
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "ended" in call_args.lower()


@pytest.mark.asyncio
async def test_error_messages_follow_pattern():
    """Test error messages follow [emoji] [problem] [action] pattern."""
    from src.handlers import format_error_message
    
    # Test format function
    error = format_error_message("❌", "Offer not found", "Try /browse for other offers")
    
    assert "❌" in error
    assert "Offer not found" in error
    assert "Try /browse for other offers" in error
    assert "\n\n" in error  # Should have proper spacing


@pytest.mark.asyncio
async def test_error_templates_available():
    """Test error templates are available."""
    from src.handlers import ERROR_TEMPLATES
    
    # Check required templates exist
    assert "not_registered" in ERROR_TEMPLATES
    assert "permission_denied" in ERROR_TEMPLATES
    assert "rate_limit" in ERROR_TEMPLATES
    assert "offer_expired" in ERROR_TEMPLATES
    assert "offer_not_found" in ERROR_TEMPLATES
    
    # Test they can be called
    error = ERROR_TEMPLATES["not_registered"]()
    assert "❌" in error
    assert "/start" in error
