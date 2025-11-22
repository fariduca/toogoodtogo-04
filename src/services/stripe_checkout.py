"""Stripe checkout session service."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import stripe


class StripeCheckoutService:
    """Service for creating Stripe checkout sessions."""

    def __init__(self, secret_key: str, success_url: str, cancel_url: str):
        """Initialize Stripe service."""
        stripe.api_key = secret_key
        self.success_url = success_url
        self.cancel_url = cancel_url

    async def create_checkout_session(
        self,
        purchase_id: UUID,
        offer_title: str,
        total_amount: Decimal,
        currency: str = "usd",
    ) -> tuple[str, datetime]:
        """Create Stripe checkout session and return URL + expiration."""
        # Convert amount to cents
        amount_cents = int(total_amount * 100)

        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": offer_title,
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{self.success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=self.cancel_url,
            metadata={
                "purchase_id": str(purchase_id),
            },
        )

        # Checkout sessions expire after 24 hours
        expires_at = datetime.utcnow() + timedelta(hours=24)

        return session.url, expires_at  # type: ignore

    async def verify_payment(self, session_id: str) -> dict[str, Any]:
        """Verify payment completion and retrieve session details."""
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "purchase_id": session.metadata.get("purchase_id"),
            "payment_status": session.payment_status,
            "payment_intent": session.payment_intent,
        }
