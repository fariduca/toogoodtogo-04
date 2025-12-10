"""Offer domain models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class OfferStatus(str, Enum):
    """Offer lifecycle status."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    EXPIRED_EARLY = "EXPIRED_EARLY"
    SOLD_OUT = "SOLD_OUT"


class OfferCategory(str, Enum):
    """Offer category options."""

    MEALS = "MEALS"
    BAKERY = "BAKERY"
    PRODUCE = "PRODUCE"
    OTHER = "OTHER"


class Offer(BaseModel):
    """Offer entity."""

    id: UUID = Field(default_factory=uuid4)
    business_id: UUID
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=200)
    photo_url: Optional[str] = Field(default=None, max_length=500)
    category: Optional[OfferCategory] = None
    price_per_unit: Decimal = Field(gt=0, decimal_places=2, description="Price in currency")
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    quantity_total: int = Field(gt=0, description="Total units available at creation")
    quantity_remaining: int = Field(ge=0, description="Current available units")
    pickup_start_time: datetime = Field(description="When pickup window opens")
    pickup_end_time: datetime = Field(description="When pickup window closes")
    state: OfferStatus = Field(default=OfferStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("pickup_end_time")
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        """Ensure pickup_start_time < pickup_end_time."""
        values = info.data
        if "pickup_start_time" in values and v <= values["pickup_start_time"]:
            raise ValueError("pickup_end_time must be after pickup_start_time")
        return v

    @field_validator("quantity_remaining")
    @classmethod
    def validate_quantity(cls, v: int, info) -> int:
        """Ensure quantity_remaining <= quantity_total."""
        values = info.data
        if "quantity_total" in values and v > values["quantity_total"]:
            raise ValueError("quantity_remaining cannot exceed quantity_total")
        return v

    @property
    def is_expired(self) -> bool:
        """Check if offer has expired based on end_time."""
        return datetime.utcnow() >= self.pickup_end_time

    @property
    def available_for_reservation(self) -> bool:
        """Check if offer is available for reservation."""
        return (
            self.state == OfferStatus.ACTIVE
            and self.quantity_remaining > 0
            and not self.is_expired
        )


class OfferInput(BaseModel):
    """Input model for offer creation."""

    business_id: UUID
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=200)
    photo_url: Optional[str] = None
    category: Optional[OfferCategory] = None
    price_per_unit: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    quantity_total: int = Field(gt=0)
    pickup_start_time: datetime
    pickup_end_time: datetime

    @field_validator("pickup_end_time")
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        """Ensure pickup_start_time < pickup_end_time."""
        values = info.data
        if "pickup_start_time" in values and v <= values["pickup_start_time"]:
            raise ValueError("pickup_end_time must be after pickup_start_time")
        return v
