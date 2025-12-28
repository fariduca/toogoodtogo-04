"""Contract tests for global command handlers (Phase 7).

Validates /help, /settings, and deep linking functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from src.models.user import UserRole


class MockUpdate:
    """Mock Telegram Update object."""
    
    def __init__(self, user_id=12345, has_message=True, callback_data=None, start_args=None):
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


class MockContext:
    """Mock Telegram Context object."""
    
    def __init__(self, args=None):
        self.args = args or []
        self.bot_data = {}
        self.user_data = {}
        self.bot = Mock()


class MockUser:
    """Mock User model."""
    
    def __init__(self, user_id=1, role=UserRole.CUSTOMER, notifications=True):
        self.id = user_id
        self.telegram_user_id = 12345
        self.role = role
        self.notification_enabled = notifications
        self.language_code = "en"


# Phase 7: Global Commands Tests

@pytest.mark.asyncio
async def test_help_shows_general_for_unregistered():
    """Test /help shows general help for unregistered users."""
    from src.handlers.system.help_handler import help_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock no user (not registered)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=None)
    context.bot_data["user_repo"] = user_repo_mock
    
    await help_command(update, context)
    
    # Should show general help
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Help" in call_args
    assert "/start" in call_args


@pytest.mark.asyncio
async def test_help_shows_business_commands_for_business():
    """Test /help shows business-specific commands for business users."""
    from src.handlers.system.help_handler import help_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock business user
    user = MockUser(role=UserRole.BUSINESS)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=user)
    context.bot_data["user_repo"] = user_repo_mock
    
    await help_command(update, context)
    
    # Should show business commands
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "/newdeal" in call_args
    assert "/myoffers" in call_args
    assert "business" in call_args.lower()


@pytest.mark.asyncio
async def test_help_shows_customer_commands_for_customer():
    """Test /help shows customer-specific commands for customers."""
    from src.handlers.system.help_handler import help_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock customer user
    user = MockUser(role=UserRole.CUSTOMER)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=user)
    context.bot_data["user_repo"] = user_repo_mock
    
    await help_command(update, context)
    
    # Should show customer commands
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "/browse" in call_args
    assert "/myreservations" in call_args
    assert "customer" in call_args.lower()


@pytest.mark.asyncio
async def test_settings_requires_registration():
    """Test /settings requires user to be registered."""
    from src.handlers.system.settings_handler import settings_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock no user
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=None)
    context.bot_data["user_repo"] = user_repo_mock
    
    await settings_command(update, context)
    
    # Should prompt to register
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "/start" in call_args


@pytest.mark.asyncio
async def test_settings_shows_current_preferences():
    """Test /settings displays current user preferences."""
    from src.handlers.system.settings_handler import settings_command
    
    update = MockUpdate()
    context = MockContext()
    
    # Mock user with notifications enabled
    user = MockUser(notifications=True)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=user)
    context.bot_data["user_repo"] = user_repo_mock
    
    await settings_command(update, context)
    
    # Should show settings
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    
    text = call_args[0][0]
    assert "Settings" in text
    assert "Notifications" in text
    assert "Enabled" in text
    
    # Should have inline keyboard
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio
async def test_toggle_notifications_changes_setting():
    """Test toggle notifications callback updates user preference."""
    from src.handlers.system.settings_handler import handle_toggle_notifications
    
    user_id = 1
    update = MockUpdate(has_message=False, callback_data=f"toggle_notifications:{user_id}")
    context = MockContext()
    
    # Mock user with notifications enabled
    user = MockUser(user_id=user_id, notifications=True)
    updated_user = MockUser(user_id=user_id, notifications=False)
    
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_id = AsyncMock(return_value=user)
    user_repo_mock.update = AsyncMock(return_value=updated_user)
    context.bot_data["user_repo"] = user_repo_mock
    
    await handle_toggle_notifications(update, context)
    
    # Should update user
    user_repo_mock.update.assert_called_once()
    
    # Should show updated settings
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "Disabled" in call_args


@pytest.mark.asyncio
async def test_deep_link_offer_shows_view_button():
    """Test deep link for offer shows offer view button."""
    from src.handlers.system.start_handler import start_command
    
    offer_id = uuid4()
    update = MockUpdate()
    context = MockContext(args=[f"offer_{offer_id}"])
    
    # Mock user repo
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=None)
    context.bot_data["user_repo"] = user_repo_mock
    
    await start_command(update, context)
    
    # Should send message with button to view offer
    assert update.message.reply_text.call_count >= 1
    
    # Check one of the messages has the offer link
    calls = update.message.reply_text.call_args_list
    has_button = any("reply_markup" in call[1] for call in calls if len(call) > 1)
    assert has_button


@pytest.mark.asyncio
async def test_deep_link_business_invite_shows_coming_soon():
    """Test deep link for business invite shows placeholder message."""
    from src.handlers.system.start_handler import start_command
    
    update = MockUpdate()
    context = MockContext(args=["business_invite_ABC123"])
    
    # Mock user repo
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=None)
    context.bot_data["user_repo"] = user_repo_mock
    
    await start_command(update, context)
    
    # Should show coming soon message
    update.message.reply_text.assert_called()
    calls = update.message.reply_text.call_args_list
    messages = [call[0][0] for call in calls]
    
    # Check at least one message mentions invitation
    has_invite_msg = any("invitation" in msg.lower() or "coming soon" in msg.lower() for msg in messages)
    assert has_invite_msg


@pytest.mark.asyncio
async def test_start_shows_role_selection_for_new_users():
    """Test /start shows role selection for new users (no deep link)."""
    from src.handlers.system.start_handler import start_command
    
    update = MockUpdate()
    context = MockContext(args=[])  # No deep link args
    
    # Mock no user
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=None)
    context.bot_data["user_repo"] = user_repo_mock
    
    await start_command(update, context)
    
    # Should show role selection
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    
    text = call_args[0][0]
    assert "Welcome" in text
    assert "role" in text.lower()
    
    # Should have reply keyboard
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio
async def test_start_shows_welcome_back_for_existing_users():
    """Test /start shows welcome back for existing users."""
    from src.handlers.system.start_handler import start_command
    
    update = MockUpdate()
    context = MockContext(args=[])
    
    # Mock existing user
    user = MockUser(role=UserRole.CUSTOMER)
    user_repo_mock = AsyncMock()
    user_repo_mock.get_by_telegram_id = AsyncMock(return_value=user)
    context.bot_data["user_repo"] = user_repo_mock
    
    await start_command(update, context)
    
    # Should show welcome back with commands
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Welcome back" in call_args
    assert "/browse" in call_args
