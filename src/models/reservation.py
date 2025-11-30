"""Reservation domain model."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReservationStatus(str, Enum):
    """Reservation status enumeration."""

    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Reservation(BaseModel):
    """Reservation entity for on-site payment pickups."""

    id: UUID = Field(default_factory=uuid4)
    order_id: str = Field(min_length=12, max_length=12, description="Customer-facing order ID (e.g., RES-A3F2B8C1)")
    offer_id: UUID = Field(description="Reserved offer")
    customer_id: int = Field(gt=0, description="Customer's telegram user ID")
    quantity: int = Field(gt=0, description="Number of units reserved")
    unit_price: Decimal = Field(ge=0, description="Price per unit at reservation time")
    total_price: Decimal = Field(ge=0, description="Total amount to pay on-site")
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    status: ReservationStatus = Field(default=ReservationStatus.CONFIRMED)
    pickup_start_time: datetime = Field(description="Pickup window start")
    pickup_end_time: datetime = Field(description="Pickup window end")
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_cancellable(self) -> bool:
        """Check if reservation can still be cancelled."""
        return self.status == ReservationStatus.CONFIRMED and datetime.utcnow() < self.pickup_end_time


class ReservationInput(BaseModel):
    """Input model for reservation creation."""

    offer_id: UUID
    customer_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    total_price: Decimal = Field(ge=0)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    pickup_start_time: datetime
    pickup_end_time: datetime
