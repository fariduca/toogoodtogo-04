"""Contract tests for lifecycle management handlers.

Validates that pause, resume, and edit handlers conform to
expected input/output contracts and error handling patterns.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# Mock Telegram types
class MockUpdate:
    def __init__(self, user_id=12345, command_args=None, has_message=True):
        self.effective_user = Mock()
        self.effective_user.id = user_id
        
        if has_message:
            self.message = Mock()
            self.message.reply_text = AsyncMock()
        else:
            self.message = None
        
        self.callback_query = Mock()
        self.callback_query.answer = AsyncMock()
        self.callback_query.edit_message_text = AsyncMock()


class MockContext:
    def __init__(self, args=None):
        self.args = args or []
        self.bot_data = {}
        self.user_data = {}
        self.bot = Mock()


@pytest.mark.asyncio
async def test_pause_handler_requires_offer_id():
    """Test pause handler requires offer_id argument."""
    from src.handlers.lifecycle.offer_pause_handler import pause_offer
    
    # Setup: No arguments
    update = MockUpdate(command_args=[])
    context = MockContext(args=[])
    
    # Execute
    await pause_offer(update, context)
    
    # Verify: Should send usage message
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Usage:" in call_args
    assert "/pause" in call_args


@pytest.mark.asyncio
async def test_pause_handler_validates_uuid_format():
    """Test pause handler validates UUID format."""
    from src.handlers.lifecycle.offer_pause_handler import pause_offer
    
    # Setup: Invalid UUID
    invalid_uuid = "not-a-uuid"
    update = MockUpdate(command_args=[invalid_uuid])
    context = MockContext(args=[invalid_uuid])
    
    # Execute
    await pause_offer(update, context)
    
    # Verify: Should send error message about invalid format
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Invalid offer ID format" in call_args or "invalid" in call_args.lower()


@pytest.mark.asyncio
async def test_resume_handler_requires_offer_id():
    """Test resume handler requires offer_id argument."""
    from src.handlers.lifecycle.offer_pause_handler import resume_offer
    
    # Setup: No arguments
    update = MockUpdate(command_args=[])
    context = MockContext(args=[])
    
    # Execute
    await resume_offer(update, context)
    
    # Verify: Should send usage message
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Usage:" in call_args
    assert "/resume" in call_args


@pytest.mark.asyncio
async def test_edit_handler_requires_offer_id():
    """Test edit handler requires offer_id argument."""
    from src.handlers.lifecycle.offer_edit_handler import start_edit
    from telegram.ext import ConversationHandler
    
    # Setup: No arguments
    update = MockUpdate(command_args=[])
    context = MockContext(args=[])
    
    # Execute
    result = await start_edit(update, context)
    
    # Verify: Should end conversation and send usage message
    assert result == ConversationHandler.END
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Usage:" in call_args
    assert "/edit" in call_args


@pytest.mark.asyncio
async def test_edit_handler_validates_uuid_format():
    """Test edit handler validates UUID format."""
    from src.handlers.lifecycle.offer_edit_handler import start_edit
    from telegram.ext import ConversationHandler
    
    # Setup: Invalid UUID
    invalid_uuid = "12345"
    update = MockUpdate(command_args=[invalid_uuid])
    context = MockContext(args=[invalid_uuid])
    
    # Execute
    result = await start_edit(update, context)
    
    # Verify: Should end conversation with error
    assert result == ConversationHandler.END
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Invalid offer ID format" in call_args or "invalid" in call_args.lower()


@pytest.mark.asyncio
async def test_pause_handler_error_handling():
    """Test pause handler handles unexpected errors gracefully."""
    from src.handlers.lifecycle.offer_pause_handler import pause_offer
    
    # Setup: Valid UUID but simulate error
    valid_uuid = str(uuid4())
    update = MockUpdate(command_args=[valid_uuid])
    context = MockContext(args=[valid_uuid])
    
    # Mock database to raise exception
    with patch('src.handlers.lifecycle.offer_pause_handler.get_database') as mock_db:
        mock_db.return_value.connect = AsyncMock(side_effect=Exception("DB error"))
        
        # Execute
        await pause_offer(update, context)
        
        # Verify: Should send error message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args[0][0]
        assert "Failed to pause" in call_args or "failed" in call_args.lower()


@pytest.mark.asyncio
async def test_edit_price_input_validation():
    """Test edit handler validates price input format."""
    from src.handlers.lifecycle.offer_edit_handler import update_item_price
    
    # Setup: Invalid price input
    update = MockUpdate()
    update.message.text = "not-a-number"
    context = MockContext()
    context.user_data = {
        "edit_offer_id": uuid4(),
        "edit_item_name": "Sandwich",
    }
    
    # Execute
    from src.handlers.lifecycle.offer_edit_handler import EDIT_PRICE
    result = await update_item_price(update, context)
    
    # Verify: Should stay in EDIT_PRICE state and show error
    assert result == EDIT_PRICE
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Invalid" in call_args or "invalid" in call_args.lower()


@pytest.mark.asyncio
async def test_edit_quantity_input_validation():
    """Test edit handler validates quantity input format."""
    from src.handlers.lifecycle.offer_edit_handler import update_item_quantity
    
    # Setup: Invalid quantity input
    update = MockUpdate()
    update.message.text = "two"
    context = MockContext()
    context.user_data = {
        "edit_offer_id": uuid4(),
        "edit_item_name": "Salad",
    }
    
    # Execute
    from src.handlers.lifecycle.offer_edit_handler import EDIT_QUANTITY
    result = await update_item_quantity(update, context)
    
    # Verify: Should stay in EDIT_QUANTITY state and show error
    assert result == EDIT_QUANTITY
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Invalid" in call_args or "invalid" in call_args.lower()


@pytest.mark.asyncio
async def test_edit_price_rejects_negative():
    """Test edit handler rejects negative prices."""
    from src.handlers.lifecycle.offer_edit_handler import update_item_price
    
    # Setup: Negative price
    update = MockUpdate()
    update.message.text = "-5.00"
    context = MockContext()
    context.user_data = {
        "edit_offer_id": uuid4(),
        "edit_item_name": "Coffee",
    }
    
    # Execute
    from src.handlers.lifecycle.offer_edit_handler import EDIT_PRICE
    result = await update_item_price(update, context)
    
    # Verify: Should stay in EDIT_PRICE state and show error
    assert result == EDIT_PRICE
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "negative" in call_args.lower() or "cannot" in call_args.lower()


@pytest.mark.asyncio
async def test_edit_quantity_rejects_negative():
    """Test edit handler rejects negative quantities."""
    from src.handlers.lifecycle.offer_edit_handler import update_item_quantity
    
    # Setup: Negative quantity
    update = MockUpdate()
    update.message.text = "-10"
    context = MockContext()
    context.user_data = {
        "edit_offer_id": uuid4(),
        "edit_item_name": "Bagel",
    }
    
    # Execute
    from src.handlers.lifecycle.offer_edit_handler import EDIT_QUANTITY
    result = await update_item_quantity(update, context)
    
    # Verify: Should stay in EDIT_QUANTITY state and show error
    assert result == EDIT_QUANTITY
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "negative" in call_args.lower() or "cannot" in call_args.lower()


@pytest.mark.asyncio
async def test_handler_command_registration():
    """Test that lifecycle handlers are properly registered."""
    from src.handlers.lifecycle.offer_pause_handler import get_pause_handler, get_resume_handler
    from src.handlers.lifecycle.offer_edit_handler import get_edit_handler
    from telegram.ext import CommandHandler, ConversationHandler
    
    # Get handlers
    pause_handler = get_pause_handler()
    resume_handler = get_resume_handler()
    edit_handler = get_edit_handler()
    
    # Verify types
    assert isinstance(pause_handler, CommandHandler)
    assert isinstance(resume_handler, CommandHandler)
    assert isinstance(edit_handler, ConversationHandler)
    
    # Verify commands
    assert pause_handler.commands == {"pause"}
    assert resume_handler.commands == {"resume"}
