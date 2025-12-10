"""Purchase domain models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class PurchaseStatus(str, Enum):
    """Purchase transaction status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELED = "canceled"


class PaymentProvider(str, Enum):
    """Payment provider options."""

    STRIPE = "stripe"


class PurchaseItem(BaseModel):
    """Item within a purchase (value object)."""

    name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseInput(BaseModel):
    """Purchase input for creation."""

    offer_id: UUID
    customer_id: int  # Telegram user ID
    item_selections: list[PurchaseItem] = Field(min_length=1)
    total_amount: Decimal = Field(ge=0)
    status: PurchaseStatus = PurchaseStatus.PENDING
    payment_provider: Optional[PaymentProvider] = None
    payment_session_id: Optional[str] = None


class Purchase(BaseModel):
    """Purchase entity."""

    id: UUID = Field(default_factory=uuid4)
    offer_id: UUID
    customer_id: int  # Telegram user ID
    item_selections: list[PurchaseItem] = Field(min_length=1)
    total_amount: Decimal = Field(ge=0)
    payment_provider: Optional[PaymentProvider] = None
    payment_session_id: Optional[str] = None
    status: PurchaseStatus = PurchaseStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("total_amount")
    @classmethod
    def validate_total(cls, v: Decimal, info) -> Decimal:
        """Ensure total matches sum of item selections."""
        values = info.data
        if "item_selections" in values:
            calculated = sum(
                item.quantity * item.unit_price for item in values["item_selections"]
            )
            if v != calculated:
                raise ValueError(
                    f"total_amount {v} does not match calculated total {calculated}"
                )
        return v


class Customer(BaseModel):
    """Customer entity."""

    id: UUID = Field(default_factory=uuid4)
    telegram_handle: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseRequest(BaseModel):
    """Purchase initiation request."""

    items: list[dict[str, int | str]] = Field(
        min_length=1, description="List of {item_name, quantity}"
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[dict]) -> list[dict]:
        """Ensure each item has required fields."""
        for item in v:
            if "item_name" not in item or "quantity" not in item:
                raise ValueError("Each item must have item_name and quantity")
            if not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                raise ValueError("quantity must be a positive integer")
        return v
