"""Unit tests for Stripe checkout service."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.services.stripe_checkout import StripeCheckoutService


@pytest.mark.asyncio
async def test_stripe_create_checkout_session(mock_stripe):
    """Test creating Stripe checkout session."""
    service = StripeCheckoutService(
        secret_key="sk_test_mock",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    purchase_id = uuid4()

    # TODO: Mock stripe.checkout.Session.create
    # checkout_url, expires_at = await service.create_checkout_session(
    #     purchase_id=purchase_id,
    #     offer_title="Test Offer",
    #     total_amount=Decimal("10.00"),
    # )
    # assert checkout_url.startswith("https://")
    # assert expires_at > datetime.utcnow()

    pytest.skip("Stripe mock implementation needed")


@pytest.mark.asyncio
async def test_stripe_verify_payment(mock_stripe):
    """Test verifying payment completion."""
    service = StripeCheckoutService(
        secret_key="sk_test_mock",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    # TODO: Mock stripe.checkout.Session.retrieve
    # result = await service.verify_payment("cs_test_mock")
    # assert "purchase_id" in result
    # assert "payment_status" in result

    pytest.skip("Stripe mock implementation needed")
