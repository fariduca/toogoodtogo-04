"""Integration tests for expiration job.

Tests the background job that marks expired offers.
"""

from datetime import datetime, timedelta

import pytest

from src.services.expiration_job import ExpirationJob


@pytest.mark.asyncio
async def test_expiration_job_marks_expired_offers(mock_db):
    """Test expiration job updates status for expired offers."""
    # TODO: Create offers with end_time in the past
    # TODO: Run expiration job
    # TODO: Verify offers are marked EXPIRED

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_expiration_job_ignores_future_offers(mock_db):
    """Test expiration job doesn't affect offers still active."""
    # TODO: Create offers with end_time in future
    # TODO: Run expiration job
    # TODO: Verify offers remain ACTIVE

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_expiration_job_only_affects_active_offers(mock_db):
    """Test expiration job only processes ACTIVE offers."""
    # TODO: Create expired offers with various statuses (DRAFT, PAUSED, SOLD_OUT)
    # TODO: Run expiration job
    # TODO: Verify only ACTIVE offers are changed to EXPIRED

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_expiration_job_counts():
    """Test expiration job returns correct counts."""
    # Create mock repository
    # TODO: Mock get_expired_offers to return test data
    # TODO: Run expiration job
    # TODO: Verify returned counts match processed offers

    pytest.skip("Repository mocking needed")


@pytest.mark.asyncio
async def test_expiration_job_handles_errors_gracefully(mock_db):
    """Test expiration job continues on individual failures."""
    # TODO: Create offers that will cause update errors
    # TODO: Run expiration job
    # TODO: Verify job completes and returns failure count

    pytest.skip("Database implementation pending")


@pytest.mark.asyncio
async def test_expiration_job_logs_activity():
    """Test expiration job produces structured logs."""
    # TODO: Capture log output
    # TODO: Run expiration job
    # TODO: Verify log entries contain expected fields

    pytest.skip("Log capture mechanism needed")
