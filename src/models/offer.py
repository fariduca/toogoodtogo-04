"""Offer domain models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class OfferStatus(str, Enum):
    """Offer lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    SOLD_OUT = "sold_out"


class Item(BaseModel):
    """Item within an offer (value object)."""

    name: str = Field(min_length=2, max_length=80)
    quantity: int = Field(ge=0)
    original_price: Decimal = Field(ge=0)
    discounted_price: Decimal = Field(ge=0)


class Offer(BaseModel):
    """Offer entity."""

    id: UUID = Field(default_factory=uuid4)
    business_id: UUID
    title: str = Field(min_length=5, max_length=120)
    items: list[Item] = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    status: OfferStatus = OfferStatus.DRAFT
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        """Ensure start_time < end_time."""
        values = info.data
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class OfferInput(BaseModel):
    """Input model for offer creation."""

    business_id: UUID
    title: str = Field(min_length=5, max_length=120)
    items: list[Item] = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    status: OfferStatus = OfferStatus.DRAFT
    image_url: Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        """Ensure start_time < end_time."""
        values = info.data
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v
