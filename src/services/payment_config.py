"""Payment configuration for Stripe."""

import json
from typing import Any


class PaymentConfig:
    """Stripe payment configuration."""

    def __init__(self, secret_key: str, price_mapping_json: str = "{}"):
        """Initialize payment config."""
        self.secret_key = secret_key
        self.price_mapping: dict[str, Any] = json.loads(price_mapping_json)

    def get_price_id(self, product_key: str) -> str | None:
        """Get Stripe price ID for product key."""
        return self.price_mapping.get(product_key)

    def add_price_mapping(self, product_key: str, price_id: str) -> None:
        """Add price mapping."""
        self.price_mapping[product_key] = price_id
