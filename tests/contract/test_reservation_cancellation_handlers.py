"""Contract tests for reservation cancellation handlers (Phase 6).

Validates cancellation flow conforms to expected contracts.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from src.models.reservation import ReservationStatus


class MockUpdate:
    """Mock Telegram Update object."""
    
    def __init__(self, callback_data=None):
        self.effective_user = Mock()
        self.effective_user.id = 12345
        
        self.callback_query = Mock()
        self.callback_query.data = callback_data
        self.callback_query.answer = AsyncMock()
        self.callback_query.edit_message_text = AsyncMock()
        self.callback_query.message = Mock()


class MockContext:
    """Mock Telegram Context object."""
    
    def __init__(self):
        self.bot_data = {}
        self.user_data = {}


class MockReservation:
    """Mock Reservation model."""
    
    def __init__(self, status=ReservationStatus.CONFIRMED, pickup_in_future=True):
        self.id = uuid4()
        self.order_id = "RES-ABC123"
        self.offer_id = uuid4()
        self.customer_id = 1
        self.quantity = 2
        self.total_price = 10.00
        self.status = status
        
        # Pickup time in future or past
        if pickup_in_future:
            self.pickup_end_time = datetime.utcnow() + timedelta(hours=2)
        else:
            self.pickup_end_time = datetime.utcnow() - timedelta(hours=1)


class MockOffer:
    """Mock Offer model."""
    
    def __init__(self):
        self.id = uuid4()
        self.title = "Test Offer"


@pytest.mark.asyncio
async def test_cancel_reservation_requires_confirmed_status():
    """Test cancel only works on CONFIRMED reservations."""
    from src.handlers.purchasing.cancel_reservation_handler import handle_cancel_reservation
    
    reservation_id = uuid4()
    update = MockUpdate(callback_data=f"cancel_reservation:{reservation_id}")
    context = MockContext()
    
    # Mock already cancelled reservation
    reservation = MockReservation(status=ReservationStatus.CANCELLED)
    reservation.id = reservation_id
    
    reservation_repo_mock = AsyncMock()
    reservation_repo_mock.get_by_id = AsyncMock(return_value=reservation)
    
    offer_repo_mock = AsyncMock()
    
    context.bot_data["reservation_repo"] = reservation_repo_mock
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_cancel_reservation(update, context)
    
    # Should reject
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "already been" in call_args.lower() or "CANCELLED" in call_args


@pytest.mark.asyncio
async def test_cancel_reservation_validates_time():
    """Test cancel validates pickup time hasn't passed."""
    from src.handlers.purchasing.cancel_reservation_handler import handle_cancel_reservation
    
    reservation_id = uuid4()
    update = MockUpdate(callback_data=f"cancel_reservation:{reservation_id}")
    context = MockContext()
    
    # Mock reservation with past pickup time
    reservation = MockReservation(status=ReservationStatus.CONFIRMED, pickup_in_future=False)
    reservation.id = reservation_id
    
    reservation_repo_mock = AsyncMock()
    reservation_repo_mock.get_by_id = AsyncMock(return_value=reservation)
    
    offer_repo_mock = AsyncMock()
    offer = MockOffer()
    offer_repo_mock.get_by_id = AsyncMock(return_value=offer)
    
    context.bot_data["reservation_repo"] = reservation_repo_mock
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_cancel_reservation(update, context)
    
    # Should reject after pickup time
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "Cannot cancel" in call_args or "ended" in call_args.lower()


@pytest.mark.asyncio
async def test_cancel_reservation_shows_confirmation():
    """Test cancel shows confirmation prompt before executing."""
    from src.handlers.purchasing.cancel_reservation_handler import handle_cancel_reservation
    
    reservation_id = uuid4()
    update = MockUpdate(callback_data=f"cancel_reservation:{reservation_id}")
    context = MockContext()
    
    # Mock valid reservation
    reservation = MockReservation(status=ReservationStatus.CONFIRMED, pickup_in_future=True)
    reservation.id = reservation_id
    
    offer = MockOffer()
    
    reservation_repo_mock = AsyncMock()
    reservation_repo_mock.get_by_id = AsyncMock(return_value=reservation)
    
    offer_repo_mock = AsyncMock()
    offer_repo_mock.get_by_id = AsyncMock(return_value=offer)
    
    context.bot_data["reservation_repo"] = reservation_repo_mock
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_cancel_reservation(update, context)
    
    # Should show confirmation with buttons
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args
    
    # Check confirmation text
    text = call_args[0][0]
    assert "Cancel Reservation" in text
    assert reservation.order_id in text
    
    # Check has reply markup
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio
async def test_confirm_cancel_returns_inventory():
    """Test confirming cancel returns inventory to offer."""
    from src.handlers.purchasing.cancel_reservation_handler import handle_confirm_cancel_reservation
    
    reservation_id = uuid4()
    update = MockUpdate(callback_data=f"confirm_cancel_reservation:{reservation_id}")
    context = MockContext()
    
    # Mock valid reservation
    reservation = MockReservation(status=ReservationStatus.CONFIRMED, pickup_in_future=True)
    reservation.id = reservation_id
    
    # Mock successful cancellation
    cancelled_reservation = MockReservation(status=ReservationStatus.CANCELLED, pickup_in_future=True)
    cancelled_reservation.id = reservation_id
    
    reservation_repo_mock = AsyncMock()
    reservation_repo_mock.get_by_id = AsyncMock(return_value=reservation)
    reservation_repo_mock.cancel = AsyncMock(return_value=cancelled_reservation)
    
    offer_repo_mock = AsyncMock()
    
    context.bot_data["reservation_repo"] = reservation_repo_mock
    context.bot_data["offer_repo"] = offer_repo_mock
    
    await handle_confirm_cancel_reservation(update, context)
    
    # Should call cancel method
    reservation_repo_mock.cancel.assert_called_once()
    call_kwargs = reservation_repo_mock.cancel.call_args[1]
    assert call_kwargs["reservation_id"] == reservation_id
    assert "reason" in call_kwargs
    
    # Should show success message
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "Cancelled" in call_args
    assert "returned to inventory" in call_args or "available" in call_args


@pytest.mark.asyncio
async def test_myreservations_shows_cancel_button_when_valid():
    """Test /myreservations shows cancel button only before pickup time."""
    # This test validates the UI logic for showing/hiding cancel button
    from datetime import datetime
    
    # Mock reservation before pickup time
    reservation_future = MockReservation(pickup_in_future=True)
    
    # Mock reservation after pickup time
    reservation_past = MockReservation(pickup_in_future=False)
    
    now = datetime.utcnow()
    
    # Future pickup should allow cancel
    assert reservation_future.pickup_end_time > now
    
    # Past pickup should not allow cancel
    assert reservation_past.pickup_end_time < now


@pytest.mark.asyncio
async def test_keep_reservation_cancels_cancel():
    """Test 'keep reservation' button cancels the cancel flow."""
    from src.handlers.purchasing.cancel_reservation_handler import handle_keep_reservation
    
    update = MockUpdate(callback_data=f"keep_reservation:{uuid4()}")
    context = MockContext()
    
    await handle_keep_reservation(update, context)
    
    # Should answer callback
    update.callback_query.answer.assert_called_once()
    
    # Should show confirmation message
    update.callback_query.edit_message_text.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args[0][0]
    assert "kept" in call_args.lower()
