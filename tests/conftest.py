"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_db():
    """Mock database connection fixture."""
    return Mock()


@pytest.fixture
def mock_redis():
    """Mock Redis connection fixture."""
    return Mock()


@pytest.fixture
def mock_stripe():
    """Mock Stripe client fixture."""
    return Mock()


@pytest.fixture
def mock_telegram_update():
    """Mock Telegram update fixture."""
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.message = Mock()
    update.message.text = "/start"
    return update


@pytest.fixture
def mock_telegram_context():
    """Mock Telegram context fixture."""
    context = Mock()
    context.bot = Mock()
    return context
