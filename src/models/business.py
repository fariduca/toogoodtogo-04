"""Business and Venue domain models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class VerificationStatus(str, Enum):
    """Business verification status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Venue(BaseModel):
    """Venue location details."""

    address: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class BusinessInput(BaseModel):
    """Input model for business registration."""

    name: str = Field(min_length=2, max_length=100)
    telegram_id: int
    verification_status: VerificationStatus = VerificationStatus.PENDING
    venue: Venue
    photo_url: Optional[str] = None


class Business(BaseModel):
    """Business entity."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=2, max_length=100)
    telegram_id: int
    verification_status: VerificationStatus = VerificationStatus.PENDING
    venue: Optional[Venue] = None
    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
